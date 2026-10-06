"""Temporal Fusion Transformer (tabular adaptation) for SMERGE downscaling.

Each MPI rank loads the data, takes a strided shard of the train and test
CSVs, trains its own model on that shard, then writes its predictions and a
SHAP importance table. Ranks do not synchronise gradients.

Usage (under srun):
    python -u PyT_TFT_MPIv1_noFE.py <state> <parting>

    state    region key used in file names (e.g. OK, BigArea)
    parting  accepted for compatibility with the other scripts; not used here

"noFE" variant: raw integer Month and Year, no land-cover feature.

Environment variables:
    SMERGE_DATA_DIR  directory holding {state}_trainV6-LC.csv / {state}_testV6-LC.csv
    SMERGE_OUT_DIR   directory for predictions and SHAP tables
"""

import os
import random
import sys
import copy
import subprocess

os.environ['PYTHONUNBUFFERED'] = '1'
print('Script starting')

# =============================================================================
# MPI SETUP - Multi-node data parallelism
# =============================================================================

from mpi4py import MPI

comm = MPI.COMM_WORLD
size = comm.Get_size()
rank = comm.Get_rank()

print(f'MPI initialized: Rank {rank}/{size}')

import torch
import torch.nn as nn
import torch.nn.functional as F
from tqdm import tqdm
from torch.utils.data import TensorDataset, DataLoader
import pandas as pd
import numpy as np
import shap
import matplotlib
matplotlib.use('Agg')

state   = str(sys.argv[1])
parting = str(sys.argv[2])

print('Script imports done')

from datetime import datetime
from scipy.stats import spearmanr

# =============================================================================
# HYPERPARAMETERS
# =============================================================================

HIDDEN       = 256    # d_model: embedding width for all feature groups
N_HEADS      = 4      # attention heads in multi-head self-attention
N_LAYERS     = 2      # number of stacked TFT encoder layers
DROPOUT      = 0.1
MAX_LR       = 3e-4
WEIGHT_DECAY = 0
HUBER_BETA   = 0.2

# =============================================================================
# GPU ASSIGNMENT
# =============================================================================

def get_num_gpus():
    """
    Detect number of GPUs visible to this rank.

    torch.cuda.device_count() respects CUDA_VISIBLE_DEVICES set by SLURM
    when --gpus-per-task=1 is used. nvidia-smi -L is a fallback only and
    ignores CUDA_VISIBLE_DEVICES, so it would return the full DGX node count.
    """
    n = torch.cuda.device_count()
    if n > 0:
        print(f'[Rank {rank}] torch sees {n} GPU(s)')
        return n
    try:
        output = subprocess.check_output(['nvidia-smi', '-L'],
                                         stderr=subprocess.DEVNULL)
        n = len(output.decode().strip().split('\n'))
        print(f'[Rank {rank}] nvidia-smi sees {n} GPU(s)')
        return n
    except Exception:
        print(f'[Rank {rank}] GPU detection failed, defaulting to 1')
        return 1


_num_gpus  = get_num_gpus()
local_rank = rank % _num_gpus
torch.cuda.set_device(local_rank)
device     = torch.device(f'cuda:{local_rank}')

print(f'Rank {rank}: Using device {device} '
      f'(local_rank={local_rank}, gpus_visible={_num_gpus})')
print(f'Rank {rank}: GPU name: {torch.cuda.get_device_name(device)}')

# =============================================================================
# REPRODUCIBILITY
# =============================================================================

# Seed differs per rank so ranks do not draw identical validation splits.
SEED = 1337 + rank
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)
torch.cuda.manual_seed(SEED)
torch.cuda.manual_seed_all(SEED)

torch.backends.cuda.matmul.allow_tf32 = True
torch.backends.cudnn.allow_tf32 = True
g = torch.Generator()   # drives DataLoader shuffling
g.manual_seed(SEED)

# =============================================================================
# TRAINING CONFIG
# =============================================================================

