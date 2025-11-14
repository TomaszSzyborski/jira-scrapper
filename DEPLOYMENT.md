# Production Deployment Guide

This guide covers deploying the Jira Flow Analyzer web service in production using Gunicorn with Uvicorn workers for maximum performance and CPU efficiency.

## 🚀 Architecture Overview

The production deployment uses:
- **Gunicorn** - Process manager and load balancer
- **Uvicorn Workers** - ASGI server for async FastAPI support
- **Multiple Workers** - Utilize all CPU cores efficiently
- **Docker** - Containerized deployment
- **Docker Secrets** - Secure credential management

### Why Gunicorn + Uvicorn?

- **Gunicorn**: Robust process management, graceful restarts, load balancing across workers
- **Uvicorn Workers**: High-performance async support for FastAPI
- **Combined**: Best of both worlds - Gunicorn's stability with Uvicorn's speed

## 📊 Worker Configuration

### Formula for Optimal Workers

```
workers = (2 x CPU_cores) + 1
```

**Examples:**
- 2 CPU cores → 5 workers
- 4 CPU cores → 9 workers
- 8 CPU cores → 17 workers

### Configuration Options

#### Option 1: Environment Variable (Recommended)

```bash
# Set number of workers
export GUNICORN_WORKERS=9

# Start service
docker-compose up -d
```

#### Option 2: .env File

```bash
# Create .env file
cat > .env << EOF
GUNICORN_WORKERS=9
LOG_LEVEL=info
EOF

docker-compose up -d
```

#### Option 3: Inline with Docker Compose

```bash
GUNICORN_WORKERS=9 docker-compose up -d
```

## 🔧 Performance Tuning

### Gunicorn Configuration

The service uses `web/gunicorn.conf.py` with these defaults:

```python
workers = (CPU_count * 2) + 1  # Auto-calculated
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
timeout = 120  # For long-running report generation
max_requests = 1000  # Restart workers after 1000 requests
keepalive = 5
```

### Custom Configuration

Create a custom `gunicorn.conf.py`:

```python
# web/gunicorn.conf.py
import multiprocessing

# Explicit worker count
workers = 8

# Increase timeout for large reports
timeout = 300  # 5 minutes

# More connections per worker
worker_connections = 2000

# Restart workers more frequently to prevent memory leaks
max_requests = 500
max_requests_jitter = 50
```

## 🐋 Docker Deployment Scenarios

### Scenario 1: Small Server (2 CPUs, 2GB RAM)

```yaml
# docker-compose.yml
environment:
  - GUNICORN_WORKERS=3  # Conservative for 2 CPUs

deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 1.5G
    reservations:
      cpus: '0.5'
      memory: 512M
```

### Scenario 2: Medium Server (4 CPUs, 8GB RAM)

```yaml
# docker-compose.yml
environment:
  - GUNICORN_WORKERS=9  # Optimal for 4 CPUs

deploy:
  resources:
    limits:
      cpus: '4.0'
      memory: 4G
    reservations:
      cpus: '2.0'
      memory: 2G
```

### Scenario 3: Large Server (8+ CPUs, 16GB+ RAM)

```yaml
# docker-compose.yml
environment:
  - GUNICORN_WORKERS=17  # For 8 CPUs

deploy:
  resources:
    limits:
      cpus: '8.0'
      memory: 8G
    reservations:
      cpus: '4.0'
      memory: 4G
```

## 📈 Load Testing

### Calculate Optimal Workers

```bash
# Check CPU count
nproc

# Calculate workers
echo $(( $(nproc) * 2 + 1 ))

# Set and start
export GUNICORN_WORKERS=$(( $(nproc) * 2 + 1 ))
docker-compose up -d
```

### Monitor Performance

```bash
# Watch resource usage
docker stats jira-analyzer-jira-analyzer-1

# View worker logs
docker-compose logs -f | grep "Worker spawned"

# Check worker count
docker-compose exec jira-analyzer ps aux | grep gunicorn
```

### Load Testing Tools

```bash
# Using Apache Bench
ab -n 1000 -c 10 http://localhost:8000/api/health

# Using wrk
wrk -t12 -c400 -d30s http://localhost:8000/api/health

# Using hey
hey -n 1000 -c 50 http://localhost:8000/api/health
```

## 🔐 Production Setup with Secrets

### Complete Production Deployment

```bash
# 1. Create secrets directory
mkdir -p secrets
chmod 700 secrets

# 2. Create secret files
echo "https://your-company.atlassian.net" > secrets/jira_url.txt
echo "your-email@company.com" > secrets/jira_email.txt
echo "your_api_token" > secrets/jira_api_token.txt

# 3. Secure secrets
chmod 600 secrets/*.txt

# 4. Configure workers for your server
export GUNICORN_WORKERS=$(( $(nproc) * 2 + 1 ))
export LOG_LEVEL=warning  # Less verbose in production

# 5. Build and start
docker-compose build --no-cache
docker-compose up -d

# 6. Verify deployment
curl http://localhost:8000/api/health
docker-compose logs --tail=50
```

## 🎯 Advanced Configurations

### Using Docker Swarm (High Availability)

```bash
# Initialize swarm
docker swarm init

# Create secrets in swarm
docker secret create jira_url secrets/jira_url.txt
docker secret create jira_email secrets/jira_email.txt
docker secret create jira_api_token secrets/jira_api_token.txt

# Deploy with replicas
docker stack deploy -c docker-compose.yml jira-analyzer

# Scale service
docker service scale jira-analyzer_jira-analyzer=3
```

### Using Kubernetes

