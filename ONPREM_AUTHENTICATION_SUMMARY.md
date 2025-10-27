# On-Premise Authentication Implementation Summary

## Overview

Successfully updated the Jira Scraper to support both **Jira Cloud** (API token) and **Jira On-Premise** (username/password) authentication, with full compatibility for Xray test management on both platforms.

## Changes Made

### 1. Updated `scraper.py` - JiraScraper Class

#### New Authentication Parameters

Added support for both authentication methods:

```python
JiraScraper(
    jira_url=None,           # Required: Jira instance URL
    # Cloud authentication
    jira_email=None,         # For Cloud: user email
    jira_api_token=None,     # For Cloud: API token
    # On-Premise authentication
    jira_username=None,      # For On-Prem: username
    jira_password=None,      # For On-Prem: password
    # Auto-detection
    auth_method="auto",      # "auto", "token", or "password"
    ...
)
```

#### Auto-Detection Logic

The scraper automatically detects the authentication method:

1. Checks for `JIRA_EMAIL` + `JIRA_API_TOKEN` → Uses **token** auth (Cloud)
2. Checks for `JIRA_USERNAME` + `JIRA_PASSWORD` → Uses **password** auth (On-Premise)
3. If `auth_method` is set explicitly, uses that method
4. Raises clear error if credentials are missing

#### Environment Variables

**Cloud (.env):**
```bash
JIRA_URL=https://company.atlassian.net
JIRA_EMAIL=user@company.com
JIRA_API_TOKEN=ATATT3xFf...
```

**On-Premise (.env):**
```bash
JIRA_URL=http://jira.company.com
JIRA_USERNAME=username
JIRA_PASSWORD=password
```

#### Client Connection

Updated `client` property to use appropriate authentication:

```python
@property
def client(self) -> JIRA:
    if self.auth_method == "token":
        # Cloud: email + API token
        self._jira_client = JIRA(
            server=self.jira_url,
            basic_auth=(self.jira_email, self.jira_api_token),
        )
    else:
        # On-Premise: username + password
        self._jira_client = JIRA(
            server=self.jira_url,
            basic_auth=(self.jira_username, self.jira_password),
        )
```

### 2. Enhanced Xray Support - On-Premise Compatibility

#### New Method: `_extract_xray_fields()`

Added Xray-specific field extraction for On-Premise:

```python
def _extract_xray_fields(self, issue) -> Dict[str, Any]:
    """Extract Xray-specific fields (On-Premise compatible)."""
    xray_data = {
        "is_test_execution": False,
        "test_execution_status": None,
        "test_plan": None,
        "test_environments": [],
        "test_count": 0,
    }
    # ... extraction logic
    return xray_data
```

This method:
- Detects if issue is a Test Execution
- Extracts test execution status from workflow
- Finds Test Plan references
- Identifies test environments
- Works with custom field configurations

#### Updated `_extract_ticket_data()`

Now includes Xray data:

```python
ticket["xray_data"] = self._extract_xray_fields(issue)
```

### 3. Updated `xray_test_chart.py` - XrayTestChart Class

#### Extended Status Mapping

Added comprehensive status mapping for On-Premise:

```python
XRAY_STATUSES = {
    # Cloud API statuses
    "PASS": "Passed",
    "FAIL": "Failed",
    "EXECUTING": "Executing",
    "TODO": "To Do",
    "ABORTED": "Aborted",

    # On-Premise workflow statuses
    "Passed": "Passed",
    "Failed": "Failed",
    "In Progress": "Executing",
    "To Do": "To Do",
    "Open": "To Do",
    "Blocked": "Aborted",
    "Done": "Passed",
    "Closed": "Passed",
    "Unexecuted": "To Do",
    # ... and more variations
}
```

#### Smart Status Detection

Enhanced `calculate_test_metrics()` with multi-source status detection:

1. **Check Xray-specific data** (from On-Premise extraction)
   ```python
   xray_data = execution.get("xray_data", {})
   if xray_data and xray_data.get("is_test_execution"):
       status = xray_data.get("test_execution_status")
   ```

