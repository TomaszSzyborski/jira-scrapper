# Test Data - Mock API Responses

This directory contains realistic mock data for testing the Jira, Xray, and Bitbucket analyzers without requiring actual API access.

## Overview

These mock responses represent typical on-premise API responses from:
- **Jira Server/Data Center** - Issue tracking
- **Xray for Jira (On-Premise)** - Test management
- **Bitbucket Server/Data Center** - Code repository

## Files

### Jira API Mock Data

#### `jira_issues_response.json`
Mock response from Jira REST API `/rest/api/2/issue/search` endpoint.

**Contents:**
- 3 issues (PROJ-123, PROJ-124, PROJ-125)
- Issue types: Bug, Story, "Zadanie Dev" (Dev Task)
- Complete issue fields including status, assignee, reporter, labels
- Full changelog history with status transitions
- Timestamps in ISO 8601 format

**Sample Issues:**
- **PROJ-123**: Bug - "Fix login authentication bug" (In Progress)
  - Status transitions: To Do → In Progress → In Review → In Progress
  - 3 changelog entries
  - Labels: authentication, security, production

- **PROJ-124**: Story - "Implement user profile page" (Done)
  - Status transitions: To Do → In Progress → To Test → In Testing → Done
  - 4 changelog entries
  - Labels: frontend, user-experience

- **PROJ-125**: Zadanie Dev - "Database performance optimization" (To Do)
  - No status transitions yet
  - Labels: performance, database, optimization

**API Endpoint Simulated:**
```
GET /rest/api/2/search?jql=project=PROJ&expand=changelog&maxResults=50
```

---

### Xray API Mock Data

#### `xray_test_executions_response.json`
Mock response from Jira REST API for test execution issues.

**Contents:**
- 2 test execution issues (PROJ-201, PROJ-202)
- Custom fields for test plan (customfield_10000) and environments (customfield_10001)
- Complete test execution metadata

**Sample Test Executions:**
- **PROJ-201**: "Sprint 1 - Test Execution" (Done)
  - Test Plan: PROJ-300
  - Environments: Chrome, Firefox
  - Labels: sprint-1, regression

- **PROJ-202**: "API Integration Tests - Execution" (In Progress)
  - Test Plan: PROJ-301
  - Environments: Production, Staging
  - Labels: api, automation

**API Endpoint Simulated:**
```
GET /rest/api/2/search?jql=project=PROJ AND issuetype="Test Execution"
```

#### `xray_test_list_response.json`
Mock response from Xray REST API `/rest/raven/1.0/api/testexec/{execKey}/test` endpoint.

**Contents:**
- List of 5 test keys (PROJ-401 to PROJ-405)
- Represents tests associated with a test execution

**API Endpoint Simulated:**
```
GET /rest/raven/1.0/api/testexec/PROJ-201/test
```

#### `xray_test_run_response.json`
Mock response from Xray REST API `/rest/raven/1.0/api/testrun` endpoint (single test run).

**Contents:**
- Single test run for PROJ-401
- Status: PASS
- Started: 2024-01-15T10:30:00.000Z
- Finished: 2024-01-15T10:32:30.000Z
- Duration: 2 minutes 30 seconds
- 3 test steps (all passed)
- Executed by: qa.tester

**API Endpoint Simulated:**
```
GET /rest/raven/1.0/api/testrun?testExecIssueKey=PROJ-201&testIssueKey=PROJ-401
```

#### `xray_test_runs_multiple.json`
Mock response showing multiple test runs with different statuses.

**Contents:**
- 5 test runs (PROJ-401 to PROJ-405)
- Statuses: 3 PASS, 1 FAIL, 1 TODO
- PROJ-402 has 1 defect (PROJ-500)
- Various execution times
- Realistic comments for each test

**Test Results Summary:**
- Pass Rate: 60% (3/5)
- Fail Rate: 20% (1/5)
- Not Executed: 20% (1/5)
- Total Defects: 1

---

### Bitbucket API Mock Data

#### `bitbucket_commits_response.json`
Mock response from Bitbucket REST API `/rest/api/1.0/projects/{project}/repos/{repo}/commits` endpoint.

**Contents:**
- 5 commits from 4 different authors
- Commit messages with prefixes: Fix, Feature, Refactor, Docs, Test
- Timestamps spanning 5 days (Jan 17-21, 2024)
- Full author and committer information
- Parent commit references

**Sample Commits:**
- **abcdef1**: John Doe - "Fix: Resolve authentication bug" (PROJ-123)
- **bcdef12**: Bob Wilson - "Feature: Add user profile page" (PROJ-124)
- **cdef123**: Jane Smith - "Refactor: Improve database query performance"
- **def1234**: Alice Brown - "Docs: Update API documentation"
- **ef12345**: John Doe - "Test: Add integration tests for auth flow"

