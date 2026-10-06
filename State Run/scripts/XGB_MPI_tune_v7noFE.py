"""XGBoost (GPU) with optional Optuna tuning for SMERGE downscaling, MPI data parallel.

Each MPI rank takes a strided shard of the train and test CSVs and trains its
own XGBoost model on it. With TUNE = True each rank runs an independent Optuna
study and writes its best parameters to JSON; with TUNE = False the rank loads
that JSON if it exists, otherwise falls back to the defaults below. Each rank
then writes its predictions and a SHAP importance table.

Usage (under srun):
    python -u XGB_MPI_tune_v7noFE.py <state> <parting>

    state    region key used in file names (e.g. OK, BigArea)
    parting  integer output offset: files are numbered rank + size * parting,
             so a second pass does not overwrite the first

Environment variables:
    SMERGE_DATA_DIR  directory holding {state}_trainV6-LC.csv / {state}_testV6-LC.csv
    SMERGE_OUT_DIR   directory for predictions, params and SHAP tables

Note: early stopping and tuning use the test shard as the eval set, so test
metrics from this script are optimistic.
"""
print('Script Start')
import os
import sys
import xgboost
from xgboost import XGBRegressor
import xgboost as xgb
import pandas as pd
import numpy as np
import shap
from sklearn.metrics import mean_squared_error, r2_score
import optuna
import json

print('Modules Imported')


# ============================================================
# CONFIGURATION
# ============================================================
# Command-line arguments: region key and output pass number
state   = str(sys.argv[1])
parting = int(sys.argv[2])   # must be int; used to number the output files

TUNE       = False   # True: run Optuna on every rank; False: load saved params
N_TRIALS   = 50      # Optuna trials per rank
EARLY_STOP = 50      # stop after this many rounds without eval improvement
SAMPLE_FRAC = 1.0    # unused; kept for optional subsampling

from mpi4py import MPI

comm = MPI.COMM_WORLD
size = comm.Get_size()
rank = comm.Get_rank()

# Threads per rank. Total threads on a node (ranks x NTHREAD) must not exceed
# its cores: oversubscribing OpenMP caused segfaults in native XGBoost code.
# Defaults to the SLURM allocation when available.
NTHREAD = int(os.environ.get('SLURM_CPUS_PER_TASK', 48))

print("Starting data input")

home    = os.environ.get('SMERGE_DATA_DIR', '/path/to/data')
out_dir = os.environ.get('SMERGE_OUT_DIR',  '/path/to/results')
# Output file stem; the number identifies the rank (and pass, via parting).
resolution = f'{out_dir}/XGB_{state}_500v7noFE' + str(int(rank) + (int(size) * int(parting)))
train_file = home + '/' + state + '_trainV6-LC.csv'
test_file = home + '/' + state + '_testV6-LC.csv'

# noFE: raw integer Month and Year are used directly (no cyclic encoding), and
# no land-cover feature is used. var2 is the model feature list; all_vars is
# every column read from the CSV (AHRR is carried through for validation).
var2     = ['Clay', 'Sand', 'Silt', 'Elevation', 'Aspect', 'Slope', 'LAI', 'MODIS', 'ALB', 'Temp', 'Month', 'Year']
all_vars = ['PageName', 'Clay', 'Sand', 'Silt', 'Elevation', 'Slope', 'Aspect', 'MODIS', 'SMERGE', 'Date', 'LAI', 'ALB', 'Temp', 'AHRR', "Month", "Year"]





# ============================================================
# DATA LOADING & PREPROCESSING
# ============================================================
# Read each CSV, keep rows whose Sand+Silt+Clay fractions sum to ~1, drop NaNs.
train_data_full = pd.read_csv(train_file, usecols=all_vars, engine='pyarrow')#.dropna().sample(frac=SAMPLE_FRAC)
train_data_full['Soil'] = train_data_full['Sand'] + train_data_full['Silt'] + train_data_full['Clay']
train_data_full = train_data_full[(train_data_full['Soil'] > 0.9999) & (train_data_full['Soil'] < 1.0001)]
train_data_full['Date'] = pd.to_datetime(train_data_full['Date'], format="%Y-%m-%d")
train_data_full.reset_index(drop=True, inplace=True)
train_data_full.dropna(inplace=True)