NUM_EPOCHS    = 60
WARMUP_EPOCHS = 12     # linear warm-up, then cosine decay
BATCH_SIZE    = 4096
PATIENCE      = 12     # epochs without validation improvement before stopping
VAL_FRAC      = 0.10   # fraction of the train shard held out for validation

# =============================================================================
# FEATURE GROUP INDICES
# var2 = ['Clay','Sand','Silt','Elevation','Aspect','Slope',   <- static  [0-5]
#          'LAI','MODIS','ALB','Temp',                          <- dynamic [6-9]
#          'Month','Year']                                      <- temporal[10-11]
# No land cover: LandC dropped from the dynamic group entirely.
# =============================================================================

STATIC_IDX   = [0, 1, 2, 3, 4, 5]
DYNAMIC_IDX  = [6, 7, 8, 9]
TEMPORAL_IDX = [10, 11]

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def rank_corr_ave(data, verifier, subject):
    """Spearman correlation on spatially-averaged monthly anomalies."""
    data = data.dropna().copy()

    month_ave = (data[[verifier, subject, 'Year', 'Month', 'PageName']]
                 .groupby(['Year', 'Month', 'PageName']).mean()
                 .reset_index())

    hist_month_ave = (month_ave[[verifier, subject, 'Month', 'PageName']]
                      .groupby(['Month', 'PageName']).mean()
                      .reset_index()
                      .rename(columns={verifier: verifier + '_M',
                                       subject:  subject  + '_M'}))

    data_t = data.merge(hist_month_ave, on=['PageName', 'Month'])
    data_t[verifier + '_A'] = data_t[verifier] - data_t[verifier + '_M']
    data_t[subject  + '_A'] = data_t[subject]  - data_t[subject  + '_M']

    d = (data_t.groupby(['Month', 'Year'])
               .agg(verifier_A=(verifier + '_A', 'mean'),
                    subject_A =(subject  + '_A', 'mean'))
               .reset_index())

    spearman_corr, spearman_p = spearmanr(d['verifier_A'], d['subject_A'])
    return spearman_corr, spearman_p


def compute_shap_values(model, X_tr, X_ts, device):
    """Return SHAP values from GradientExplainer for a trained PyTorch model.

    Uses the first 500 rows of the train shard as the background and the first
    500 rows of the test shard as the samples to explain.
    """
    model.eval()
    background  = torch.tensor(X_tr[:500], dtype=torch.float32, device=device)
    test_tensor = torch.tensor(X_ts[:500], dtype=torch.float32, device=device)
    explainer   = shap.GradientExplainer(model, background)
    vals        = explainer.shap_values(test_tensor)
    if isinstance(vals, list):
        vals = vals[0]
    return np.asarray(vals)


def make_loaders(X_tr, y_tr):
    """Split the train shard into shuffled train and ordered validation loaders.

    The split is a seeded random permutation, so each rank gets a different but
    reproducible validation set. drop_last is used on the training loader only,
    to avoid a tiny final batch with unstable BatchNorm statistics.
    """
    n     = len(X_tr)
    idx   = np.random.RandomState(SEED).permutation(n)
    n_val = max(1, int(n * VAL_FRAC))
    tr_idx, val_idx = idx[n_val:], idx[:n_val]

    def _loader(X, y, shuffle):
        return DataLoader(
            TensorDataset(torch.tensor(X, dtype=torch.float32),
                          torch.tensor(y, dtype=torch.float32)),
            batch_size=BATCH_SIZE,
            shuffle=shuffle,
            generator=g if shuffle else None,
            num_workers=0,
            pin_memory=True,
            drop_last=shuffle,
        )

    return (_loader(X_tr[tr_idx],  y_tr[tr_idx],  shuffle=True),
            _loader(X_tr[val_idx], y_tr[val_idx],  shuffle=False))


