"""
Gunicorn configuration for ML workload optimization
"""
import multiprocessing
import os

# Server socket
bind = "0.0.0.0:8080"
backlog = 2048

# Worker processes
workers = int(os.getenv("GUNICORN_WORKERS", multiprocessing.cpu_count()))
if workers > 2:
    workers = 2  # Limit for memory constraints
if workers < 1:
    workers = 1

worker_class = "sync"
worker_connections = 1000
max_requests = 200
max_requests_jitter = 50
timeout = 300
graceful_timeout = 60
keepalive = 5

# Preload app for model sharing between workers (disabled in dev mode for hot reload)
preload_app = os.getenv("GUNICORN_RELOAD", "false").lower() != "true"

# Hot reload in development
reload = os.getenv("GUNICORN_RELOAD", "false").lower() == "true"
reload_extra_files = []

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "stream-worker"

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# Worker tmp directory (use shared memory for better performance)
worker_tmp_dir = "/dev/shm"


def on_starting(server):
    """Called just before the master process is initialized."""
    is_dev = os.getenv("GUNICORN_RELOAD", "false").lower() == "true"
    mode = "DEVELOPMENT (hot reload enabled)" if is_dev else "PRODUCTION (preload enabled)"
    print(f"Starting gunicorn in {mode}")
    print(f"Workers: {workers}")
    if not is_dev:
        print("Preloading application and ML models...")


def when_ready(server):
    """Called just after the server is started."""
    print("Gunicorn server is ready. Accepting connections.")


def on_reload(server):
    """Called to recycle workers during a reload via SIGHUP."""
    print("Reloading workers...")


def worker_int(worker):
    """Called just after a worker exited on SIGINT or SIGQUIT."""
    print(f"Worker {worker.pid} received INT or QUIT signal")


def pre_fork(server, worker):
    """Called just before a worker is forked."""
    pass


def post_fork(server, worker):
    """Called just after a worker has been forked."""
    cpu_count = multiprocessing.cpu_count()
    # Set PyTorch threading environment variables for each worker
    os.environ["OMP_NUM_THREADS"] = str(cpu_count)
    os.environ["MKL_NUM_THREADS"] = str(cpu_count)
    os.environ["TORCH_NUM_THREADS"] = str(cpu_count)
    print(f"Worker {worker.pid} spawned (will use {cpu_count} threads for PyTorch)")


def worker_abort(worker):
    """Called when a worker received the SIGABRT signal."""
    print(f"Worker {worker.pid} received SIGABRT signal")
