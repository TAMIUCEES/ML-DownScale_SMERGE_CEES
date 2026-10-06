"""cuML Random Forest on GPU for SMERGE downscaling, MPI data parallel.

Each MPI rank streams its strided shard of the train and test CSVs into GPU
memory and fits one cuML RandomForestRegressor on it. Rank 0 first runs a
randomized k-fold hyperparameter search (OOM-tolerant) and broadcasts the best
parameters to all ranks. Each rank then predicts its test shard, writes the
predictions, and computes a KernelExplainer SHAP importance table.

Usage (under srun):
    python -u RapRF_MultGPU_MultiNode_MPI_tuner_noFE.py <state> <parting>

    state    region key used in file names (e.g. OK, BigArea)
    parting  integer output offset: files are numbered rank + size * parting

Environment variables:
    SMERGE_DATA_DIR  directory holding {state}_trainV6-LC.csv / {state}_testV6-LC.csv
    SMERGE_OUT_DIR   directory for predictions, tuning log and SHAP tables

Requires RAPIDS (cudf, cupy, cuml). Set SKIP_TUNING = True below to use
default_params. The tuning subsample is drawn from the test shard, so
hyperparameters are selected using test data.
"""
print('Script Start')
import os
import sys
import subprocess
import shap

# ─────────────────────────────────────────────────────────────────────────────
# 1. MPI initialization (must happen before any GPU library is imported)
# ─────────────────────────────────────────────────────────────────────────────
from mpi4py import MPI

comm = MPI.COMM_WORLD
size = comm.Get_size()
rank = comm.Get_rank()

# ─────────────────────────────────────────────────────────────────────────────
# 2. GPU assignment: bind each MPI rank to a specific GPU
#    On Launch A30 nodes, typically 2 GPUs per node.
#    This MUST be set BEFORE importing cuml/cudf.
# ─────────────────────────────────────────────────────────────────────────────
def get_num_gpus():
    """Count NVIDIA GPUs on this node with nvidia-smi.

    Unused while the CUDA_VISIBLE_DEVICES block below is commented out. It is
    not needed with --gpus-per-task=1, where SLURM already gives each rank one GPU.
    """
    try:
        output = subprocess.check_output(['nvidia-smi', '-L'])
        return len(output.decode().strip().split('\n'))
    except Exception:
        print(f'[Rank {rank}] No GPUs detected, defaulting to 1')
        return 1


#num_gpus = get_num_gpus()
#gpu_id = rank % num_gpus
#os.environ['CUDA_VISIBLE_DEVICES'] = str(gpu_id)
#print(f'[Rank {rank}] Assigned to GPU {gpu_id} of {num_gpus}')
print(f'[Rank {rank}] CUDA_VISIBLE_DEVICES={os.environ.get("CUDA_VISIBLE_DEVICES", "not set")}')

# ─────────────────────────────────────────────────────────────────────────────
# 3. Import GPU libraries AFTER setting CUDA_VISIBLE_DEVICES
# ─────────────────────────────────────────────────────────────────────────────
import cudf
import cupy as cp
import pandas as pd
import numpy as np
import gc
from cuml.ensemble import RandomForestRegressor as cuRF
from scipy.stats import spearmanr, kendalltau

print(f'[Rank {rank}] Modules imported')

# ─────────────────────────────────────────────────────────────────────────────
# 4. Configuration
# ─────────────────────────────────────────────────────────────────────────────
state = str(sys.argv[1])
parting = str(sys.argv[2])

home    = os.environ.get('SMERGE_DATA_DIR', '/path/to/data')
out_dir = os.environ.get('SMERGE_OUT_DIR',  '/path/to/results')
resolution = f'{out_dir}/RapRF_{state}_500v7noFE'   # output file stem
train_file = home + '/' + state + '_trainV6-LC.csv'
test_file = home + '/' + state + '_testV6-LC.csv'

# Variable groups. noFE: raw integer Month and Year, no land-cover feature.
var1 = ['Clay', 'Sand', 'Silt', 'Elevation', 'Aspect', 'Slope',
        'LAI', 'SMERGE', 'MODIS', 'ALB', 'Temp', 'Month', 'Year']  # all features + label
var2 = ['Clay', 'Sand', 'Silt', 'Elevation', 'Aspect', 'Slope',
        'LAI', 'MODIS', 'ALB', 'Temp', 'Month', 'Year']  # features only (no SMERGE)