# =============================================================================
# MODEL DEFINITION - Temporal Fusion Transformer (TFT)
#
# Adapted from Lim et al. (2021) for single-step tabular regression.
# The original TFT targets multi-horizon time-series forecasting; here it is
# adapted to process flat feature vectors grouped into static / dynamic /
# temporal streams rather than sequences.
#
# Architecture:
#   1. Variable Selection Networks (VSN) — one per group
#      Each VSN learns a soft weight over its group's features, projects each
#      feature to d_model, then returns a weighted sum + the weight vector
#      for interpretability.
#   2. Static context vectors from the static VSN gate the dynamic and
#      temporal VSNs via GRN context inputs.
#   3. Gated Residual Networks (GRN) — core nonlinear building block used
#      throughout (VSN, enrichment, output layers). Two linear layers with
#      ELU activation, gated by a sigmoid, with a skip connection.
#   4. Static Enrichment — a GRN that uses static context to modulate the
#      concatenated dynamic+temporal representation.
#   5. Multi-head Self-Attention — applied across the three group tokens
#      (static, dynamic, temporal) after enrichment, so the model can learn
#      cross-group dependencies.
#   6. Position-wise feed-forward + residual gating → output head.
#
# Key hyperparameters:
#   HIDDEN (d_model): embedding dimension for all feature projections
#   N_HEADS:          attention heads
#   N_LAYERS:         stacked self-attention layers after enrichment
# =============================================================================

class GRN(nn.Module):
    """
    Gated Residual Network — core TFT building block.

    out = LayerNorm(x_skip + gate * (W2 * ELU(W1 * x + b1) + b2))

    Optional context vector c is added before the ELU activation,
    allowing external conditioning (e.g. static features gating dynamic).
    """
    def __init__(self, in_dim: int, hidden: int, out_dim: int,
                 dropout: float = 0.1, context_dim: int = 0):
        super().__init__()
        self.skip_proj = nn.Linear(in_dim, out_dim) if in_dim != out_dim else nn.Identity()
        self.fc1       = nn.Linear(in_dim + context_dim, hidden)
        self.fc2       = nn.Linear(hidden, out_dim)
        self.gate_fc   = nn.Linear(in_dim + context_dim, out_dim)
        self.norm      = nn.LayerNorm(out_dim)
        self.drop      = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor,
                c: torch.Tensor = None) -> torch.Tensor:
        if c is not None:
            x_in = torch.cat([x, c], dim=-1)
        else:
            x_in = x
        h    = F.elu(self.fc1(x_in))
        h    = self.drop(self.fc2(h))
        gate = torch.sigmoid(self.gate_fc(x_in))
        return self.norm(self.skip_proj(x) + gate * h)


class VariableSelectionNetwork(nn.Module):
    """
    VSN: projects each feature in a group to d_model independently, then
    learns a softmax weight over the group to produce a single d_model vector.

    Returns (selected_embedding, weights) where weights are [B, n_features]
    and can be logged for interpretability.
    """
    def __init__(self, n_features: int, d_model: int,
                 dropout: float = 0.1, context_dim: int = 0):
        super().__init__()
        # Per-feature linear projection to d_model
        self.feature_projs = nn.ModuleList([
            nn.Linear(1, d_model) for _ in range(n_features)
        ])
        # Soft weight over features (optionally conditioned on context)
        self.grn_weights = GRN(
            in_dim      = n_features * d_model,
            hidden      = d_model,
            out_dim     = n_features,
            dropout     = dropout,
            context_dim = context_dim,
        )
        # Per-feature GRN to refine the projection
        self.grns = nn.ModuleList([
            GRN(d_model, d_model, d_model, dropout) for _ in range(n_features)
        ])

    def forward(self, x: torch.Tensor,
                context: torch.Tensor = None):
        """
        x: [B, n_features]
        context: [B, context_dim] or None
        returns: embedding [B, d_model], weights [B, n_features]
        """
        # Project each feature independently
        projections = [
            self.grns[i](self.feature_projs[i](x[:, i:i+1]))
            for i in range(x.shape[1])
        ]
        # Concatenate all projections for weight computation
        flat = torch.cat(projections, dim=-1)     # [B, n_features * d_model]
        weights = torch.softmax(
            self.grn_weights(flat, context), dim=-1
        )                                          # [B, n_features]

        # Weighted sum of per-feature projections
        stacked = torch.stack(projections, dim=1)  # [B, n_features, d_model]
        selected = (stacked * weights.unsqueeze(-1)).sum(dim=1)  # [B, d_model]
        return selected, weights


