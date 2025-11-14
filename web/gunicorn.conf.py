"""
Gunicorn configuration for Jira Flow Analyzer.

This configuration uses Uvicorn workers for optimal async performance
with FastAPI while leveraging Gunicorn's process management.
"""

import multiprocessing
import os

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes
# Formula: (2 x $num_cores) + 1
# Can be overridden with GUNICORN_WORKERS environment variable
workers = int(os.getenv("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1))

# Worker class - use uvicorn worker for async support
worker_class = "uvicorn.workers.UvicornWorker"

# Worker connections - only relevant for sync workers, but set for consistency
worker_connections = 1000

# Timeouts
timeout = 120  # 2 minutes for long-running report generation
keepalive = 5

# Graceful timeout for worker shutdown
graceful_timeout = 30

# Maximum requests per worker before restart (helps with memory leaks)
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = "-"  # Log to stdout
errorlog = "-"   # Log to stderr
loglevel = os.getenv("LOG_LEVEL", "info")
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "jira-flow-analyzer"

# Preload application for better performance
preload_app = True

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (if needed)
# keyfile = "/path/to/key.pem"
# certfile = "/path/to/cert.pem"


def on_starting(server):
    """Called just before the master process is initialized."""
    server.log.info("Starting Jira Flow Analyzer with Gunicorn + Uvicorn workers")
    server.log.info(f"Workers: {workers}")
    server.log.info(f"Worker class: {worker_class}")


def on_reload(server):
    """Called to recycle workers during a reload via SIGHUP."""
    server.log.info("Reloading workers...")


def when_ready(server):
    """Called just after the server is started."""
    server.log.info("Server is ready. Spawning workers")


def pre_fork(server, worker):
    """Called just before a worker is forked."""
    pass


def post_fork(server, worker):
    """Called just after a worker has been forked."""
    server.log.info(f"Worker spawned (pid: {worker.pid})")


def pre_exec(server):
    """Called just before a new master process is forked."""
    server.log.info("Forked child, re-executing.")


def worker_int(worker):
    """Called when a worker receives the SIGINT or SIGQUIT signal."""
    worker.log.info("Worker received INT or QUIT signal")


def worker_abort(worker):
    """Called when a worker receives the SIGABRT signal."""
    worker.log.info("Worker received SIGABRT signal")