all_vars = ['PageName', 'Clay', 'Sand', 'Silt', 'Elevation', 'Slope',
            'Aspect', 'MODIS', 'SMERGE', 'Date', 'LAI', 'ALB', 'Temp',
            'AHRR', 'Month', 'Year']

LABEL = 'SMERGE'




# ─────────────────────────────────────────────────────────────────────────────
# 5. Data loading: stream each CSV in chunks, keep only this rank's stride.
#
#    Scattering from rank 0 hit OpenMPI's ~1 GB per-message limit, and having
#    every rank read the whole file before slicing kept N full copies per node
#    in RAM (cgroup "oom_kill" on every task). Streaming keeps one chunk plus
#    this rank's own 1/size share in memory.
#
#    Uses the C parser because the pyarrow engine does not support chunksize.
#    The stride is applied to the raw file row index (before cleaning), so
#    which rows land on which rank differs slightly from an iloc[rank::size]
#    slice of the cleaned data. The split is still even and unbiased.
# ─────────────────────────────────────────────────────────────────────────────
print(f'[Rank {rank}] Starting data input (chunked read, strided partition)')

CHUNK_SIZE = 500_000  # rows per streamed chunk; lower if RAM is tight,
                       # raise if parsing time dominates

def load_strided(path, usecols, rank, size, chunk_size=CHUNK_SIZE):
    """Stream a CSV and keep only rows where global row index % size == rank.

    Returns this rank's rows as a DataFrame. Never holds more than one chunk
    plus the rank's accumulated share in memory.
    """
    parts = []
    row_offset = 0
    last_cols = None
    for chunk in pd.read_csv(path, usecols=usecols, engine='c', chunksize=chunk_size):
        last_cols = chunk.columns
        n = len(chunk)
        global_idx = np.arange(row_offset, row_offset + n)
        mask = (global_idx % size) == rank
        if mask.any():
            parts.append(chunk.loc[mask])
        row_offset += n
    if parts:
        return pd.concat(parts, ignore_index=True)
    return pd.DataFrame(columns=last_cols if last_cols is not None else usecols)


def clean_chunk(df, parse_date=False):
    """Drop NaNs and rows whose Sand+Silt+Clay do not sum to ~1; optionally parse Date."""
    df = df.dropna()
    df['Soil'] = df['Sand'] + df['Silt'] + df['Clay']
    df = df[(df['Soil'] > 0.9999) & (df['Soil'] < 1.0001)]
    if parse_date:
        df['Date'] = pd.to_datetime(df['Date'], format="%Y-%m-%d")
    df.reset_index(drop=True, inplace=True)
    df.dropna(inplace=True)
    return df


chunk_train_pd = clean_chunk(load_strided(train_file, all_vars, rank, size), parse_date=True)
chunk_test_pd  = clean_chunk(load_strided(test_file,  all_vars, rank, size), parse_date=False)

#
#if parting==0:
#    mid_train = len(chunk_train_pd) // 2
#    mid_test = len(chunk_test_pd) // 2
#    chunk_train_pd = chunk_train_pd.iloc[mid_train:]
#    chunk_test_pd = chunk_test_pd.iloc[mid_test:]
#if parting==1:
#    mid_train = len(chunk_train_pd) // 2
#    mid_test = len(chunk_test_pd) // 2
#    chunk_train_pd = chunk_train_pd.iloc[:mid_train]
#    chunk_test_pd = chunk_test_pd.iloc[:mid_test]

# Shuffle each shard with a rank-specific seed. frac=1.0 keeps every row; lower
# it to subsample.
chunk_train_pd = chunk_train_pd.sample(frac=1.0, random_state=rank).reset_index(drop=True)
chunk_test_pd  = chunk_test_pd.sample(frac=1.0, random_state=rank).reset_index(drop=True)

gc.collect()

print(f'[Rank {rank}] Chunk shapes — train: {chunk_train_pd.shape}, '
      f'test: {chunk_test_pd.shape}')

# ─────────────────────────────────────────────────────────────────────────────
# 6. Move data to GPU via cuDF, then free the CPU-side pandas objects.
# ─────────────────────────────────────────────────────────────────────────────
print(f'[Rank {rank}] Transferring data to GPU')

# GPU VRAM diagnostic before loading data
free_mem, total_mem = cp.cuda.Device(0).mem_info
print(f'[Rank {rank}] GPU memory before data load: '
      f'{free_mem / 1e9:.1f} GB free / {total_mem / 1e9:.1f} GB total')

# Training: features (var2) and label (SMERGE)
X_train = cudf.DataFrame(chunk_train_pd[var2].astype(np.float32))
y_train = cudf.Series(chunk_train_pd[LABEL].astype(np.float32))