class TFT(nn.Module):
    """Group-token TFT regressor.

    The 12 features are split into static / dynamic / temporal groups (indices
    bound with set_group_indices after construction). Each group is embedded by a
    variable selection network; the static embedding becomes a context vector for
    the other two. The three group tokens go through a Transformer encoder and a
    linear head. output_grn and static_context_grn outputs beyond the context are
    unused, but kept so seeded initialisation matches earlier runs.
    """
    def __init__(self,
                 static_dim:   int,
                 dynamic_dim:  int,
                 temporal_dim: int,
                 d_model:      int   = 128,
                 n_heads:      int   = 4,
                 n_layers:     int   = 2,
                 dropout:      float = 0.1):
        super().__init__()

        self.d_model = d_model

        # ── Variable Selection Networks ───────────────────────────────────────
        # Static VSN has no context input; its output becomes context for others
        self.static_vsn   = VariableSelectionNetwork(
            static_dim, d_model, dropout, context_dim=0)
        self.dynamic_vsn  = VariableSelectionNetwork(
            dynamic_dim, d_model, dropout, context_dim=d_model)
        self.temporal_vsn = VariableSelectionNetwork(
            temporal_dim, d_model, dropout, context_dim=d_model)

        # ── Static context encoders ───────────────────────────────────────────
        # Four static context vectors following the TFT paper:
        # c_s: enrichment context, c_e: encoder context (not used in flat mode),
        # c_h, c_c: initialise hidden states (unused here, kept for completeness)
        self.static_context_grn = GRN(d_model, d_model, d_model, dropout)

        # ── Static enrichment ─────────────────────────────────────────────────
        # GRN that uses static context to modulate the combined representation
        self.static_enrichment = GRN(
            d_model, d_model, d_model, dropout, context_dim=d_model)

        # ── Self-Attention across group tokens ────────────────────────────────
        # We treat the 3 group embeddings (static, dynamic, temporal) as a
        # sequence of length 3 and apply multi-head attention across them.
        encoder_layer = nn.TransformerEncoderLayer(
            d_model         = d_model,
            nhead           = n_heads,
            dim_feedforward = d_model * 4,
            dropout         = dropout,
            activation      = 'relu',
            batch_first     = True,
            norm_first      = True,   # pre-LN for training stability
        )
        self.transformer = nn.TransformerEncoder(encoder_layer,
                                                  num_layers=n_layers)

        # ── Output gate + head ────────────────────────────────────────────────
        # Gated residual after attention, then project to scalar
        self.output_grn = GRN(d_model, d_model, d_model, dropout)
        self.head       = nn.Linear(d_model * 3, 1)  # concat of 3 group tokens
        self.drop       = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor):
        """
        x: [B, total_features] — split internally by group index.
        Returns: [B, 1] prediction.
        """
        # ── Split by group ────────────────────────────────────────────────────
        # Index slices are defined by the module-level constants passed at init
        x_static   = x[:, self._static_idx]    # [B, n_s]
        x_dynamic  = x[:, self._dynamic_idx]   # [B, n_d]
        x_temporal = x[:, self._temporal_idx]  # [B, n_t]

        # ── Variable selection ────────────────────────────────────────────────
        s_emb, s_weights = self.static_vsn(x_static)                # [B, d]
        context          = self.static_context_grn(s_emb)           # [B, d]
        d_emb, d_weights = self.dynamic_vsn(x_dynamic, context)     # [B, d]
        t_emb, t_weights = self.temporal_vsn(x_temporal, context)   # [B, d]

        # ── Static enrichment on dynamic + temporal ───────────────────────────
        d_enrich = self.static_enrichment(d_emb, context)
        t_enrich = self.static_enrichment(t_emb, context)

        # ── Self-Attention across 3 group tokens ──────────────────────────────
        # Sequence: [static_token, dynamic_token, temporal_token]
        tokens  = torch.stack([s_emb, d_enrich, t_enrich], dim=1)  # [B, 3, d]
        encoded = self.transformer(tokens)                           # [B, 3, d]

        # ── Gated output ──────────────────────────────────────────────────────
        out = self.drop(encoded)
        out = out.reshape(out.shape[0], -1)   # [B, 3 * d_model]
        return self.head(out)                  # [B, 1]

    def set_group_indices(self, static_idx, dynamic_idx, temporal_idx):
        """Called after construction to bind feature group indices."""
        self._static_idx   = static_idx
        self._dynamic_idx  = dynamic_idx
        self._temporal_idx = temporal_idx


