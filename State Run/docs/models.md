# Model notes

Shared settings for the PyTorch scripts: AdamW (lr 3e-4, betas 0.9/0.99, no weight decay), 12
warm-up epochs then cosine decay to 1e-6 over 60 epochs, batch size 4096, Huber loss (`SmoothL1`,
beta 0.2), BF16 autocast, gradient clipping at 1.0, 10% of the shard held out for early stopping,
best-validation weights restored. Seed is `1337 + rank`.

## GLU

Each feature group passes through BatchNorm and a sigmoid gate. The groups are concatenated and
projected to 256 units, then go through residual pre-norm GLU blocks (1 by default) and a small
head. Patience is 7 epochs. After early stopping the model runs a 20-epoch stochastic weight
averaging tail at 10% of the peak learning rate, recomputes BatchNorm statistics, and uses the
averaged weights for prediction.

## TabNet

Six sequential attention steps with sparsemax masks, a prior-scale reuse penalty (`gamma` 1.5),
shared plus step-specific GLU feature transformers, and an entropy penalty on the masks
(`LAMBDA_SPARSE` 1e-4). Patience is 12 epochs. This is a simplified implementation: no ghost batch
norm, no split of the hidden vector into decision and attention parts, and only the first shared
layer is used. `N_INDEP` is accepted but unused.

## TFT

An adaptation of the Temporal Fusion Transformer to non-sequential data. A variable-selection
network per feature group produces one embedding per group. The static embedding becomes a context
vector that conditions the dynamic and temporal selection networks and a shared enrichment GRN. A
Transformer encoder runs across the three group tokens, and a linear head on the concatenated
tokens gives the prediction. `output_grn` is created but unused, and is kept so seeded
initialisation matches earlier runs. Patience is 12 epochs.

## XGBoost

GPU `hist` booster. With `TUNE = True`, each rank runs an Optuna study (50 trials) minimising test
RMSE. With `TUNE = False`, the rank loads `{stem}_best_params.json` if present, else the defaults in
the script. SHAP uses `TreeExplainer(approximate=True)` on 500 training rows.

## Random Forest

cuML `RandomForestRegressor` (MSE criterion, bootstrap). Rank 0 evaluates up to 60 random
combinations from a discrete grid with 3-fold CV R2 on a 50,000-row subsample and broadcasts the
winner. Combinations that fail, typically from GPU out-of-memory, are logged as `OOM` and skipped.
SHAP uses `KernelExplainer` with 200 background and 500 explained rows: slow but model-agnostic.