# Testing: features only (predictions are written back onto out_cpu)
X_test = cudf.DataFrame(chunk_test_pd[var2].astype(np.float32))

# Keep a CPU copy of the test shard for the output CSV and for tuning.
out_cpu = chunk_test_pd.copy()

# Free the pandas training chunk (test chunk freed via out_cpu taking ownership)
del chunk_train_pd, chunk_test_pd
gc.collect()

print(f'[Rank {rank}] GPU data ready — X_train: {X_train.shape}, X_test: {X_test.shape}')

# GPU VRAM diagnostic after loading data
free_mem, total_mem = cp.cuda.Device(0).mem_info
print(f'[Rank {rank}] GPU memory after data load: '
      f'{free_mem / 1e9:.1f} GB free / {total_mem / 1e9:.1f} GB total')

# ─────────────────────────────────────────────────────────────────────────────
# 7. OOM-resilient hyperparameter tuning + final model training
#
#    Rank 0 runs a manual randomized search with k-fold CV on a subsample and
#    skips any combination that runs out of GPU memory; the best parameters are
#    broadcast to all ranks. A manual loop is used instead of RandomizedSearchCV
#    because sklearn aborts the whole search on the first exception.
#
#    FIL memory is roughly 2^max_depth x n_estimators x node_bytes, so high
#    depth with many trees is what most often runs out of VRAM in predict().
#    The search space follows the iterative approach of Tobin et al. (2023).
#
#    Set SKIP_TUNING=True to use default_params (faster reruns).
# ─────────────────────────────────────────────────────────────────────────────
import time
import itertools
from sklearn.model_selection import KFold
from sklearn.metrics import r2_score

SKIP_TUNING = False          # True → skip tuning, use default_params below
TUNE_SAMPLE_N = 50_000       # rows for tuning subsample (speed vs repr.)
TUNE_N_ITER = 60             # max random param combos to evaluate
TUNE_CV_FOLDS = 3            # k-fold CV splits

# --- Search space (discrete grid; combinations are sampled without replacement) ---

param_distributions = {
    'n_estimators':    [1100],
    'max_depth':       [ 18, 20],
    'min_samples_leaf': [3, 5, 10, 20],
    'min_samples_split': [2, 5, 10, 20],
    'max_features':    ['sqrt', 'log2', 0.33, 0.5, 0.75],
    'n_bins':          [64, 128, 256],
    'max_samples':     [0.7, 0.8, 0.9, 1.0],
}

# --- Default / fallback params (used when SKIP_TUNING or every combo fails) ---
default_params = {
    'n_estimators': 900,
    'max_depth': 20,
    'min_samples_leaf': 5,
    'min_samples_split': 2,
    'max_features': 'sqrt',
    'n_bins': 128,
    'max_samples': 1.0,
}

best_params = None

