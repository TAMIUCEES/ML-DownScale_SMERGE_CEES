# HPC notes

Lessons that shaped the scripts. Most cost several failed jobs to learn.

**OpenMPI message ceiling.** A single MPI message is limited to about 1 GB, so scattering a large
DataFrame from rank 0 fails with a "message too big" error. Every rank instead takes its own shard
by strided indexing (`iloc[rank::size]`). Do not use `np.array_split` on a DataFrame to do the
same: recent NumPy returns ndarrays, which breaks column selection by name.

**Host RAM with several ranks per node.** Reading the whole CSV on every rank and then slicing keeps
N full copies alive per node. If every task is "Killed" with `oom_kill` events, that is the cgroup
host-memory limit, not a CUDA allocator error. The Random Forest script streams the CSV in chunks
to avoid it (`CHUNK_SIZE`). The torch and XGBoost scripts still read the full file, so give them
enough `--mem`.

**GPU visibility under SLURM.** With `--gpus-per-task=1` each task sees only `cuda:0`, so the local
device index must be 0. With `--gres=gpu:N`, SLURM does not isolate GPUs per task and ranks must
choose a device themselves (`rank % num_gpus`). `nvidia-smi -L` ignores `CUDA_VISIBLE_DEVICES`
and reports the whole node, so the torch scripts only use it as a fallback.

**Import order.** Initialise MPI first, then import cudf/cuml/torch, so CUDA sees the environment
SLURM set for the task.

**Launching.** Use `srun --mpi=pmix`, put the venv on `PATH` and `PYTHONPATH` explicitly, and use
absolute Python paths; `source activate` is not always inherited by launched tasks.

**XGBoost threads.** Ranks per node times `NTHREAD` must not exceed the node's cores. Oversubscribed
OpenMP threads have caused segfaults in native XGBoost code.

**SHAP on GPU models.** `shap.TreeExplainer` reads tree nodes as CPU pointers and segfaults on a
GPU-resident XGBoost booster. Move it to CPU with `booster.set_param("device", "cpu")` first. The
SHAP background data must use exactly the training feature set; a column-count mismatch silently
misaligns features positionally in XGBoost.

**cuML.** Version 24 and later removed `predict_model='CPU'` and `convert_to_sklearn()` from
`RandomForestRegressor`. FIL memory grows roughly with `2^max_depth * n_estimators`, so
`max_depth` is the main VRAM lever. Predict large test sets in batches.

**BF16.** On Ampere and later, BF16 matches FP16 tensor-core speed with FP32's exponent range, so
small MSE/Huber losses do not underflow and no GradScaler is needed.
