#!/bin/bash
#SBATCH --account=pr_368_general
#SBATCH --mail-type=ALL
#SBATCH --mail-user=nc1827@nyu.edu

#SBATCH --job-name=test_def_B120
#SBATCH --output=/scratch/nc1827/leaf_splitting/logs/test_def_B120_%A_%a.out
#SBATCH --error=/scratch/nc1827/leaf_splitting/logs/test_def_B120_%A_%a.err
#SBATCH --time=01:00:00
#SBATCH --mem=2G
#SBATCH --cpus-per-task=1
#SBATCH --array=0-39
# TEST RUN: 20 seeds × 2 r values = 40 tasks (each runs 40 p values)
# r=1: 200k insertions, r=60: 874k insertions
# Total: 40 tasks × 40 p values = 1,600 simulations
# Insertion strategy: sqrt scaling

# Load conda
module load anaconda3/2024.02
# Enable conda activate
source /share/apps/anaconda3/2024.02/etc/profile.d/conda.sh
# Activate your environment
conda activate mygpu

# Define paths
ROOT_DIR="/home/$USER/leaf_splitting"
RUN_DIR="$ROOT_DIR/runs/test_deferred_B120"
SCRATCH_LOG_DIR="/scratch/$USER/leaf_splitting/logs"

# Create output directories
mkdir -p "$RUN_DIR/results"
mkdir -p "$SCRATCH_LOG_DIR"

# Run the simulation task
python "$ROOT_DIR/leaf_splitting_sim_slurm.py" run \
    --config "$RUN_DIR/sweep_config.json" \
    --task_id $SLURM_ARRAY_TASK_ID \
    --output_dir "$RUN_DIR/results"

echo "Task $SLURM_ARRAY_TASK_ID completed"

