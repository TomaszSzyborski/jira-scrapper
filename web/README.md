# Jira Flow Analyzer - Web Service

A FastAPI-based web service for generating and serving Jira flow analysis reports on demand.

## Features

- 🌐 Web-based UI with navy blue theme
- 📊 Generate reports for different issue types (Bug, Story, Task, etc.)
- 🔄 Real-time report generation with progress tracking
- 💾 Automatic caching of Jira data
- 📥 Download and view generated reports
- 🔐 Secure credential management via Docker secrets
- 🚀 RESTful API for programmatic access

## Quick Start

### Using Docker (Recommended)

```bash
# 1. Set up credentials
mkdir -p secrets
echo "https://your-company.atlassian.net" > secrets/jira_url.txt
echo "your-email@company.com" > secrets/jira_email.txt
echo "your_api_token" > secrets/jira_api_token.txt

# 2. Start the service
docker-compose up -d

# 3. Access the UI
open http://localhost:8000
```

### Running Locally

```bash
# 1. Install dependencies
pip install -r ../requirements.txt

# 2. Set environment variables
export JIRA_URL="https://your-company.atlassian.net"
export JIRA_EMAIL="your-email@company.com"
export JIRA_API_TOKEN="your_token"

# 3. Start the server
python app.py

# 4. Access the UI
open http://localhost:8000
```

## API Endpoints

### Health Check
```bash
GET /api/health
```

### Generate Report
```bash
POST /api/reports/generate
Content-Type: application/json

{
  "project": "PROJ",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "label": "Sprint-1",
  "issue_types": ["Bug", "Story"],
  "force_fetch": false
}
```

### Check Report Status
```bash
GET /api/reports/status/{report_id}
```

### List All Reports
```bash
GET /api/reports/list
```

### View Report
```bash
GET /api/reports/view/{report_id}/{filename}
```

### Download Report
```bash
GET /api/reports/download/{filename}
```

## Directory Structure

```
web/
├── app.py              # FastAPI application
├── static/             # Static files (CSS, JS, images)
├── templates/          # Jinja2 templates
│   └── index.html     # Main UI page
└── README.md          # This file
```

## Configuration

### Environment Variables

- `JIRA_URL` - Jira instance URL (required)
- `JIRA_EMAIL` - Email for Jira Cloud (Cloud only)
- `JIRA_API_TOKEN` - API token for Jira Cloud (Cloud only)
- `JIRA_USERNAME` - Username for Jira On-Premise (On-Premise only)
- `JIRA_PASSWORD` - Password for Jira On-Premise (On-Premise only)

### Docker Secrets

When using Docker, credentials can be provided as secrets:

```bash
docker secret create jira_url secrets/jira_url.txt
docker secret create jira_email secrets/jira_email.txt
docker secret create jira_api_token secrets/jira_api_token.txt
```

See [DOCKER_SETUP.md](../DOCKER_SETUP.md) for detailed instructions.

## Usage Examples

### Generate Bug Report

1. Open http://localhost:8000
2. Enter project key (e.g., "PROJ")
3. Leave issue types empty (defaults to Bug)
4. Click "Generate Report"
5. Wait for completion and view report

### Generate Story Report

1. Open http://localhost:8000
2. Enter project key
3. Enter "Story" in issue types
4. Click "Generate Report"

### Generate Multi-Type Report

1. Open http://localhost:8000
2. Enter project key
3. Enter "Bug, Story, Task" in issue types
4. Click "Generate Report"

### Generate with Date Range

1. Open http://localhost:8000
2. Enter project key
3. Select start and end dates
4. Click "Generate Report"

## Development

### Running in Development Mode

```bash
# With auto-reload
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### Testing the API

```bash
# Health check
curl http://localhost:8000/api/health

# Generate report
curl -X POST http://localhost:8000/api/reports/generate \
  -H "Content-Type: application/json" \
  -d '{
    "project": "PROJ",
    "issue_types": ["Bug"]
  }'

# List reports
curl http://localhost:8000/api/reports/list
```

## Troubleshooting

### Service Won't Start

- Check if port 8000 is already in use
- Verify environment variables are set correctly
- Check Docker logs: `docker-compose logs -f`

### Cannot Connect to Jira

- Verify JIRA_URL is correct
- Check credentials are valid
- Ensure network connectivity to Jira instance

### Reports Not Generating

- Check application logs for errors
- Verify project key exists in Jira
- Ensure sufficient permissions for API user

## Performance Tips

- Use caching (avoid `force_fetch` unless necessary)
- Filter by date range to reduce data size
- Use specific issue types instead of fetching all

## Security Notes

- Never commit secrets to Git
- Use Docker secrets in production
- Rotate API tokens regularly
- Use read-only Jira API tokens when possible

## License

Same as main project.
