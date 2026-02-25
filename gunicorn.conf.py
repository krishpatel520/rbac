"""
Gunicorn configuration for the RBAC Service.

All runtime tuning lives here rather than being scattered across CLI args.
Reference: https://docs.gunicorn.org/en/stable/settings.html
"""
import multiprocessing

# ─────────────────────────────────────────────────────────────────────
# Server socket
# ─────────────────────────────────────────────────────────────────────
bind = "0.0.0.0:8002"

# ─────────────────────────────────────────────────────────────────────
# Workers
# ─────────────────────────────────────────────────────────────────────
# Formula: 2 × num_cpus + 1  (standard recommendation for I/O-bound Django)
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"          # Use 'gevent' or 'gthread' for async
threads = 1                    # Threads per worker (relevant for gthread)

# ─────────────────────────────────────────────────────────────────────
# Timeouts
# ─────────────────────────────────────────────────────────────────────
timeout = 120          # Kill worker if it doesn't respond within 120 s
graceful_timeout = 30  # Time to finish in-flight requests on SIGTERM
keepalive = 5          # Seconds to wait for the next request on a keep-alive connection

# ─────────────────────────────────────────────────────────────────────
# Process naming
# ─────────────────────────────────────────────────────────────────────
proc_name = "rbac_service"

# ─────────────────────────────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────────────────────────────
accesslog  = "-"    # stdout  → captured by Docker logging driver
errorlog   = "-"    # stderr  → captured by Docker logging driver
loglevel   = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s μs'

# ─────────────────────────────────────────────────────────────────────
# Security
# ─────────────────────────────────────────────────────────────────────
forwarded_allow_ips = "*"   # Trust X-Forwarded-For from upstream proxy/LB
