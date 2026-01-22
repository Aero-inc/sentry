#!/bin/sh
# Entrypoint script optimized for CPU-bound ML inference workloads

# Get number of CPU cores
CPU_CORES=$(nproc)

# For CPU-bound ML inference:
# - Use sync workers (GIL prevents thread parallelism)
# - Limit workers to prevent memory exhaustion (models are large)
# - Each worker gets full CPU for inference
if [ $CPU_CORES -le 2 ]; then
    WORKERS=1
else
    WORKERS=2
fi

echo "Container has $CPU_CORES CPU cores available"
echo "Configuring $WORKERS gunicorn workers"

# Export worker count for gunicorn config
export GUNICORN_WORKERS=$WORKERS

# Configure PyTorch to use all available cores per inference
export OMP_NUM_THREADS=$CPU_CORES
export MKL_NUM_THREADS=$CPU_CORES
export TORCH_NUM_THREADS=$CPU_CORES

# Start gunicorn with config file
exec gunicorn -c gunicorn_config.py app:app
