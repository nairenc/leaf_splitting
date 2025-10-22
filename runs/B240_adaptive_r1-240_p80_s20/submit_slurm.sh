#!/bin/bash
#SBATCH --account=pr_368_general
#SBATCH --mail-type=ALL                      # Request status by email 
#SBATCH --mail-user=nc1827@nyu.edu         # Email address to send results to

#SBATCH --job-name=adaptive_sweep_B240
#SBATCH --output=/scratch/nc1827/leaf_splitting/logs/B240_adp_p80_sweep_%A_%a.out
#SBATCH --error=/scratch/nc1827/leaf_splitting/logs/B240_adp_p80_sweep_%A_%a.err
#SBATCH --time=12:00:00
#SBATCH --mem=2G
#SBATCH --cpus-per-task=1
#SBATCH --array=0-4799
# PRODUCTION RUN: 20 seeds × 240 r values = 4800 tasks (each runs 80 p values internally)
# Total: 4800 tasks × 80 p values = 384,000 simulations with sqrt-scaled insertions

# Load conda
module load anaconda3/2024.02
# Enable conda activate
source /share/apps/anaconda3/2024.02/etc/profile.d/conda.sh
# Activate your environment
conda activate mygpu

# Define paths
ROOT_DIR="/home/$USER/leaf_splitting"
RUN_DIR="$ROOT_DIR/runs/B240_adaptive_r1-240_p80_s20"
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


