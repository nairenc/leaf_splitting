#!/bin/bash
#SBATCH --account=pr_368_general
#SBATCH --mail-type=ALL                      # Request status by email 
#SBATCH --mail-user=nc1827@nyu.edu         # Email address to send results to

#SBATCH --job-name=even_split_B256-512
#SBATCH --output=/scratch/nc1827/leaf_splitting/logs/even_split_B256-512_%A_%a.out
#SBATCH --error=/scratch/nc1827/leaf_splitting/logs/even_split_B256-512_%A_%a.err
#SBATCH --time=6:00:00                       # 6 hours per task (max r=257 for B=512)
#SBATCH --mem=4G                             # 4GB memory
#SBATCH --cpus-per-task=1
#SBATCH --array=0-5139
# Even split simulation: 20 seeds × 257 B values = 5,140 tasks
# B values: 256 to 512 (step=1, every value)
# Each task runs r values from 1 to B/2+1:
#   B=256: 129 r values
#   B=512: 257 r values (largest)

# Load conda
module load anaconda3/2024.02
# Enable conda activate
source /share/apps/anaconda3/2024.02/etc/profile.d/conda.sh
# Activate your environment
conda activate mygpu

# Define paths
ROOT_DIR="/home/$USER/leaf_splitting"
RUN_DIR="$ROOT_DIR/runs/Fix_R/B256-512_even_split_s20"
SCRATCH_LOG_DIR="/scratch/$USER/leaf_splitting/logs"

# Create output directories
mkdir -p "$RUN_DIR/results"
mkdir -p "$SCRATCH_LOG_DIR"

# Run the even split simulation task
python "$ROOT_DIR/core/leaf_splitting_sim_even_split_slurm.py" run \
    --config "$RUN_DIR/even_split_config.json" \
    --task_id $SLURM_ARRAY_TASK_ID \
    --output_dir "$RUN_DIR/results"

echo "Task $SLURM_ARRAY_TASK_ID completed"

