bind = "127.0.0.1:8000"
workers = 3
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Logging
accesslog = "/home/ubuntu/shristi/logs/gunicorn-access.log"
errorlog = "/home/ubuntu/shristi/logs/gunicorn-error.log"
loglevel = "info"

# Process naming
proc_name = "shristi_printing"

# Server mechanics
daemon = False
pidfile = "/home/ubuntu/shristi/gunicorn.pid"
user = "ubuntu"
group = "ubuntu"

# SSL (if needed later)
# keyfile = "/path/to/key.pem"
# certfile = "/path/to/cert.pem"