# =============================================================================
# TRAINING FUNCTION
# =============================================================================

def ML_PyTorch(X_ts, X_tr, y_tr):
    """Full training run with TFT."""
    train_loader, val_loader = make_loaders(X_tr, y_tr)

    print(f'Rank {rank}: Training started at {datetime.now()}')
    print(f'Rank {rank}: d_model={HIDDEN}, n_heads={N_HEADS}, '
          f'n_layers={N_LAYERS}, dropout={DROPOUT:.3f}')
    print(f'Rank {rank}: lr={MAX_LR:.2e}, weight_decay={WEIGHT_DECAY}')
    print(f'Rank {rank}: train={int(len(X_tr) * (1 - VAL_FRAC))}, '
          f'val={int(len(X_tr) * VAL_FRAC)}')
    print(f'Rank {rank}: static={len(STATIC_IDX)}f  '
          f'dynamic={len(DYNAMIC_IDX)}f  '
          f'temporal={len(TEMPORAL_IDX)}f')

    model = TFT(
        static_dim   = len(STATIC_IDX),
        dynamic_dim  = len(DYNAMIC_IDX),
        temporal_dim = len(TEMPORAL_IDX),
        d_model      = HIDDEN,
        n_heads      = N_HEADS,
        n_layers     = N_LAYERS,
        dropout      = DROPOUT,
    ).to(device)
    model.set_group_indices(STATIC_IDX, DYNAMIC_IDX, TEMPORAL_IDX)

    optimizer = torch.optim.AdamW(model.parameters(),
                                  lr=MAX_LR,
                                  weight_decay=WEIGHT_DECAY,
                                  betas=(0.9, 0.99), eps=1e-7)

    warmup = torch.optim.lr_scheduler.LinearLR(
        optimizer, start_factor=0.1, end_factor=1.0,
        total_iters=WARMUP_EPOCHS)
    cosine = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=max(1, NUM_EPOCHS - WARMUP_EPOCHS), eta_min=1e-6)
    scheduler = torch.optim.lr_scheduler.SequentialLR(
        optimizer, schedulers=[warmup, cosine], milestones=[WARMUP_EPOCHS])

    criterion = nn.SmoothL1Loss(beta=HUBER_BETA)

    best_val          = float('inf')
    best_state        = None
    epochs_no_improve = 0

    for epoch in tqdm(range(NUM_EPOCHS), desc=f'Rank {rank} Training'):
        # ── train ─────────────────────────────────────────────────────────────
        model.train()
        epoch_loss, n_batches = 0.0, 0
        for Xb, yb in train_loader:
            Xb, yb = Xb.to(device), yb.to(device)
            optimizer.zero_grad()
            with torch.amp.autocast(device_type='cuda', dtype=torch.bfloat16):
                pred = model(Xb)
                loss = criterion(pred.squeeze(), yb.squeeze())
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            epoch_loss += loss.item()
            n_batches  += 1
        scheduler.step()

        # ── validate ──────────────────────────────────────────────────────────
        model.eval()
        val_loss, n_vb = 0.0, 0
        with torch.no_grad():
            for Xb, yb in val_loader:
                Xb, yb = Xb.to(device), yb.to(device)
                with torch.amp.autocast(device_type='cuda', dtype=torch.bfloat16):
                    val_loss += criterion(model(Xb).squeeze(),
                                          yb.squeeze()).item()
                n_vb += 1
        val_loss /= max(1, n_vb)

        # Keep a copy of the best weights seen so far
        if val_loss < best_val - 1e-7:
            best_val          = val_loss
            best_state        = copy.deepcopy(model.state_dict())
            epochs_no_improve = 0
        else:
            epochs_no_improve += 1

        if epoch % 5 == 0 or epoch == NUM_EPOCHS - 1:
            print(f'Rank {rank}, Epoch {epoch:3d}, '
                  f'train={epoch_loss / max(1, n_batches):.6f}, '
                  f'val={val_loss:.6f}, '
                  f'lr={optimizer.param_groups[0]["lr"]:.2e}, '
                  f'patience={epochs_no_improve}/{PATIENCE}')

        if epochs_no_improve >= PATIENCE:
            print(f'Rank {rank}: Early stop at epoch {epoch} '
                  f'(best val={best_val:.6f})')
            break

    if best_state is not None:
        model.load_state_dict(best_state)
        print(f'Rank {rank}: Restored best weights (val={best_val:.6f})')

    print(f'Rank {rank}: Training complete at {datetime.now()}')

    # ── Batched inference ─────────────────────────────────────────────────────
    # Batches bound GPU memory on large test shards.
    model.eval()
    predictions = []
    with torch.no_grad():
        torch.cuda.empty_cache()
        for i in range(0, len(X_ts), BATCH_SIZE):
            Xb     = torch.tensor(X_ts[i:i + BATCH_SIZE],
                                  dtype=torch.float32).to(device)
            pred_b = model(Xb).cpu().numpy()
            predictions.append(pred_b)
            del Xb
            torch.cuda.empty_cache()

    pred = np.concatenate(predictions, axis=0).ravel()
    return pred, model


