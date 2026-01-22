#!/bin/sh
# Entrypoint script to configure gunicorn workers based on available CPU

# Get number of CPU cores
CPU_CORES=$(nproc)

# Calculate workers: (2 * CPU) + 1, capped at 8
WORKERS=$((2 * CPU_CORES + 1))
if [ $WORKERS -gt 8 ]; then
    WORKERS=8
fi

echo "Starting with $WORKERS gunicorn workers (CPU cores: $CPU_CORES)"

# Start gunicorn with calculated workers
exec gunicorn --bind 0.0.0.0:8080 \
     --workers $WORKERS \
     --worker-class sync \
     --timeout 120 \
     --graceful-timeout 30 \
     --max-requests 1000 \
     --max-requests-jitter 100 \
     --access-logfile - \
     --error-logfile - \
     --log-level info \
     app:app
