#!/bin/bash
#SBATCH --account=pr_368_general
#SBATCH --mail-type=ALL                      # Request status by email 
#SBATCH --mail-user=nc1827@nyu.edu         # Email address to send results to

#SBATCH --job-name=compare_strategies_r1
#SBATCH --output=/scratch/nc1827/leaf_splitting/logs/compare_strategies_r1_%A_%a.out
#SBATCH --error=/scratch/nc1827/leaf_splitting/logs/compare_strategies_r1_%A_%a.err
#SBATCH --time=12:00:00
#SBATCH --mem=2G
#SBATCH --cpus-per-task=1

# Calculate array size: num_strategies × num_seeds
# IMPORTANT: Update this if you change the config file!
# Current config: 2 strategies × 20 seeds = 40 tasks (0-39)
# Formula: array should be 0 to (num_strategies × num_seeds - 1)
#SBATCH --array=0-39

# Load conda
module load anaconda3/2024.02
# Enable conda activate
source /share/apps/anaconda3/2024.02/etc/profile.d/conda.sh
# Activate your environment
conda activate mygpu

# Define paths
ROOT_DIR="/home/$USER/leaf_splitting"
RUN_DIR="$ROOT_DIR/runs/Even_R1"
SCRATCH_LOG_DIR="/scratch/$USER/leaf_splitting/logs"

# Create output directories
mkdir -p "$RUN_DIR/results"
mkdir -p "$SCRATCH_LOG_DIR"

# Run the comparison task
python "$ROOT_DIR/core/compare_split_strategies_r1_slurm.py" run \
    --config "$RUN_DIR/split_strategy_config.json" \
    --task_id $SLURM_ARRAY_TASK_ID \
    --output_dir "$RUN_DIR/results"

echo "Task $SLURM_ARRAY_TASK_ID completed"