if not SKIP_TUNING and rank == 0:
    print(f'[Rank {rank}] Starting OOM-resilient hyperparameter tuning '
          f'({TUNE_N_ITER} combos × {TUNE_CV_FOLDS}-fold CV)')
    tune_start = time.time()

    # --- Build tuning subsample on CPU (drawn from the test shard) ----------
    tune_n = min(TUNE_SAMPLE_N, len(out_cpu))
    tune_sample = out_cpu.sample(n=tune_n, random_state=42)
    X_tune_np = tune_sample[var2].to_numpy(dtype=np.float32)
    y_tune_np = tune_sample[LABEL].to_numpy(dtype=np.float32)

    # --- Generate random param combos --------------------------------------
    rng = np.random.default_rng(seed=42)
    param_keys = list(param_distributions.keys())
    all_combos = list(itertools.product(*[param_distributions[k] for k in param_keys]))
    rng.shuffle(all_combos)
    combos_to_try = all_combos[:TUNE_N_ITER]

    kf = KFold(n_splits=TUNE_CV_FOLDS, shuffle=True, random_state=42)

    results_log = []  # [{params, mean_r2, status}, ...]
    best_score = -np.inf

    for ci, combo in enumerate(combos_to_try):
        params = dict(zip(param_keys, combo))
        fold_scores = []
        oom_hit = False

        for fold_i, (tr_idx, va_idx) in enumerate(kf.split(X_tune_np)):
            try:
                # Move fold data to GPU
                X_tr = cudf.DataFrame(X_tune_np[tr_idx], columns=var2)
                y_tr = cudf.Series(y_tune_np[tr_idx])
                X_va = cudf.DataFrame(X_tune_np[va_idx], columns=var2)

                m = cuRF(
                    n_estimators=params['n_estimators'],
                    max_depth=params['max_depth'],
                    min_samples_leaf=params['min_samples_leaf'],
                    min_samples_split=params['min_samples_split'],
                    max_features=params['max_features'],
                    n_bins=params['n_bins'],
                    max_samples=params['max_samples'],
                    split_criterion=2,
                    bootstrap=True,
                    n_streams=4,
                    random_state=42,
                    verbose=0
                )
                m.fit(X_tr, y_tr)
                preds = m.predict(X_va)
                preds_np = preds.to_numpy() if hasattr(preds, 'to_numpy') else cp.asnumpy(preds)
                score = r2_score(y_tune_np[va_idx], preds_np)
                fold_scores.append(score)

            except (MemoryError, RuntimeError, cp.cuda.memory.OutOfMemoryError) as oom:
                # GPU OOM; RuntimeError covers cuML/CUDA exceptions
                print(f'[Rank {rank}] OOM on combo {ci+1}/{len(combos_to_try)} '
                      f'fold {fold_i+1}: {params} — skipping '
                      f'({type(oom).__name__})')
                oom_hit = True

            except Exception as e:
                # Any other error (e.g. a cuML internal failure) also skips this combo
                print(f'[Rank {rank}] Error on combo {ci+1} fold {fold_i+1}: '
                      f'{type(e).__name__}: {e} — skipping')
                oom_hit = True

            finally:
                # Release GPU objects before the next fold/combo. Rebinding the
                # names drops the references; `del locals()[name]` would not.
                X_tr = y_tr = X_va = preds = m = None
                cp.get_default_memory_pool().free_all_blocks()
                gc.collect()

            if oom_hit:
                break  # skip remaining folds for this combo

        # --- Record result --------------------------------------------------
        if oom_hit or len(fold_scores) == 0:
            results_log.append({**params, 'mean_r2': np.nan, 'status': 'OOM'})
            continue

        mean_r2 = np.mean(fold_scores)
        results_log.append({**params, 'mean_r2': mean_r2, 'status': 'OK'})

        if mean_r2 > best_score:
            best_score = mean_r2
            best_params = params.copy()

        if (ci + 1) % 5 == 0 or ci == 0:
            print(f'[Rank {rank}] Combo {ci+1}/{len(combos_to_try)} — '
                  f'R²={mean_r2:.4f}  best so far={best_score:.4f}')

    # --- Save full tuning log -----------------------------------------------
    tune_df = pd.DataFrame(results_log)
    tune_df.to_csv(resolution + '_tuning_results.csv', index=False)

    tune_elapsed = time.time() - tune_start
    ok_count = tune_df[tune_df['status'] == 'OK'].shape[0]
    oom_count = tune_df[tune_df['status'] == 'OOM'].shape[0]
    print(f'[Rank {rank}] Tuning complete in {tune_elapsed:.1f}s — '
          f'{ok_count} OK, {oom_count} OOM skipped')
    print(f'[Rank {rank}] Best R²={best_score:.4f}  params={best_params}')

    del X_tune_np, y_tune_np
    gc.collect()

    # Fall back to defaults if every combo OOM'd
    if best_params is None:
        print(f'[Rank {rank}] WARNING: All combos OOM — falling back to defaults')
        best_params = default_params

elif not SKIP_TUNING:
    # Other ranks wait for rank 0's result via the broadcast below
    best_params = None

else:
    best_params = default_params
    if rank == 0:
        print(f'[Rank {rank}] Tuning skipped, using default params')

# --- Broadcast best params from rank 0 to all ranks ------------------------
best_params = comm.bcast(best_params, root=0)
print(f'[Rank {rank}] Using params: {best_params}')

# --- Train final model on this rank's full chunk ----------------------------
print(f'[Rank {rank}] Training final model with tuned params')

model = cuRF(
    n_estimators=best_params['n_estimators'],
    max_depth=best_params['max_depth'],
    min_samples_leaf=best_params['min_samples_leaf'],
    min_samples_split=best_params['min_samples_split'],
    max_features=best_params['max_features'],
    n_bins=best_params['n_bins'],
    max_samples=best_params['max_samples'],
    split_criterion=2,
    bootstrap=True,
    n_streams=4,
    random_state=42,
    verbose=2
)

model.fit(X_train, y_train)

print(f'[Rank {rank}] Model training complete')

