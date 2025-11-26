#!/bin/bash
#SBATCH --account=pr_368_general
#SBATCH --mail-type=ALL
#SBATCH --mail-user=nc1827@nyu.edu

#SBATCH --job-name=B240_hard_p06
#SBATCH --output=/scratch/nc1827/leaf_splitting/logs/B240_hardcase_%A_%a.out
#SBATCH --error=/scratch/nc1827/leaf_splitting/logs/B240_hardcase_%A_%a.err
#SBATCH --time=4:00:00                       # 4 hours per task (720M insertions)
#SBATCH --mem=4G                             # 4GB memory
#SBATCH --cpus-per-task=1
#SBATCH --array=0-19                         # 20 seeds (tasks 0-19)

# Load conda
module load anaconda3/2024.02
source /share/apps/anaconda3/2024.02/etc/profile.d/conda.sh
conda activate mygpu

# Define paths
ROOT_DIR="/home/$USER/leaf_splitting"
RUN_DIR="$ROOT_DIR/runs/Var_R/B240_immediately_hardcase_p06_seq1M"
SCRATCH_LOG_DIR="/scratch/$USER/leaf_splitting/logs"

# Create output directories
mkdir -p "$RUN_DIR/results"
mkdir -p "$SCRATCH_LOG_DIR"

# Run the sequence simulation task
python "$ROOT_DIR/core/leaf_splitting_sim_sequence_slurm.py" run \
    --config "$RUN_DIR/sequence_sweep_config.json" \
    --task_id $SLURM_ARRAY_TASK_ID \
    --output_dir "$RUN_DIR/results"

echo "Task $SLURM_ARRAY_TASK_ID completed"