**Commit Authors:**
- john.doe@example.com (2 commits)
- bob.wilson@example.com (1 commit)
- jane.smith@example.com (1 commit)
- alice.brown@example.com (1 commit)

**API Endpoint Simulated:**
```
GET /rest/api/1.0/projects/PROJ/repos/my-repo/commits?limit=100
```

#### `bitbucket_pull_requests_response.json`
Mock response from Bitbucket REST API `/rest/api/1.0/projects/{project}/repos/{repo}/pull-requests` endpoint.

**Contents:**
- 3 pull requests (IDs 1, 2, 3)
- States: 2 MERGED, 1 OPEN
- Full reviewer information with approval status
- Detailed descriptions with markdown formatting
- Creation, update, and close timestamps

**Sample Pull Requests:**
- **PR #1**: "Fix authentication bug" (MERGED)
  - Author: John Doe
  - Reviewers: Jane Smith (approved), Bob Wilson (approved)
  - Branch: feature/fix-auth-bug → master
  - Time to merge: ~24 hours

- **PR #2**: "Feature: User profile page implementation" (MERGED)
  - Author: Bob Wilson
  - Reviewers: John Doe (approved), Alice Brown (approved)
  - Branch: feature/user-profile → master
  - Time to merge: ~48 hours

- **PR #3**: "Database performance improvements" (OPEN)
  - Author: Jane Smith
  - Reviewers: John Doe (not approved), Alice Brown (approved)
  - Branch: feature/db-optimization → master
  - Currently awaiting approval

**API Endpoint Simulated:**
```
GET /rest/api/1.0/projects/PROJ/repos/my-repo/pull-requests?state=ALL&limit=100
```

#### `bitbucket_repository_response.json`
Mock response from Bitbucket REST API `/rest/api/1.0/projects/{project}/repos/{repo}` endpoint.

**Contents:**
- Repository metadata (slug, name, description)
- Project information (key, name, type)
- Clone URLs (SSH and HTTPS)
- Repository state and settings

**Repository Details:**
- Slug: my-repo
- Name: My Repository
- Project: PROJ (Project Example)
- State: AVAILABLE
- SCM: git
- Public: false (private repository)

**API Endpoint Simulated:**
```
GET /rest/api/1.0/projects/PROJ/repos/my-repo
```

---

## Using Mock Data for Testing

### Manual Testing

You can use these files to test the analyzer logic without API access:

```python
import json

# Test Jira analyzer
with open('test_data/jira_issues_response.json', 'r') as f:
    mock_data = json.load(f)
    issues = mock_data['issues']
    # Process issues...

# Test Xray analyzer
with open('test_data/xray_test_runs_multiple.json', 'r') as f:
    test_runs = json.load(f)
    # Analyze test runs...

# Test Bitbucket analyzer
with open('test_data/bitbucket_commits_response.json', 'r') as f:
    commits_data = json.load(f)
    commits = commits_data['values']
    # Process commits...
```

### Unit Testing

Create mock HTTP responses using these files:

```python
import json
from unittest.mock import Mock, patch

def test_jira_fetcher():
    with open('test_data/jira_issues_response.json', 'r') as f:
        mock_response = json.load(f)

    with patch('requests.get') as mock_get:
        mock_get.return_value = Mock(
            status_code=200,
            json=lambda: mock_response
        )

        # Test your fetcher
        fetcher = JiraFetcher()
        issues = fetcher.fetch_issues('PROJ')
        assert len(issues) == 3
```

### Integration Testing

Use these files to test the full pipeline without external dependencies:

```bash
# Copy mock data to cache location
cp test_data/jira_issues_response.json data/cache/PROJ_issues.json

# Run analyzer with cached data (no API calls)
python main.py --project PROJ --use-cache
```

---

## Data Relationships

### Cross-Reference Map

The mock data is designed with consistent relationships:

**Jira Issues → Bitbucket Commits:**
- PROJ-123 (Bug) ↔ Commit abcdef1 (Fix: Resolve authentication bug)
- PROJ-124 (Story) ↔ Commit bcdef12 (Feature: Add user profile page)

**Jira Issues → Pull Requests:**
- PROJ-123 ↔ PR #1 (Fix authentication bug)
- PROJ-124 ↔ PR #2 (Feature: User profile page implementation)

**Test Executions → Issues:**
- PROJ-201 (Test Execution) tests functionality from PROJ-123, PROJ-124
- PROJ-402 (Failed Test) found defect PROJ-500

**Users Across Systems:**
- john.doe@example.com - Active in Jira, Bitbucket, Git commits
- bob.wilson@example.com - Active in Jira, Bitbucket, Git commits
- jane.smith@example.com - Active in Jira, Bitbucket, Git commits, Xray
- alice.brown@example.com - Active in Jira, Bitbucket, Git commits

