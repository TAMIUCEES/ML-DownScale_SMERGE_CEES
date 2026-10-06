# smerge-downscaling-mpi

MPI data-parallel training scripts for ML downscaling of SMERGE soil moisture (about 12.5 km) to
about 500 m across the U.S. Southern Great Plains. There is one self-contained script per model.

| Script | Model | Hardware |
| --- | --- | --- |
| `scripts/PyT_GLU_MPIv10_noFE.py` | Grouped-gate GLU MLP with an SWA tail | GPU (PyTorch) |
| `scripts/PyT_TabNet_MPIv2_noFE.py` | Simplified TabNet | GPU (PyTorch) |
| `scripts/PyT_TFT_MPIv1_noFE.py` | Temporal Fusion Transformer adapted to tabular data | GPU (PyTorch) |
| `scripts/XGB_MPI_tune_v7noFE.py` | XGBoost with optional Optuna tuning | GPU (`device=cuda`) |
| `scripts/RapRF_MultGPU_MultiNode_MPI_tuner_noFE.py` | Random Forest with OOM-tolerant tuning | GPU (RAPIDS cuML) |

Each MPI rank takes a strided shard of the training and test CSVs, trains its own model, and writes
its own predictions and SHAP importance table. There is no gradient synchronisation and no MPI data
scatter. Combining per-rank outputs and validating them (AVHRR/VIIRS NDVI anomalies, streamflow) is
done downstream and is not part of this repository.

"noFE" means no feature engineering: raw integer Month and Year, and no land-cover feature.

## Layout

```
scripts/   the five training scripts
slurm/     job scripts (XGBoost, Random Forest, PyTorch with and without _LC variants)
docs/      data schema, model notes, HPC notes, known issues
```

## Inputs

Two CSVs per region: `{state}_trainV6-LC.csv` and `{state}_testV6-LC.csv`. Columns, features and
feature groups are described in [docs/data_schema.md](docs/data_schema.md).

## Install

Two environments are recommended, because RAPIDS pins CUDA-specific packages.

```bash
# PyTorch + XGBoost
python -m venv .venv_main && source .venv_main/bin/activate
pip install torch --index-url https://download.pytorch.org/whl/cu128    # match your CUDA
pip install -r requirements-torch.txt      # mpi4py must build against the cluster OpenMPI

# cuML Random Forest
python -m venv .venv_rapids && source .venv_rapids/bin/activate
# install RAPIDS (cudf, cuml, cupy) for your CUDA version, then:
pip install -r requirements-rapids.txt
```

## Run

Set where the data lives and where results go:

```bash
export SMERGE_DATA_DIR=/path/to/csvs
export SMERGE_OUT_DIR=/path/to/results
```

Every script takes the same two positional arguments, a region key and a pass number:

```bash
srun --mpi=pmix python -u scripts/PyT_GLU_MPIv10_noFE.py OK 0
```

The job scripts in `slurm/` run the scripts in sequence. Before submitting, edit the script paths
(they point at `/home/$USER/`), module names, venv location, QoS and e-mail address. The
`multinode_test_4tasks.slurm` and `multinode_RapRF_4tasks.slurm` files also reference `_LC`
(land-cover) script variants that are not in this repository.

Options are set by editing constants near the top of each script, for example `TUNE` and `N_TRIALS`
in the XGBoost script and `SKIP_TUNING` in the Random Forest script.

## Outputs

Files are written to `SMERGE_OUT_DIR`, one set per rank.

| Script | Predictions | SHAP table | Other |
| --- | --- | --- | --- |
| GLU | `GLU_{state}_500v10noFE-{rank}_{rank}.csv` | `..._shap_importance.csv` | |
| TabNet | `TabNet_{state}_500v1noFE-{rank}_{rank}.csv` | `..._shap_importance.csv` | |
| TFT | `TFT_{state}_500v1noFE-{rank}_{rank}.csv` | `..._shap_importance.csv` | |
| XGBoost | `XGB_{state}_500v7noFE{n}.csv` | `..._shap.csv` | `..._best_params.json`, `..._top10_trials.csv` with `TUNE = True` |
| Random Forest | `RapRF_{state}_500v7noFE{n}.csv` | `..._shap.csv` | `RapRF_{state}_500v7noFE_tuning_results.csv` |

Here `n = rank + size * parting`. Predictions are the rank's test shard with an extra `ML_` column
(predicted SMERGE). The version tag in the name (`500v7noFE`, ...) is a hardcoded string; bump it
by hand before a new run so earlier outputs are not overwritten.

## Caveats

- The Spearman value printed by the PyTorch scripts is a quick sanity check on monthly anomaly
  series for that rank's shard only, not a pixel-level statistic.
- XGBoost early stopping and tuning, and the Random Forest tuning subsample, use the test shard,
  so reported test metrics are optimistic. See [docs/known_issues.md](docs/known_issues.md).
- MPI, SLURM and GPU pitfalls that shaped the design are in [docs/hpc_notes.md](docs/hpc_notes.md).
- Model descriptions are in [docs/models.md](docs/models.md).

## Differences from the working versions

Logic, hyperparameters and output formats are unchanged. Edits are limited to:

- Cluster paths replaced by `SMERGE_DATA_DIR` / `SMERGE_OUT_DIR`; the e-mail address replaced by a
  placeholder in the SLURM files.
- Docstrings and comments added; stale change-log comments removed.
- XGBoost: `NTHREAD` reads `SLURM_CPUS_PER_TASK` (default 48); unused variables removed.
- Random Forest: the per-fold GPU cleanup used `del locals()[name]`, which does nothing; it now
  rebinds the names to `None`.

## License

Add a license and citation details before publishing. The input data products (SMERGE, MODIS,
AVHRR, VIIRS, NLCD) have their own terms.
