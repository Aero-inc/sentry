# Multi-stage Dockerfile for Stream Worker (CPU variant - Optimized)
FROM python:3.11-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment and install Python packages
WORKDIR /build
COPY requirements.txt .
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir --upgrade pip && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.11-slim

# Install only runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    curl \
    gosu \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Set PATH to use virtual environment
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

###############################################################
# Create app directory and non-root user
# Permissions set here only affect files/directories in the image.
# For directories mounted as Docker volumes, set permissions in entrypoint.sh.
###############################################################
WORKDIR /app
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app

# Copy application code (cleaner glob handling)
COPY --chown=appuser:appuser . .

# Setup entrypoint with cross-platform compatibility
RUN sed -i 's/\r$//' /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Expose port
EXPOSE 8080

# Health check (uses curl from runtime deps)
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Start as root to allow entrypoint to fix volume permissions.
# The entrypoint script will drop privileges to appuser using gosu.
ENTRYPOINT ["/app/entrypoint.sh"]