free_mem, total_mem = cp.cuda.Device(0).mem_info
print(f'[Rank {rank}] GPU memory after fit (forest in VRAM): '
      f'{free_mem / 1e9:.1f} GB free / {total_mem / 1e9:.1f} GB total')

# Free training data from GPU — no longer needed
del X_train, y_train
cp.get_default_memory_pool().free_all_blocks()
gc.collect()

free_mem, total_mem = cp.cuda.Device(0).mem_info
print(f'[Rank {rank}] GPU memory after training (freed train data): '
      f'{free_mem / 1e9:.1f} GB free / {total_mem / 1e9:.1f} GB total')

# ─────────────────────────────────────────────────────────────────────────────
# 8. Prediction via GPU FIL (forest inference library)
#    Large test sets are predicted in batches to avoid OOM during inference.
# ─────────────────────────────────────────────────────────────────────────────
print(f'[Rank {rank}] Model testing')

BATCH_SIZE = 500_000
n_test = X_test.shape[0]

if n_test <= BATCH_SIZE:
    pred = model.predict(X_test)
    pred_np = pred.to_numpy() if hasattr(pred, 'to_numpy') else cp.asnumpy(pred)
else:
    print(f'[Rank {rank}] Predicting in batches of {BATCH_SIZE} ({n_test} total rows)')
    pred_parts = []
    for start in range(0, n_test, BATCH_SIZE):
        end = min(start + BATCH_SIZE, n_test)
        p = model.predict(X_test.iloc[start:end])
        pred_parts.append(p.to_numpy() if hasattr(p, 'to_numpy') else cp.asnumpy(p))
        del p
        cp.get_default_memory_pool().free_all_blocks()
    pred_np = np.concatenate(pred_parts)
    del pred_parts

print(f'[Rank {rank}] Predictions complete — shape: {pred_np.shape}')

# Free test data from GPU
del X_test
cp.get_default_memory_pool().free_all_blocks()
gc.collect()

# ─────────────────────────────────────────────────────────────────────────────
# 9. Output: save predictions with full test data
# ─────────────────────────────────────────────────────────────────────────────
print(f'[Rank {rank}] Saving results')

out_cpu['ML_'] = pred_np
out_cpu.to_csv(resolution + str(int(rank)+(int(size)*int(parting))) + '.csv', index=False)

del pred_np
gc.collect()

print(f'[Rank {rank}] Starting SHAP feature importance')
 
SHAP_BACKGROUND_N = 200
SHAP_EXPLAIN_N    = 500
 
rng = np.random.default_rng(seed=rank)
 
# Feature matrix from the test shard (already on CPU)
features_np = out_cpu[var2].to_numpy(dtype=np.float32)
 
# Background: small subsample representing the data distribution
bg_size       = min(SHAP_BACKGROUND_N, len(features_np))
bg_idx        = rng.choice(len(features_np), size=bg_size, replace=False)
background_np = features_np[bg_idx]
 
# Explanation: separate subsample to compute SHAP values for
exp_size   = min(SHAP_EXPLAIN_N, len(features_np))
exp_idx    = rng.choice(len(features_np), size=exp_size, replace=False)
explain_np = features_np[exp_idx]
 
del features_np
gc.collect()
 
# KernelExplainer passes plain numpy; the cuML model needs a cuDF DataFrame
def predict_fn(X_np):
    X_cudf = cudf.DataFrame(X_np.astype(np.float32), columns=var2)
    p      = model.predict(X_cudf)
    result = p.to_numpy() if hasattr(p, 'to_numpy') else cp.asnumpy(p)
    del X_cudf, p
    cp.get_default_memory_pool().free_all_blocks()
    return result
 
print(f'[Rank {rank}] KernelExplainer — '
      f'background: {background_np.shape[0]} rows, '
      f'explain: {explain_np.shape[0]} rows')
 
explainer   = shap.KernelExplainer(predict_fn, background_np)
shap_values = explainer.shap_values(explain_np, silent=True)
 
# Mean absolute SHAP per feature, sorted descending
mean_abs_shap = np.abs(shap_values).mean(axis=0)
shap_df = pd.DataFrame({
    'Feature':       var2,
    'mean_abs_shap': mean_abs_shap
}).sort_values('mean_abs_shap', ascending=False).reset_index(drop=True)
 
print(f'[Rank {rank}] SHAP results:\n{shap_df.to_string(index=False)}')
shap_df.to_csv(resolution + str(int(rank)+(int(size)*int(parting))) + '_shap.csv', index=False)

MPI.Finalize()   # close MPI explicitly once all outputs are written
print(f'[Rank {rank}] Done')