---

## Expected Analytics Results

### Jira Flow Analysis

**Issue Metrics:**
- Total Issues: 3
- Bug: 1 (33%)
- Story: 1 (33%)
- Zadanie Dev: 1 (33%)

**Status Distribution:**
- To Do: 1 (33%)
- In Progress: 1 (33%)
- Done: 1 (33%)

**Average Transitions:**
- PROJ-123: 3 transitions
- PROJ-124: 4 transitions
- PROJ-125: 0 transitions
- Average: 2.33 transitions/issue

**Status Regressions:**
- PROJ-123: In Review → In Progress (regression detected)

### Xray Test Metrics

**Execution Statistics:**
- Total Test Executions: 2
- Total Test Runs: 5
- Pass Rate: 60% (3/5)
- Fail Rate: 20% (1/5)
- Not Executed: 20% (1/5)

**Test Duration:**
- PROJ-401: 2.5 minutes (PASS)
- PROJ-402: 3.75 minutes (FAIL)
- PROJ-403: 5.5 minutes (PASS)
- PROJ-404: 5.25 minutes (PASS)
- Average: 4.25 minutes

**Defects Found:** 1 (PROJ-500)

### Bitbucket Repository Metrics

**Commit Activity:**
- Total Commits: 5
- Total Contributors: 4
- Commits per Day: 1.0
- Busiest Day: Each day had 1 commit

**Contributor Ranking:**
1. John Doe: 2 commits (40%)
2. Bob Wilson: 1 commit (20%)
3. Jane Smith: 1 commit (20%)
4. Alice Brown: 1 commit (20%)

**Pull Request Metrics:**
- Total PRs: 3
- Merged: 2 (67%)
- Open: 1 (33%)
- Declined: 0 (0%)
- Average Time to Merge: ~36 hours

**Commit Types:**
- Fix: 1 (20%)
- Feature: 1 (20%)
- Refactor: 1 (20%)
- Docs: 1 (20%)
- Test: 1 (20%)

---

## Timestamp Reference

All timestamps use Unix epoch milliseconds or ISO 8601 format:

**Date Range:** January 10-23, 2024

**Jira Issues:**
- 2024-01-10: PROJ-124 created
- 2024-01-15: PROJ-123 created, status changes
- 2024-01-20: PROJ-123 status changes
- 2024-01-22: PROJ-124 completed
- 2024-01-23: PROJ-125 created

**Xray Test Executions:**
- 2024-01-15: PROJ-201 execution (10:30-11:05)
- 2024-01-20: PROJ-202 execution (09:00-16:45)

**Bitbucket Commits:**
- 2024-01-17: abcdef1 (John Doe)
- 2024-01-18: bcdef12 (Bob Wilson)
- 2024-01-19: cdef123 (Jane Smith)
- 2024-01-20: def1234 (Alice Brown)
- 2024-01-21: ef12345 (John Doe)

**Pull Requests:**
- 2024-01-16: PR #1 created
- 2024-01-17: PR #1 merged
- 2024-01-17: PR #2 created
- 2024-01-19: PR #2 merged
- 2024-01-20: PR #3 created (still open)

---

## File Format Notes

### JSON Structure

All JSON files follow the actual API response format:

- **Jira**: Standard Jira REST API v2 format
- **Xray**: Xray for Jira on-premise REST API format (Raven endpoints)
- **Bitbucket**: Bitbucket Server REST API 1.0 format

### Timestamps

- **Jira**: ISO 8601 strings (e.g., "2024-01-15T09:30:00.000+0000")
- **Xray**: ISO 8601 strings with 'Z' suffix (e.g., "2024-01-15T10:30:00.000Z")
- **Bitbucket**: Unix epoch milliseconds (e.g., 1705482000000)

### User References

Users are consistently represented across all mock data:
- john.doe / john.doe@example.com
- bob.wilson / bob.wilson@example.com
- jane.smith / jane.smith@example.com
- alice.brown / alice.brown@example.com
- qa.tester / qa.tester@example.com
- qa.automation / qa.automation@example.com

---

## Extending Mock Data

To add more test scenarios:

1. **Follow the existing structure** - Use current files as templates
2. **Maintain relationships** - Keep user emails, issue keys consistent
3. **Use realistic data** - Base timestamps on a coherent timeline
4. **Update this README** - Document new scenarios and expected results

### Example: Adding a New Issue

```json
{
  "id": "10004",
  "key": "PROJ-126",
  "fields": {
    "summary": "Your new issue summary",
    "issuetype": {"name": "Bug"},
    "status": {"name": "To Do"},
    "created": "2024-01-24T10:00:00.000+0000",
    // ... other fields
  },
  "changelog": {
    "histories": []
  }
}
```

---

## License

These mock data files are provided for testing purposes only and should not contain any real or sensitive data.