test_data_full = pd.read_csv(test_file, usecols=all_vars, engine='pyarrow')#.dropna().sample(frac=SAMPLE_FRAC)
test_data_full['Soil'] = test_data_full['Sand'] + test_data_full['Silt'] + test_data_full['Clay']
test_data_full = test_data_full[(test_data_full['Soil'] > 0.9999) & (test_data_full['Soil'] < 1.0001)]
test_data_full.reset_index(drop=True, inplace=True)
test_data_full.dropna(inplace=True)

print(f"Train shape: {train_data_full.shape}")
print(f"Test shape:  {test_data_full.shape}")



# ============================================================
# PREPARE TRAIN/TEST ARRAYS (strided per-rank chunks)
# ============================================================
# Every size-th row goes to this rank, so no MPI scatter is needed (OpenMPI
# caps a single message at about 1 GB).
data_chunk_train = train_data_full.iloc[rank::size].reset_index(drop=True)
data_chunk_test  = test_data_full.iloc[rank::size].reset_index(drop=True)

X_train = data_chunk_train[var2].astype(np.float32)
y_train = data_chunk_train['SMERGE']
X_test  = data_chunk_test[var2].astype(np.float32)
y_test  = data_chunk_test['SMERGE']


# ============================================================
# OPTUNA HYPERPARAMETER TUNER
# ============================================================
# Search ranges were narrowed from an earlier set of runs: depth and
# min_child_weight raised, learning rate shifted up (the old ceiling was binding),
# n_estimators widened, regularisation upper bounds lowered, gamma on log scale.

def objective(trial):
    """Fit XGBoost with one set of sampled hyperparameters; return test RMSE.

    Optuna minimises this value. The test shard is used as the early-stopping
    eval set, so the returned RMSE is optimistic.
    """

    param = {
        # Tree structure
        'max_depth':         trial.suggest_int('max_depth', 10, 16),
        'min_child_weight':  trial.suggest_int('min_child_weight', 5, 25),

        # Learning rate and boosting rounds
        'learning_rate':     trial.suggest_float('learning_rate', 3e-4, 5e-3, log=True),
        'n_estimators':      trial.suggest_int('n_estimators', 1800, 3500, step=100),

        # Sampling regularization
        'subsample':         trial.suggest_float('subsample', 0.6, 1.0),
        'colsample_bytree':  trial.suggest_float('colsample_bytree', 0.6, 1.0),
        'colsample_bylevel': trial.suggest_float('colsample_bylevel', 0.7, 1.0),

        # L1/L2/gamma (all log-scale)
        'reg_alpha':         trial.suggest_float('reg_alpha',  1e-3, 3.0, log=True),
        'reg_lambda':        trial.suggest_float('reg_lambda', 1e-3, 5.0, log=True),
        'gamma':             trial.suggest_float('gamma',      1e-4, 0.3, log=True),

        # Fixed
        'device':                  'cuda',
        'tree_method':             'hist',
        'booster':                 'gbtree',
        'nthread':                 NTHREAD,
        'early_stopping_rounds':   EARLY_STOP,
    }

    model = XGBRegressor(**param)
    model.fit(
        X_train.values, y_train,
        eval_set=[(X_test.values, y_test)],
        verbose=False,
        callbacks=[xgb.callback.EarlyStopping(rounds=EARLY_STOP, data_name='validation_0')],
    )

    pred = model.predict(X_test.values.astype(np.float32))
    rmse = np.sqrt(mean_squared_error(y_test, pred))
    return rmse


if TUNE:
    print("=" * 60)
    print("STARTING HYPERPARAMETER TUNING (v7 ranges)")
    print(f"  Trials: {N_TRIALS}")
    print(f"  Early stopping rounds: {EARLY_STOP}")
    print(f"  Train size: {X_train.shape[0]:,} rows x {X_train.shape[1]} features")
    print(f"  Test size:  {X_test.shape[0]:,} rows")
    print("=" * 60)

    # Per-rank independent study (no shared storage, so no SQLite write contention)
    study = optuna.create_study(
        direction='minimize',
        study_name=f'xgb_{state}_tuning_v7_rank{rank}',
        pruner=optuna.pruners.MedianPruner(n_warmup_steps=5),
    )
    study.optimize(objective, n_trials=N_TRIALS, show_progress_bar=True)

    print("\n" + "=" * 60)
    print("TUNING COMPLETE")
    print(f"  Best RMSE: {study.best_value:.6f}")
    print("  Best params:")
    for k, v in study.best_params.items():
        print(f"    {k}: {v}")
    print("=" * 60)

    best_params = study.best_params
    best_params.update({
        'device':      'cuda',
        'tree_method': 'hist',
        'booster':     'gbtree',
        'nthread':     NTHREAD,
    })

    params_file = resolution + '_best_params.json'
    with open(params_file, 'w') as f:
        json.dump(best_params, f, indent=2)
    print(f"Best params saved to: {params_file}")

    trials_df = study.trials_dataframe()
    trials_df.sort_values('value', ascending=True).head(10).to_csv(
        resolution + '_top10_trials.csv', index=False
    )

