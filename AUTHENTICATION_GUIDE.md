# Authentication Guide - Jira Cloud and On-Premise

This guide explains how to authenticate with both Jira Cloud and Jira On-Premise (Server/Data Center) instances, with full support for Xray test management.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Jira Cloud Authentication (API Token)](#jira-cloud-authentication)
3. [Jira On-Premise Authentication (Username/Password)](#jira-on-premise-authentication)
4. [Auto-Detection](#auto-detection)
5. [Xray Integration](#xray-integration)
6. [Configuration Examples](#configuration-examples)
7. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Option 1: Environment Variables (Recommended)

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your credentials (see sections below)

3. The scraper will auto-detect your authentication method

### Option 2: Direct Parameters

```python
from jira_scraper import JiraScraper

# Cloud
scraper = JiraScraper(
    jira_url="https://your-company.atlassian.net",
    jira_email="your-email@company.com",
    jira_api_token="your_api_token",
    auth_method="token"
)

# On-Premise
scraper = JiraScraper(
    jira_url="http://jira.your-company.com",
    jira_username="your_username",
    jira_password="your_password",
    auth_method="password"
)
```

---

## Jira Cloud Authentication

### For Atlassian Cloud (*.atlassian.net)

#### 1. Generate API Token

1. Go to https://id.atlassian.com/manage/api-tokens
2. Click **"Create API token"**
3. Give it a name (e.g., "Jira Scraper")
4. Copy the token (you won't be able to see it again!)

#### 2. Configure Environment Variables

Edit your `.env` file:

```bash
JIRA_URL=https://your-company.atlassian.net
JIRA_EMAIL=your-email@company.com
JIRA_API_TOKEN=YourAPITokenHere123456
```

#### 3. Usage

```python
from jira_scraper import JiraScraper

# Auto-detect (recommended)
scraper = JiraScraper()

# Or explicitly specify
scraper = JiraScraper(auth_method="token")

# Test connection
if scraper.test_connection():
    print("Connected successfully!")
```

### Important Notes

- **Email**: Must be the email address associated with your Atlassian account
- **API Token**: Not your password! Generate a specific API token
- **URL Format**: Must include https:// and end with .atlassian.net
- **Token Security**: Never commit tokens to version control

---

## Jira On-Premise Authentication

### For Jira Server/Data Center (Self-Hosted)

#### 1. Get Your Credentials

You'll need:
- Your Jira username (not email)
- Your Jira password
- Your Jira server URL

#### 2. Configure Environment Variables

Edit your `.env` file:

```bash
JIRA_URL=http://jira.your-company.com
JIRA_USERNAME=your_username
JIRA_PASSWORD=your_password
```

Or for HTTPS:

```bash
JIRA_URL=https://jira.your-company.com
JIRA_USERNAME=your_username
JIRA_PASSWORD=your_password
```

#### 3. Usage

```python
from jira_scraper import JiraScraper

# Auto-detect (recommended)
scraper = JiraScraper()

# Or explicitly specify
scraper = JiraScraper(auth_method="password")

# Test connection
if scraper.test_connection():
    print("Connected successfully!")
```

### Important Notes

- **Username**: Your Jira login username, not email
- **Password**: Your actual Jira password
- **URL Format**: Include http:// or https://
- **Port**: Include if non-standard (e.g., http://jira.company.com:8080)
- **Security**: Use HTTPS in production, never commit passwords to git

---

## Auto-Detection

The scraper automatically detects which authentication method to use:

### Detection Logic

1. If `JIRA_EMAIL` and `JIRA_API_TOKEN` are set → Uses **API Token** (Cloud)
2. If `JIRA_USERNAME` and `JIRA_PASSWORD` are set → Uses **Username/Password** (On-Premise)
3. If both are set → Prefers API Token
4. If neither → Raises error

### Example

```python
from jira_scraper import JiraScraper

# Just initialize - it will auto-detect
scraper = JiraScraper()
# Output: "Auto-detected: Using username/password authentication (Jira On-Premise)"
```

### Override Auto-Detection

```python
# Force token authentication
scraper = JiraScraper(auth_method="token")

# Force password authentication
scraper = JiraScraper(auth_method="password")
```

---

## Xray Integration

### Xray Cloud vs On-Premise

The scraper supports both Xray Cloud and Xray On-Premise:

#### Xray Cloud
- Uses Jira Cloud authentication (API token)
- Test execution statuses: PASS, FAIL, EXECUTING, TODO, ABORTED
- Accessed via Jira REST API

#### Xray On-Premise
- Uses Jira On-Premise authentication (username/password)
- Test execution statuses from workflow (customizable)
- Common statuses: Passed, Failed, In Progress, To Do, Blocked
- Accessed via Jira REST API

### Supported Test Execution Statuses

The `XrayTestChart` module automatically recognizes these statuses:

**Standard Statuses (Both Cloud and On-Premise):**
- Passed / PASS / PASSED / Done / Closed
- Failed / FAIL / FAILED
- Executing / EXECUTING / In Progress
- To Do / TODO / Open / Unexecuted
- Aborted / ABORTED / Blocked

**Custom Statuses:**
The module also uses heuristics to detect custom statuses:
- Contains "pass" or "success" → Mapped to Passed
- Contains "fail" or "error" → Mapped to Failed
- Contains "progress" or "executing" → Mapped to Executing
- Contains "abort" or "block" → Mapped to Aborted

### Fetching Xray Test Executions

```python
from jira_scraper import JiraScraper

# Initialize (works for both Cloud and On-Premise)
scraper = JiraScraper()

# Fetch test executions
test_executions = scraper.get_project_tickets(
    project_key="PROJ",
    start_date="2024-01-01",
    end_date="2024-10-23"
)

# Filter for test execution issue types
tests = [t for t in test_executions if t['issue_type'] in ['Test Execution', 'Test']]

print(f"Found {len(tests)} test executions")
```

### Xray-Specific Fields (On-Premise)

The scraper automatically extracts Xray-specific data:

```python
ticket = scraper._extract_ticket_data(issue)
xray_data = ticket['xray_data']

print(f"Is test execution: {xray_data['is_test_execution']}")
print(f"Test status: {xray_data['test_execution_status']}")
print(f"Test plan: {xray_data['test_plan']}")
print(f"Environments: {xray_data['test_environments']}")
```

---

## Configuration Examples

### Example 1: Jira Cloud with Xray Cloud

```bash
# .env file
JIRA_URL=https://mycompany.atlassian.net
JIRA_EMAIL=john.doe@company.com
JIRA_API_TOKEN=ATATT3xFfGF0abcdef123456
```

```python
from jira_scraper import JiraScraper, XrayTestChart

scraper = JiraScraper()
tickets = scraper.get_project_tickets("PROJ", "2024-01-01", "2024-10-23")

# Xray test charts
test_executions = [t for t in tickets if t['issue_type'] == 'Test Execution']
xray_chart = XrayTestChart(test_executions, target_label="release-1.0")
metrics = xray_chart.calculate_test_metrics()
```

### Example 2: Jira On-Premise with Xray On-Premise

```bash
# .env file
JIRA_URL=http://jira.internal.company.com
JIRA_USERNAME=johndoe
JIRA_PASSWORD=MySecurePassword123
```

```python
from jira_scraper import JiraScraper, XrayTestChart

scraper = JiraScraper()
tickets = scraper.get_project_tickets("PROJ", "2024-01-01", "2024-10-23")

# Xray test charts (same code works for on-premise!)
test_executions = [t for t in tickets if t['issue_type'] == 'Test Execution']
xray_chart = XrayTestChart(test_executions, target_label="release-1.0")
metrics = xray_chart.calculate_test_metrics()
```

### Example 3: Explicit Authentication

```python
from jira_scraper import JiraScraper

# Cloud - explicit
cloud_scraper = JiraScraper(
    jira_url="https://company.atlassian.net",
    jira_email="user@company.com",
    jira_api_token="ATATT...",
    auth_method="token"
)

# On-Premise - explicit
onprem_scraper = JiraScraper(
    jira_url="http://jira.company.com",
    jira_username="username",
    jira_password="password",
    auth_method="password"
)
```

### Example 4: SSL Certificate Verification (On-Premise)

For self-signed certificates:

```python
import os
os.environ['REQUESTS_CA_BUNDLE'] = '/path/to/ca-bundle.crt'

scraper = JiraScraper()
```

Or disable verification (not recommended for production):

```python
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Note: The jira library will need to be configured separately for SSL
```

---

## Troubleshooting

### Common Issues

#### 1. "401 Unauthorized" Error

**Cloud:**
- Check that email matches your Atlassian account
- Verify API token is correct (regenerate if needed)
- Ensure token hasn't expired

**On-Premise:**
- Verify username (not email) is correct
- Check password is correct
- Ensure account is not locked

#### 2. "Connection Refused" or "Timeout"

- Check JIRA_URL is correct
- Verify you can access the URL in your browser
- Check network/firewall settings
- For on-premise, ensure VPN is connected if required

#### 3. "404 Project Not Found"

- Verify project key is correct (case-sensitive)
- Check you have permissions to access the project
- Ensure project exists

#### 4. Auto-Detection Not Working

Set auth_method explicitly:
```python
scraper = JiraScraper(auth_method="password")  # or "token"
```

#### 5. SSL Certificate Errors (On-Premise)

```python
import os
# Point to your certificate bundle
os.environ['REQUESTS_CA_BUNDLE'] = '/path/to/ca-bundle.crt'
```

#### 6. Xray Test Executions Not Found

- Check issue type name (might be "Test" instead of "Test Execution")
- Verify Xray is installed and configured
- Check custom field IDs match your installation

### Testing Your Connection

```python
from jira_scraper import JiraScraper

scraper = JiraScraper()

# Test basic connection
if scraper.test_connection():
    print("✓ Connection successful")

    # Test project access
    try:
        project_info = scraper.get_project_info("PROJ")
        print(f"✓ Project found: {project_info['name']}")
    except Exception as e:
        print(f"✗ Project error: {e}")
else:
    print("✗ Connection failed")
```

### Debug Mode

Enable verbose output:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

scraper = JiraScraper()
```

---

## Security Best Practices

1. **Never commit credentials to version control**
   ```bash
   # Add to .gitignore
   .env
   ```

2. **Use environment variables**
   - Store credentials in `.env` file
   - Keep `.env` out of version control

3. **Use HTTPS when possible**
   - Cloud: Always HTTPS
   - On-Premise: Use HTTPS in production

4. **Rotate credentials regularly**
   - Cloud: Generate new API tokens periodically
   - On-Premise: Change passwords according to policy

5. **Use least-privilege accounts**
   - Create dedicated service accounts
   - Grant only necessary permissions

6. **Secure your .env file**
   ```bash
   chmod 600 .env  # Read/write for owner only
   ```

---

## Next Steps

- See [NEW_CHARTS_DOCUMENTATION.md](NEW_CHARTS_DOCUMENTATION.md) for chart features
- See [QUICK_START_NEW_CHARTS.md](QUICK_START_NEW_CHARTS.md) for quick start guide
- See [README.md](README.md) for general usage

---

## Support

For issues related to:
- **Jira Cloud API**: https://developer.atlassian.com/cloud/jira/platform/rest/v3/
- **Jira On-Premise API**: https://docs.atlassian.com/software/jira/docs/api/REST/latest/
- **Xray On-Premise**: https://docs.getxray.app/display/XRAY/REST+API
- **Xray Cloud**: https://docs.getxray.app/display/XRAYCLOUD/REST+API