2. **Fallback to main status field**
   ```python
   if not status:
       status = execution.get("status", "To Do")
   ```

3. **Normalize using mapping**
   ```python
   normalized_status = self.XRAY_STATUSES.get(status, "To Do")
   ```

4. **Heuristic detection** for custom statuses
   ```python
   if "pass" in status_lower or "success" in status_lower:
       normalized_status = "Passed"
   elif "fail" in status_lower or "error" in status_lower:
       normalized_status = "Failed"
   # ... etc
   ```

### 4. Configuration Files

#### Created `.env.example`

Comprehensive example configuration file with:
- Cloud authentication example
- On-Premise authentication example
- Comments explaining each option
- Security notes

#### Created `AUTHENTICATION_GUIDE.md`

Detailed authentication guide covering:
- Quick start for both platforms
- Step-by-step setup for Cloud
- Step-by-step setup for On-Premise
- Auto-detection explanation
- Xray integration details
- Configuration examples
- Troubleshooting section
- Security best practices

### 5. Updated Documentation

#### Updated `README.md`

- Added dual authentication support section
- Linked to comprehensive authentication guide
- Explained auto-detection

## Key Features

### ✅ Dual Authentication Support

- **Jira Cloud**: API token authentication (email + token)
- **Jira On-Premise**: Username/password authentication
- **Auto-detection**: Automatically selects correct method
- **Manual override**: Can force specific auth method

### ✅ Xray On-Premise Compatibility

- **Status mapping**: Handles both Cloud API and On-Premise workflow statuses
- **Custom workflows**: Smart detection for custom status names
- **Custom fields**: Extracts Xray-specific fields from custom field IDs
- **Test Plans**: Detects and extracts Test Plan references
- **Environments**: Extracts test environment information

### ✅ Backward Compatibility

- **Existing code**: Works without changes for Cloud users
- **Environment variables**: Supports both old and new variable names
- **Default behavior**: Auto-detection doesn't break existing setups

### ✅ Security

- **Environment variables**: Credentials stored securely in `.env`
- **No hardcoding**: No credentials in code
- **Clear errors**: Helpful messages for missing credentials
- **Best practices**: Documentation includes security guidance

## Usage Examples

### Example 1: Cloud with Auto-Detection

```python
from jira_scraper import JiraScraper

# .env contains:
# JIRA_URL=https://company.atlassian.net
# JIRA_EMAIL=user@company.com
# JIRA_API_TOKEN=token123

scraper = JiraScraper()  # Auto-detects Cloud
# Output: "Auto-detected: Using API token authentication (Jira Cloud)"

tickets = scraper.get_project_tickets("PROJ")
```

### Example 2: On-Premise with Auto-Detection

```python
from jira_scraper import JiraScraper

# .env contains:
# JIRA_URL=http://jira.company.com
# JIRA_USERNAME=johndoe
# JIRA_PASSWORD=mypassword

scraper = JiraScraper()  # Auto-detects On-Premise
# Output: "Auto-detected: Using username/password authentication (Jira On-Premise)"

tickets = scraper.get_project_tickets("PROJ")
```

### Example 3: Explicit Authentication Method

```python
from jira_scraper import JiraScraper

# Force password authentication
scraper = JiraScraper(
    jira_url="http://jira.company.com",
    jira_username="username",
    jira_password="password",
    auth_method="password"
)
```

### Example 4: Xray Test Executions (Works for Both!)

```python
from jira_scraper import JiraScraper, XrayTestChart

# Works for both Cloud and On-Premise
scraper = JiraScraper()
tickets = scraper.get_project_tickets("PROJ", "2024-01-01", "2024-10-23")

# Extract test executions
test_executions = [t for t in tickets if t['issue_type'] == 'Test Execution']

# Create Xray chart (handles both Cloud and On-Premise statuses)
xray_chart = XrayTestChart(test_executions, target_label="release-1.0")
metrics = xray_chart.calculate_test_metrics()

print(f"Total tests: {metrics['total_tests']}")
print(f"Coverage: {metrics['coverage_percent']}%")
```

## Migration Guide

### For Existing Cloud Users

No changes needed! Your existing configuration continues to work:

```bash
# Old .env (still works)
JIRA_URL=https://company.atlassian.net
JIRA_EMAIL=user@company.com
JIRA_API_TOKEN=token
```

### For New On-Premise Users

Create `.env` with On-Premise credentials:

```bash
# New .env for On-Premise
JIRA_URL=http://jira.company.com
JIRA_USERNAME=username
JIRA_PASSWORD=password
```

## Testing

### Test Cloud Connection

```python
from jira_scraper import JiraScraper

scraper = JiraScraper(
    jira_url="https://company.atlassian.net",
    jira_email="user@company.com",
    jira_api_token="token",
    auth_method="token"
)

if scraper.test_connection():
    print("✓ Cloud connection successful")
```

### Test On-Premise Connection

```python
from jira_scraper import JiraScraper

scraper = JiraScraper(
    jira_url="http://jira.company.com",
    jira_username="username",
    jira_password="password",
    auth_method="password"
)

if scraper.test_connection():
    print("✓ On-Premise connection successful")
```

## Xray Status Compatibility

### Cloud Statuses (API)
- PASS → Passed
- FAIL → Failed
- EXECUTING → Executing
- TODO → To Do
- ABORTED → Aborted

### On-Premise Statuses (Workflow)
- Passed, PASSED, Done, Closed → Passed
- Failed, FAILED → Failed
- In Progress, Executing → Executing
- To Do, TODO, Open, Unexecuted → To Do
- Aborted, ABORTED, Blocked → Aborted

### Custom Status Detection
If a status doesn't match the above, the system uses heuristics:
- Contains "pass", "success", "done" → Passed
- Contains "fail", "error" → Failed
- Contains "progress", "executing", "running" → Executing
- Contains "abort", "block", "cancel" → Aborted
- Default → To Do

## Files Modified/Created

### Modified Files
1. **`src/jira_scraper/scraper.py`**
   - Added username/password authentication
   - Added auto-detection logic
   - Added Xray field extraction for On-Premise

2. **`src/jira_scraper/xray_test_chart.py`**
   - Extended status mapping for On-Premise
   - Enhanced status detection logic
   - Added heuristic status inference

3. **`README.md`**
   - Added authentication methods section
   - Linked to authentication guide

### New Files
1. **`.env.example`** - Configuration template
2. **`AUTHENTICATION_GUIDE.md`** - Comprehensive auth documentation
3. **`ONPREM_AUTHENTICATION_SUMMARY.md`** - This file

## Security Considerations

1. **Never commit `.env` to git**
   ```bash
   # .gitignore should contain:
   .env
   ```

2. **Use HTTPS for production** (On-Premise)
   ```bash
   JIRA_URL=https://jira.company.com  # Not http://
   ```

3. **Rotate credentials regularly**
   - Cloud: Regenerate API tokens periodically
   - On-Premise: Change passwords per security policy

4. **Use service accounts**
   - Create dedicated accounts for automation
   - Grant minimal required permissions

## Troubleshooting

### "401 Unauthorized"
- **Cloud**: Check email and API token
- **On-Premise**: Verify username (not email) and password

### "Auto-detection failed"
- Set `auth_method` explicitly
- Check environment variables are set correctly

### "No test executions found"
- Verify issue type is "Test Execution" or "Test"
- Check Xray is installed and configured

### "Custom statuses not recognized"
- Add custom status mapping in `XRAY_STATUSES`
- Or rely on heuristic detection

## Next Steps

1. **Set up authentication** using [AUTHENTICATION_GUIDE.md](AUTHENTICATION_GUIDE.md)
2. **Test connection** with your Jira instance
3. **Fetch test executions** and verify Xray integration
4. **Generate reports** with new charts

## Support

- **Authentication Issues**: See [AUTHENTICATION_GUIDE.md](AUTHENTICATION_GUIDE.md)
- **Chart Features**: See [NEW_CHARTS_DOCUMENTATION.md](NEW_CHARTS_DOCUMENTATION.md)
- **Quick Start**: See [QUICK_START_NEW_CHARTS.md](QUICK_START_NEW_CHARTS.md)