# =============================================================================
# MAIN EXECUTION
# =============================================================================

home    = os.environ.get('SMERGE_DATA_DIR', '/path/to/data')
out_dir = os.environ.get('SMERGE_OUT_DIR',  '/path/to/results')
resolution = f'{out_dir}/TFT_{state}_500v1noFE-{rank}'   # output file stem
train_file = f'{home}/{state}_trainV6-LC.csv'
test_file  = f'{home}/{state}_testV6-LC.csv'

if rank == 0:
    print(f'\nMPI Multi-Node TFT Configuration:')
    print(f'  Total ranks  : {size}')
    print(f'  GPUs visible : {_num_gpus}')
    print(f'  State        : {state}')
    print(f'  d_model      : {HIDDEN}')
    print(f'  n_heads      : {N_HEADS}')
    print(f'  n_layers     : {N_LAYERS}')
    print(f'  dropout      : {DROPOUT:.3f}')
    print(f'  lr           : {MAX_LR:.2e}')
    print(f'  weight_decay : {WEIGHT_DECAY}')
    print(f'  huber_beta   : {HUBER_BETA:.3f}')
    print(f'  Batch size   : {BATCH_SIZE}')
    print(f'  Loading from : {train_file}')

# ── Column sets ───────────────────────────────────────────────────────────────

# all_vars: columns read from the CSV. AHRR is not a model input; it is kept for
# the sanity metric and downstream validation.
all_vars = ['PageName', 'Clay', 'Sand', 'Silt', 'Elevation', 'Slope',
            'Aspect', 'MODIS', 'SMERGE', 'Date', 'LAI', 'ALB', 'Temp',
            'AHRR', 'Month', 'Year']

