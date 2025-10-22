#!/bin/bash
#SBATCH --account=pr_368_general
#SBATCH --mail-type=ALL                      # Request status by email 
#SBATCH --mail-user=nc1827@nyu.edu         # Email address to send results to

#SBATCH --job-name=deferred_sweep
#SBATCH --output=/scratch/nc1827/leaf_splitting/logs/sweep_%A_%a.out
#SBATCH --error=/scratch/nc1827/leaf_splitting/logs/sweep_%A_%a.err
#SBATCH --time=10:00:00                      # ADJUST: Time per job (HH:MM:SS)
#SBATCH --mem=2G                             # ADJUST: Memory per job
#SBATCH --cpus-per-task=1
#SBATCH --array=0-999                        # ADJUST: 0 to (total_tasks - 1)
# 
# CONFIGURATION INFO:
# Update the array size based on config output
# Example: 20 seeds × 120 r values = 2400 tasks → --array=0-2399

# Load conda (adjust module name if needed)
module load anaconda3/2024.02
# Enable conda activate
source /share/apps/anaconda3/2024.02/etc/profile.d/conda.sh
# Activate your environment (change 'mygpu' to your env name)
conda activate mygpu

# Define paths
# ADJUST THIS if you put the project in a different location
ROOT_DIR="/home/$USER/leaf_splitting"
# ADJUST THIS to match your specific run directory name
RUN_DIR="$ROOT_DIR/runs/YOUR_RUN_NAME_HERE"
SCRATCH_LOG_DIR="/scratch/$USER/leaf_splitting/logs"

# Create output directories
mkdir -p "$RUN_DIR/results"
mkdir -p "$SCRATCH_LOG_DIR"

# Run the simulation task
python "$ROOT_DIR/deferred_split_slurm.py" run \
    --config "$RUN_DIR/sweep_config.json" \
    --task_id $SLURM_ARRAY_TASK_ID \
    --output_dir "$RUN_DIR/results"

echo "Task $SLURM_ARRAY_TASK_ID completed"

