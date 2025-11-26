#!/bin/bash
# Script to collect and aggregate results after SLURM jobs complete

# Define paths
ROOT_DIR="/home/$USER/leaf_splitting"
RUN_DIR="$ROOT_DIR/runs/Even_R1"

# Load conda
module load anaconda3/2024.02
source /share/apps/anaconda3/2024.02/etc/profile.d/conda.sh
conda activate mygpu

# Collect results
python "$ROOT_DIR/core/compare_split_strategies_r1_slurm.py" collect \
    --results_dir "$RUN_DIR/results" \
    --output "$RUN_DIR/aggregated_results.json"

echo "Results collected to $RUN_DIR/aggregated_results.json"