# noFE: raw integer Month and Year. No land cover: LandC dropped.
# var2 = ['Clay','Sand','Silt','Elevation','Aspect','Slope',   <- [0-5]  static
#          'LAI','MODIS','ALB','Temp',                          <- [6-9]  dynamic
#          'Month','Year']                                      <- [10-11] temporal
var2 = ['Clay', 'Sand', 'Silt', 'Elevation', 'Aspect', 'Slope',
        'LAI', 'MODIS', 'ALB', 'Temp',
        'Month', 'Year']

# ── Load + clean ──────────────────────────────────────────────────────────────

def load_and_clean(path):
    """Read a CSV and keep complete rows whose Sand+Silt+Clay sum to ~1."""
    df = pd.read_csv(path, usecols=all_vars, engine='pyarrow').dropna()
    df['Soil'] = df['Sand'] + df['Silt'] + df['Clay']
    df = df[(df['Soil'] >= 0.9999) & (df['Soil'] < 1.0001)].reset_index()
    for col in ['index', 'level_0']:
        if col in df.columns:
            df.drop(columns=[col], inplace=True)
    return df.dropna()


train_df = load_and_clean(train_file)
test_df  = load_and_clean(test_file)

print(f'Rank {rank}: Data loaded — Train={len(train_df)}, Test={len(test_df)}')

# ── Strided per-rank split ────────────────────────────────────────────────────
# Every size-th row goes to this rank. Avoids an MPI scatter, which is capped
# at about 1 GB per message in OpenMPI.

data_chunk_train = train_df.iloc[rank::size].reset_index(drop=True)
data_chunk_test  = test_df.iloc[rank::size].reset_index(drop=True)

print(f'Rank {rank}: Chunk {rank}/{size} — '
      f'Train={len(data_chunk_train)}, Test={len(data_chunk_test)}')

X_train = data_chunk_train[var2].astype(np.float32).values
y_train = data_chunk_train[['SMERGE']].astype(np.float32).values
X_test  = data_chunk_test[var2].astype(np.float32).values

print(f'Rank {rank}: X_train shape={X_train.shape}')

# =============================================================================
# TRAIN + PREDICT
# =============================================================================

ml_out, trained_model = ML_PyTorch(X_test, X_train, y_train)

# ── Evaluate ──────────────────────────────────────────────────────────────────

data_chunk_test['ML_'] = ml_out
corr, p_value = rank_corr_ave(data_chunk_test, 'AHRR', 'ML_')
print(f'Rank {rank}: Spearman corr={corr:.4f}, p={p_value:.4e}')

# ── Save predictions ──────────────────────────────────────────────────────────

output_path = f'{resolution}_{int(rank)}.csv'
try:
    import dask.dataframe as dd
    ddf = dd.from_pandas(data_chunk_test, npartitions=12)
    ddf.to_csv(output_path, single_file=True, index=False)
    print(f'Rank {rank}: Results saved via Dask -> {output_path}')
except Exception as e:
    print(f'Rank {rank}: Dask failed ({e}), falling back to pandas')
    data_chunk_test.to_csv(output_path, index=False)

# =============================================================================
# SHAP FEATURE IMPORTANCE
# =============================================================================

print(f'Rank {rank}: Computing SHAP values...')
raw_shap = compute_shap_values(trained_model, X_train, X_test, device)
raw_shap = np.squeeze(raw_shap, axis=-1)   # (n, features, 1) -> (n, features)

feat_importance = np.mean(np.abs(raw_shap), axis=0)
shap_df = (pd.DataFrame({'Feature': var2, 'Mean|SHAP|': feat_importance})
             .sort_values('Mean|SHAP|', ascending=False))

shap_path = f'{resolution}_{int(rank)}_shap_importance.csv'
shap_df.to_csv(shap_path, index=False)
print(f'Rank {rank}: SHAP table -> {shap_path}')
print(shap_df.to_string(index=False))

if rank == 0:
    print('\n' + '=' * 60)
    print('All ranks completed successfully!')
    print('=' * 60)
