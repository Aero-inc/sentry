#!/bin/sh
# Entrypoint script to configure gunicorn workers based on available CPU

# Get number of CPU cores
CPU_CORES=$(nproc)

# Optimized worker config for ML inference:
# Use 1 worker per CPU core (model loads once per worker, no fork issues)
# Each worker handles ~100-200 concurrent requests via async
WORKERS=$CPU_CORES
if [ $WORKERS -lt 1 ]; then
    WORKERS=1
fi
if [ $WORKERS -gt 4 ]; then
    WORKERS=4
fi

echo "Starting with $WORKERS gunicorn workers (CPU cores: $CPU_CORES)"

# Start gunicorn with optimized settings for ML workloads
exec gunicorn --bind 0.0.0.0:8080 \
     --workers $WORKERS \
     --worker-class sync \
     --timeout 120 \
     --graceful-timeout 30 \
     --preload-app \
     --worker-tmp-dir /dev/shm \
     --access-logfile - \
     --error-logfile - \
     --log-level info \
     app:app