Create `k8s-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: jira-analyzer
spec:
  replicas: 3
  selector:
    matchLabels:
      app: jira-analyzer
  template:
    metadata:
      labels:
        app: jira-analyzer
    spec:
      containers:
      - name: jira-analyzer
        image: jira-analyzer:latest
        ports:
        - containerPort: 8000
        env:
        - name: GUNICORN_WORKERS
          value: "9"
        - name: JIRA_URL
          valueFrom:
            secretKeyRef:
              name: jira-secrets
              key: url
        - name: JIRA_EMAIL
          valueFrom:
            secretKeyRef:
              name: jira-secrets
              key: email
        - name: JIRA_API_TOKEN
          valueFrom:
            secretKeyRef:
              name: jira-secrets
              key: token
        resources:
          limits:
            cpu: "2000m"
            memory: "2Gi"
          requests:
            cpu: "1000m"
            memory: "1Gi"
```

### Nginx Reverse Proxy

```nginx
# /etc/nginx/sites-available/jira-analyzer
upstream jira_analyzer {
    server localhost:8000;
}

server {
    listen 80;
    server_name analyzer.example.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name analyzer.example.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Proxy settings
    location / {
        proxy_pass http://jira_analyzer;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts for long-running report generation
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
        proxy_read_timeout 300;
        send_timeout 300;
    }

    # Static files (if served separately)
    location /static/ {
        alias /path/to/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

## 📊 Monitoring

### Health Checks

```bash
# Basic health check
curl http://localhost:8000/api/health

# Detailed monitoring
watch -n 5 'curl -s http://localhost:8000/api/health | jq'
```

### Logging

```bash
# Follow all logs
docker-compose logs -f

# Follow specific service
docker-compose logs -f jira-analyzer

# View worker activity
docker-compose logs -f | grep "Worker"

# View errors only
docker-compose logs -f | grep "ERROR"
```

### Metrics with Prometheus (Optional)

Add to `web/app.py`:

```python
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()

# Add Prometheus metrics
Instrumentator().instrument(app).expose(app)
```

Then scrape metrics at: `http://localhost:8000/metrics`

## 🔄 Graceful Deployment Updates

### Zero-Downtime Updates

```bash
# Build new image
docker-compose build

# Graceful reload
docker-compose up -d --no-deps --build jira-analyzer

# Verify new workers started
docker-compose logs --tail=20 | grep "Worker spawned"
```

### Rollback

```bash
# View available images
docker images jira-scrapper-jira-analyzer

# Tag current as backup
docker tag jira-scrapper-jira-analyzer:latest jira-scrapper-jira-analyzer:backup

# Rollback to previous
docker-compose down
docker tag jira-scrapper-jira-analyzer:backup jira-scrapper-jira-analyzer:latest
docker-compose up -d
```

## 🛡️ Security Hardening

### Additional Security Measures

```yaml
# docker-compose.yml
services:
  jira-analyzer:
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
    read_only: true
    tmpfs:
      - /tmp
      - /app/data/cache:uid=1000,gid=1000
      - /app/data/reports:uid=1000,gid=1000
```

### Rate Limiting with Nginx

```nginx
# /etc/nginx/nginx.conf
http {
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

    server {
        location /api/ {
            limit_req zone=api_limit burst=20 nodelay;
            proxy_pass http://jira_analyzer;
        }
    }
}
```

## 📝 Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `GUNICORN_WORKERS` | `(CPU * 2) + 1` | Number of worker processes |
| `LOG_LEVEL` | `info` | Logging level (debug, info, warning, error) |
| `JIRA_URL` | Required | Jira instance URL |
| `JIRA_EMAIL` | Required (Cloud) | Email for Jira Cloud |
| `JIRA_API_TOKEN` | Required (Cloud) | API token for Jira Cloud |
| `JIRA_USERNAME` | Required (On-Prem) | Username for Jira On-Premise |
| `JIRA_PASSWORD` | Required (On-Prem) | Password for Jira On-Premise |

## 🆘 Troubleshooting

### High CPU Usage

```bash
# Reduce workers
export GUNICORN_WORKERS=3
docker-compose up -d

# Check if too many concurrent reports
docker-compose exec jira-analyzer ps aux
```

### High Memory Usage

```bash
# Reduce max_requests (restart workers more often)
# Edit web/gunicorn.conf.py:
max_requests = 500  # Instead of 1000

# Rebuild
docker-compose build --no-cache
docker-compose up -d
```

### Workers Timing Out

```bash
# Increase timeout
# Edit web/gunicorn.conf.py:
timeout = 300  # 5 minutes instead of 2

# Rebuild
docker-compose build --no-cache
docker-compose up -d
```

### Connection Refused

```bash
# Check if service is running
docker-compose ps

# Check logs
docker-compose logs --tail=50

# Verify port binding
netstat -tlnp | grep 8000

# Test inside container
docker-compose exec jira-analyzer curl http://localhost:8000/api/health
```

## 🎓 Best Practices

1. **Always use Gunicorn + Uvicorn in production** (not standalone Uvicorn)
2. **Set workers based on CPU cores**: `(cores * 2) + 1`
3. **Use Docker secrets** for credentials in production
4. **Enable health checks** for automatic recovery
5. **Monitor resource usage** and adjust limits accordingly
6. **Use reverse proxy** (Nginx/Traefik) for SSL and load balancing
7. **Implement log aggregation** (ELK stack, CloudWatch, etc.)
8. **Regular backups** of data volumes
9. **Test deployments** in staging before production
10. **Document your configuration** for team reference

## 📞 Support

For production deployment issues:
1. Check logs: `docker-compose logs -f`
2. Verify configuration: `docker-compose config`
3. Test health endpoint: `curl http://localhost:8000/api/health`
4. Review this guide's troubleshooting section
5. Open an issue on GitHub with logs and configuration
