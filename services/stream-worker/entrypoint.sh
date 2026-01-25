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

# Fix permissions for model weights directory (important for Docker volumes)
# This requires root privileges, which we have at the start of this script.
echo "Ensuring /app/src/models/weights is owned by appuser..."
mkdir -p /app/src/models/weights
chown -R appuser:appuser /app/src/models/weights

# Note: Thread configuration (OMP_NUM_THREADS, etc.) is handled 
# dynamically in gunicorn_config.py's post_fork hook for optimal 
# performance per worker.

# Start gunicorn via gosu to drop privileges to appuser
echo "Starting application as appuser..."
exec gosu appuser gunicorn -c gunicorn_config.py app:app
