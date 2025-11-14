# Docker Setup Guide for Jira Flow Analyzer

This guide explains how to run the Jira Flow Analyzer as a Dockerized web service with secure secret management.

## 🚀 Quick Start

### Option 1: Using Environment Variables (.env file)

1. **Create a `.env` file** in the project root:

```bash
# Copy the example file
cp .env.example .env

# Edit with your credentials
nano .env
```

2. **Start the service:**

```bash
docker-compose up -d
```

3. **Access the web interface:**

Open your browser to: http://localhost:8000

### Option 2: Using Docker Secrets (Recommended for Production)

Docker secrets provide a more secure way to handle sensitive information.

## 🔐 Setting Up Docker Secrets

### Step 1: Create Secrets Directory

```bash
mkdir -p secrets
chmod 700 secrets
```

### Step 2: Create Secret Files

Create individual files for each secret:

```bash
# For Jira Cloud
echo "https://your-company.atlassian.net" > secrets/jira_url.txt
echo "your-email@company.com" > secrets/jira_email.txt
echo "your_api_token_here" > secrets/jira_api_token.txt

# For Jira On-Premise (alternative to Cloud)
echo "http://jira.your-company.com" > secrets/jira_url.txt
echo "your_username" > secrets/jira_username.txt
echo "your_password" > secrets/jira_password.txt
```

### Step 3: Secure the Secrets

```bash
# Set restrictive permissions
chmod 600 secrets/*.txt

# Verify permissions
ls -la secrets/
```

### Step 4: Update Application to Read Secrets

The application automatically looks for secrets in `/run/secrets/` when using Docker Swarm, or falls back to environment variables.

Modify `web/app.py` if needed to add secret reading logic:

```python
import os

def get_secret(secret_name, default=None):
    """Read secret from Docker secret or environment variable."""
    secret_path = f'/run/secrets/{secret_name}'
    if os.path.exists(secret_path):
        with open(secret_path, 'r') as f:
            return f.read().strip()
    return os.getenv(secret_name.upper(), default)

# Usage
jira_url = get_secret('jira_url', os.getenv('JIRA_URL'))
```

## 🐋 Running with Docker Compose

### Basic Setup (with .env)

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### With Custom Environment

```bash
# Set variables inline
JIRA_URL=https://your.atlassian.net docker-compose up -d
```

## 🔄 Running with Docker Swarm (Production)

For production deployments with true Docker secrets:

### Initialize Swarm

```bash
docker swarm init
```

### Create Secrets in Swarm

```bash
# Create secrets from files
docker secret create jira_url secrets/jira_url.txt
docker secret create jira_email secrets/jira_email.txt
docker secret create jira_api_token secrets/jira_api_token.txt
docker secret create jira_username secrets/jira_username.txt
docker secret create jira_password secrets/jira_password.txt

# List secrets
docker secret ls
```

### Deploy as Stack

```bash
# Deploy the stack
docker stack deploy -c docker-compose.yml jira-analyzer

# Check status
docker stack services jira-analyzer

# View logs
docker service logs -f jira-analyzer_jira-analyzer

# Remove stack
docker stack rm jira-analyzer
```

## 📝 Configuration Options

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `JIRA_URL` | Jira instance URL | Yes |
| `JIRA_EMAIL` | Email for Cloud authentication | Cloud only |
| `JIRA_API_TOKEN` | API token for Cloud | Cloud only |
| `JIRA_USERNAME` | Username for On-Premise | On-Premise only |
| `JIRA_PASSWORD` | Password for On-Premise | On-Premise only |

### Docker Secrets (Swarm Mode)

Same as environment variables above, but stored as Docker secrets:

- `jira_url`
- `jira_email`
- `jira_api_token`
- `jira_username`
- `jira_password`

## 🗂️ Data Persistence

The application stores data in two directories:

- `/app/data/cache` - Cached Jira data
- `/app/data/reports` - Generated HTML reports

These are mounted as volumes in `docker-compose.yml`:

```yaml
volumes:
  - ./data/cache:/app/data/cache
  - ./data/reports:/app/data/reports
```

## 🔍 Health Checks

The service includes a health check endpoint:

```bash
# Check service health
curl http://localhost:8000/api/health

# Expected response
{
  "status": "healthy",
  "timestamp": "2025-01-14T10:30:00",
  "jira_url": "https://your.atlassian.net"
}
```

## 🛠️ Troubleshooting

### Service Won't Start

```bash
# Check logs
docker-compose logs jira-analyzer

# Common issues:
# 1. Missing secrets - ensure all secret files exist
# 2. Permission denied - check file permissions (chmod 600)
# 3. Port conflict - ensure port 8000 is available
```

### Cannot Connect to Jira

```bash
# Verify credentials
docker-compose exec jira-analyzer env | grep JIRA

# Test Jira connection
docker-compose exec jira-analyzer python -c "
from jira_analyzer import JiraFetcher
fetcher = JiraFetcher()
print('Connection successful!')
"
```

### Secrets Not Working

```bash
# In Swarm mode, verify secrets are mounted
docker-compose exec jira-analyzer ls -la /run/secrets/

# Check secret permissions
docker-compose exec jira-analyzer cat /run/secrets/jira_url
```

## 🔒 Security Best Practices

1. **Never commit secrets to Git:**
   ```bash
   # Add to .gitignore
   echo "secrets/" >> .gitignore
   echo ".env" >> .gitignore
   ```

2. **Use Docker Swarm secrets for production:**
   - Secrets are encrypted at rest
   - Only available to authorized services
   - Automatically removed when service stops

3. **Rotate credentials regularly:**
   ```bash
   # Update secret
   docker secret rm jira_api_token
   docker secret create jira_api_token new_token.txt

   # Force service update
   docker service update --secret-rm jira_api_token \
     --secret-add jira_api_token jira-analyzer_jira-analyzer
   ```

4. **Use read-only file systems where possible:**
   ```yaml
   services:
     jira-analyzer:
       read_only: true
       tmpfs:
         - /tmp
   ```

## 📊 API Endpoints

Once running, the service provides these endpoints:

- `GET /` - Web UI
- `GET /api/health` - Health check
- `POST /api/reports/generate` - Generate new report
- `GET /api/reports/status/{id}` - Check report status
- `GET /api/reports/list` - List all reports
- `GET /api/reports/view/{id}/{filename}` - View report
- `GET /api/reports/download/{filename}` - Download report

## 🔗 Additional Resources

- [Docker Secrets Documentation](https://docs.docker.com/engine/swarm/secrets/)
- [Docker Compose Secrets](https://docs.docker.com/compose/use-secrets/)
- [Jira API Documentation](https://developer.atlassian.com/cloud/jira/platform/rest/v3/)

## 📞 Support

For issues or questions:
1. Check the logs: `docker-compose logs -f`
2. Review the troubleshooting section above
3. Open an issue on GitHub
