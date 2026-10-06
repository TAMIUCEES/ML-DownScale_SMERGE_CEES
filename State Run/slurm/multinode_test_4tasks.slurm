#!/bin/bash
# PyTorch models (GLU, TabNet, TFT), land-cover (_LC) script variants. Those _LC scripts are not in this repo; use multinode_test_4tasks_2.slurm for the noFE versions.
#
# Submit with: sbatch multinode_test_4tasks.slurm
# Edit the module names, venv path, QoS and script paths for your cluster.
#
#SBATCH --job-name=FE_GLU_VISION_1
#SBATCH --output=multinode_mpi.o%j
#SBATCH --error=multinode_mpi.e%j

# ---- Scheduler: this cluster uses QoS instead of a partition, and --time is required ----
#SBATCH --qos=standard
#SBATCH --time=15:00:00

# ---- Resources: 10 MPI ranks in total, one H200 GPU each ----
# --ntasks is the rank count. Tasks are spread across nodes by the scheduler.
# An H200 has 144 GB, so more ranks per node are possible if memory allows.
#SBATCH --ntasks=10
#SBATCH --cpus-per-task=50          # CPU cores per rank (112 cores/node shared by 2 ranks)
#SBATCH --gpus-per-task=1           # one GPU per rank; SLURM sets CUDA_VISIBLE_DEVICES so each rank sees cuda:0
#SBATCH --mem=256G                  # node has 2 TB available; bump if needed

# ---- E-mail notifications (replace the address, or delete these two lines) ----
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --mail-user=you@example.edu

# =============================================================================
# Software environment
# Module names and versions are cluster-specific; check `module avail`.
# =============================================================================

module load GCC/13.3.0          # verify
module load Python/3.12.3       # verify
module load CUDA/12.8.0         # verify — H200 works best on 12.4+
module load OpenMPI/5.0.3       # verify — must be UCX/IB enabled

# Data and output locations read by the Python scripts (edit these).
export SMERGE_DATA_DIR="${SMERGE_DATA_DIR:-/path/to/data}"
export SMERGE_OUT_DIR="${SMERGE_OUT_DIR:-/path/to/results}"


VENV=/scratch/user/$USER/.venv_main
if [[ ! -d "$VENV" ]]; then
    echo "ERROR: venv not found at $VENV — build it on a login node first." >&2
    exit 1
fi
source "$VENV/bin/activate"
# srun tasks do not always inherit the venv, so set PATH and PYTHONPATH explicitly
export PATH="$VENV/bin:$PATH"
export PYTHONPATH="$VENV/lib/python3.12/site-packages:$PYTHONPATH"

# Fail fast if mpi4py is missing or built against the wrong MPI
python3 -c "from mpi4py import MPI; print(f'mpi4py: MPI v{MPI.Get_version()}')" \
    || { echo "ERROR: mpi4py not importable in $VENV"; exit 1; }



# =============================================================================
# Network environment: InfiniBand (mlx5 HCA) enabled; one OpenMP thread per rank
# =============================================================================
export OMP_NUM_THREADS=1          # avoids CPU oversubscription from BLAS/OpenMP inside each rank
export NCCL_DEBUG=WARN
unset  NCCL_IB_DISABLE
export NCCL_IB_HCA=mlx5
export NCCL_SOCKET_IFNAME=^lo,docker
export UCX_TLS=rc,sm,self         # MPI transports: InfiniBand RC, shared memory, loopback

# =============================================================================
# Job info
# =============================================================================
echo "=========================================="
echo "VISION Multi-Node MPI Job (PyTorch)"
echo "=========================================="
echo "Job ID:       $SLURM_JOB_ID"
echo "Nodes:        $SLURM_NNODES ($SLURM_NODELIST)"
echo "Tasks/node:   $SLURM_NTASKS_PER_NODE"
echo "Total tasks:  $SLURM_NTASKS"
echo "CPUs/task:    $SLURM_CPUS_PER_TASK"
echo "GPUs/task:    1 (H200, 144 GB)"
echo "Start:        $(date)"
echo "=========================================="

# =============================================================================
# Training loop: one srun per state (and per model); every rank gets its own
# shard of the data. The trailing 0 is the 'parting' output offset.
# =============================================================================
STATES=(BigArea)



for STATE in "${STATES[@]}"; do
    echo ">>> Training: $STATE  ($(date +%H:%M:%S))" >&2
    srun --mpi=pmix \
         --ntasks=$SLURM_NTASKS \
         --cpus-per-task=$SLURM_CPUS_PER_TASK \
         python3 -u /home/$USER/PyT_GLU_MPIv10_noFE_LC.py "$STATE" 0
    echo ">>> Done:     $STATE  ($(date +%H:%M:%S))"
    echo
done

for STATE in "${STATES[@]}"; do
    echo ">>> Training: $STATE  ($(date +%H:%M:%S))" >&2
    srun --mpi=pmix \
         --ntasks=$SLURM_NTASKS \
         --cpus-per-task=$SLURM_CPUS_PER_TASK \
         python3 -u /home/$USER/PyT_TabNet_MPIv2_noFE_LC.py "$STATE" 0
    echo ">>> Done:     $STATE  ($(date +%H:%M:%S))"
    echo
done

for STATE in "${STATES[@]}"; do
    echo ">>> Training: $STATE  ($(date +%H:%M:%S))" >&2
    srun --mpi=pmix \
         --ntasks=$SLURM_NTASKS \
         --cpus-per-task=$SLURM_CPUS_PER_TASK \
         python3 -u /home/$USER/PyT_TFT_MPIv1_noFE_LC.py "$STATE" 0
    echo ">>> Done:     $STATE  ($(date +%H:%M:%S))"
    echo
done
echo "=========================================="
echo "Job completed: $(date)"
echo "=========================================="
# Print CPU and memory efficiency for this job if seff is installed
command -v seff &>/dev/null && seff "$SLURM_JOB_ID"