else:
    params_file = resolution + '_best_params.json'
    if os.path.exists(params_file):
        print(f"Loading saved params from: {params_file}")
        with open(params_file, 'r') as f:
            best_params = json.load(f)
    else:
        print("No saved params found, using default params")
        # Log-scale averages of earlier tuned runs on this 12-feature set.
        # Re-tune with TUNE=True before treating results as final.
        best_params = {
            'max_depth':         16,
            'min_child_weight':  25,
            'learning_rate':     0.002925692749524813,
            'n_estimators':      1500,
            'subsample':         0.970029184560155,
            'colsample_bytree':  0.8265724997008287,
            'colsample_bylevel': 0.9080345905573968,
            'reg_alpha':         0.004203822694069684,
            'reg_lambda':        3.124095653610472,
            'gamma':             0.00021557866485607188,
            'device':            'cuda',
            'tree_method':       'hist',
            'booster':           'gbtree',
            'nthread':           NTHREAD,
        }

# ============================================================
# FINAL MODEL TRAINING WITH BEST PARAMS
# ============================================================
print("\n" + "=" * 60)
print("TRAINING FINAL MODEL")
print(f"  Params: {best_params}")
print("=" * 60)

final_params = dict(best_params)
final_params.setdefault('early_stopping_rounds', EARLY_STOP)
# nthread always comes from this run, even if the JSON was saved with another value
final_params['nthread'] = NTHREAD

model = XGBRegressor(**final_params)
model.fit(
    X_train.values.astype(np.float32),
    y_train,
    eval_set=[(X_test.values.astype(np.float32), y_test)],
    verbose=100,
)

print("Model Testing")
pred = model.predict(X_test.values.astype(np.float32))

rmse = np.sqrt(mean_squared_error(y_test, pred))
r2   = r2_score(y_test, pred)
print(f"\nFinal Model Performance:")
print(f"  RMSE: {rmse:.6f}")
print(f"  R2:   {r2:.4f}")
if hasattr(model, 'best_iteration'):
    print(f"  Best iteration: {model.best_iteration}  (of {final_params.get('n_estimators')})")

# ============================================================
# OUTPUT & SHAP
# ============================================================
print("Saving outputs")

out = data_chunk_test.copy()
out['ML_'] = pred
out.to_csv(resolution + ".csv", index=False)

# SHAP sample: 500 rows from this rank's own train chunk. random_state=rank is
# reproducible but differs per rank, so ranks do not all explain the same rows.
x_sampled = data_chunk_train[var2].sample(
    min(500, len(data_chunk_train)),
    random_state=rank,
)

# SHAP's C++ TreeExplainer reads tree nodes as CPU pointers and segfaults if
# the booster is on the GPU, so move it to CPU first and call TreeExplainer
# directly (shap.Explainer auto-dispatch still hits the same crash).
booster = model.get_booster()
booster.set_param('device', 'cpu')
explainer   = shap.TreeExplainer(booster)
# approximate=True uses a path-based estimate instead of exact traversal; much
# faster at depth 16 / 3500 trees with little effect on feature ranking.
shap_vals   = explainer.shap_values(x_sampled.values.astype(np.float32), approximate=True)
mean_shap   = np.abs(shap_vals).mean(axis=0)
shap_pd     = pd.DataFrame(mean_shap, index=x_sampled.columns).sort_values(by=[0], ascending=False)
shap_pd.to_csv(resolution + '_shap.csv')

print("\nSHAP Feature Importance:")
print(shap_pd)
print("\nDone!")