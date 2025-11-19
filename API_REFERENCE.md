# API Reference - Bitbucket On-Premise Endpoints

This document details all Bitbucket Server/Data Center REST API endpoints used by the enhanced scraper.

---

## Base URL Structure

```
{BITBUCKET_URL}/rest/api/1.0/
```

Example: `https://bitbucket.company.com/rest/api/1.0/`

---

## Authentication

All endpoints require HTTP Basic Authentication:

```python
from requests.auth import HTTPBasicAuth

auth = HTTPBasicAuth(username, password)
# or
auth = HTTPBasicAuth('x-token-auth', api_token)
```

---

## Endpoints Reference

### 1. Repository Information

**GET** `/projects/{projectKey}/repos/{repositorySlug}`

Get repository metadata.

**Parameters:**
- `projectKey` (path): Project key (e.g., "PROJ")
- `repositorySlug` (path): Repository slug (e.g., "my-repo")

**Response:**
```json
{
  "slug": "my-repo",
  "name": "My Repository",
  "description": "Repository description",
  "state": "AVAILABLE",
  "public": false,
  "project": {
    "key": "PROJ",
    "name": "Project Name"
  }
}
```

**Implementation:** `jira_analyzer/bitbucket_fetcher.py:fetch_repository_info()`

---

### 2. Commits List

**GET** `/projects/{projectKey}/repos/{repositorySlug}/commits`

Fetch commits from repository with pagination.

**Parameters:**
- `projectKey` (path): Project key
- `repositorySlug` (path): Repository slug
- `limit` (query): Number of results per page (default: 25, max: 1000)
- `start` (query): Page start index (for pagination)
- `since` (query): Commit hash or timestamp to start from
- `until` (query): Commit hash or timestamp to end at

**Response:**
```json
{
  "size": 100,
  "limit": 100,
  "isLastPage": false,
  "nextPageStart": 100,
  "values": [
    {
      "id": "abcdef1234567890...",
      "displayId": "abcdef1",
      "author": {
        "name": "john.doe",
        "emailAddress": "john@example.com",
        "displayName": "John Doe"
      },
      "authorTimestamp": 1705482000000,
      "committer": {
        "name": "john.doe",
        "emailAddress": "john@example.com"
      },
      "committerTimestamp": 1705482000000,
      "message": "Fix authentication bug\n\nDetailed description...",
      "parents": [
        {"id": "fedcba0987654321..."}
      ]
    }
  ]
}
```

**Implementation:** `jira_analyzer/bitbucket_fetcher.py:fetch_commits()`

---

### 3. Commit Changes (Files)

**GET** `/projects/{projectKey}/repos/{repositorySlug}/commits/{commitId}/changes`

Get list of files changed in a commit.

**Parameters:**
- `projectKey` (path): Project key
- `repositorySlug` (path): Repository slug
- `commitId` (path): Full commit hash
- `limit` (query): Max number of changes (default: 25, max: 1000)
- `start` (query): Page start index

**Response:**
```json
{
  "values": [
    {
      "type": "MODIFY",
      "path": {
        "toString": "src/main/java/Auth.java",
        "components": ["src", "main", "java", "Auth.java"]
      },
      "srcPath": {
        "toString": "src/main/java/Auth.java"
      }
    },
    {
      "type": "ADD",
      "path": {
        "toString": "src/test/NewTest.java"
      }
    },
    {
      "type": "DELETE",
      "path": {
        "toString": "src/old/OldFile.java"
      },
      "srcPath": {
        "toString": "src/old/OldFile.java"
      }
    }
  ]
}
```

**Change Types:**
- `ADD`: File added
- `MODIFY`: File modified
- `DELETE`: File deleted
- `MOVE`: File moved/renamed
- `COPY`: File copied

**Implementation:** `jira_analyzer/bitbucket_fetcher.py:_fetch_commit_changes()`

---

### 4. Commit Diff (Line Changes)

**GET** `/projects/{projectKey}/repos/{repositorySlug}/commits/{commitId}/diff`

Get actual diff with line-level changes.

**Parameters:**
- `projectKey` (path): Project key
- `repositorySlug` (path): Repository slug
- `commitId` (path): Full commit hash
- `contextLines` (query): Number of context lines (default: 3)
  - Set to 0 to minimize response size
- `whitespace` (query): Whitespace handling
  - `SHOW`: Show all whitespace
  - `IGNORE_ALL`: Ignore all whitespace changes

**Response:**
```json
{
  "diffs": [
    {
      "source": {
        "toString": "src/Auth.java"
      },
      "destination": {
        "toString": "src/Auth.java"
      },
      "hunks": [
        {
          "sourceLine": 10,
          "sourceSpan": 5,
          "destinationLine": 10,
          "destinationSpan": 7,
          "segments": [
            {
              "type": "CONTEXT",
              "lines": [
                {"source": 10, "destination": 10, "line": "  public class Auth {"}
              ]
            },
            {
              "type": "REMOVED",
              "lines": [
                {"source": 11, "line": "    // Old implementation"},
                {"source": 12, "line": "    return false;"}
              ]
            },
            {
              "type": "ADDED",
              "lines": [
                {"destination": 11, "line": "    // New implementation"},
                {"destination": 12, "line": "    // With additional check"},
                {"destination": 13, "line": "    return validateToken();"}
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

**Segment Types:**
- `CONTEXT`: Unchanged lines (context)
- `ADDED`: Lines added
- `REMOVED`: Lines removed

**Calculation:**
```python
lines_added = count(segments where type == 'ADDED')
lines_removed = count(segments where type == 'REMOVED')
lines_modified = lines_added + lines_removed
```

**Implementation:** `jira_analyzer/bitbucket_fetcher.py:_fetch_commit_diff_stats()`

**Performance Note:**
- Use `contextLines=0` to get only changed lines
- Large commits may timeout - has 15s timeout
- Returns empty stats on failure (doesn't break entire fetch)

---

### 5. Pull Requests List

**GET** `/projects/{projectKey}/repos/{repositorySlug}/pull-requests`

Fetch pull requests from repository.

**Parameters:**
- `projectKey` (path): Project key
- `repositorySlug` (path): Repository slug
- `state` (query): Filter by state
  - `ALL`: All pull requests (default)
  - `OPEN`: Open PRs only
  - `MERGED`: Merged PRs only
  - `DECLINED`: Declined PRs only
- `limit` (query): Results per page (default: 25)
- `start` (query): Page start index

**Response:**
```json
{
  "values": [
    {
      "id": 1,
      "version": 5,
      "title": "Add authentication feature",
      "description": "Implements OAuth2 authentication...",
      "state": "MERGED",
      "createdDate": 1705482000000,
      "updatedDate": 1705568400000,
      "closedDate": 1705568400000,
      "fromRef": {
        "id": "refs/heads/feature/auth",
        "displayId": "feature/auth"
      },
      "toRef": {
        "id": "refs/heads/main",
        "displayId": "main"
      },
      "author": {
        "user": {
          "name": "john.doe",
          "emailAddress": "john@example.com",
          "displayName": "John Doe"
        }
      },
      "reviewers": [
        {
          "user": {
            "name": "jane.smith",
            "emailAddress": "jane@example.com"
          },
          "approved": true,
          "status": "APPROVED"
        }
      ]
    }
  ]
}
```

**PR States:**
- `OPEN`: Currently open
- `MERGED`: Merged to target branch
- `DECLINED`: Rejected/closed without merge

**Reviewer Status:**
- `UNAPPROVED`: Not yet reviewed
- `NEEDS_WORK`: Requested changes
- `APPROVED`: Approved

**Implementation:** `jira_analyzer/bitbucket_fetcher.py:fetch_pull_requests()`

---

### 6. Pull Request Activities

**GET** `/projects/{projectKey}/repos/{repositorySlug}/pull-requests/{pullRequestId}/activities`

Get activities (comments, reviews, approvals) for a pull request.

**Parameters:**
- `projectKey` (path): Project key
- `repositorySlug` (path): Repository slug
- `pullRequestId` (path): PR numeric ID
- `limit` (query): Results per page (default: 25, max: 1000)
- `start` (query): Page start index

**Response:**
```json
{
  "values": [
    {
      "id": 100,
      "createdDate": 1705482000000,
      "user": {
        "name": "jane.smith",
        "emailAddress": "jane@example.com"
      },
      "action": "COMMENTED",
      "comment": {
        "id": 200,
        "version": 0,
        "text": "Looks good, just one small suggestion...",
        "author": {
          "name": "jane.smith",
          "emailAddress": "jane@example.com"
        },
        "createdDate": 1705482000000,
        "updatedDate": 1705482000000
      }
    },
    {
      "id": 101,
      "createdDate": 1705485000000,
      "user": {
        "name": "bob.wilson",
        "emailAddress": "bob@example.com"
      },
      "action": "APPROVED",
      "comment": {
        "text": "LGTM"
      }
    },
    {
      "id": 102,
      "action": "REVIEWED"
    }
  ]
}
```

**Activity Actions:**
- `COMMENTED`: User added a comment
- `APPROVED`: User approved the PR
- `UNAPPROVED`: User removed approval
- `REVIEWED`: User marked as reviewed (without approval)
- `OPENED`: PR opened
- `UPDATED`: PR updated
- `MERGED`: PR merged
- `DECLINED`: PR declined

**Implementation:** `jira_analyzer/bitbucket_fetcher.py:_fetch_pr_activities()`

**Metrics Calculated:**
```python
comments_count = count(action == 'COMMENTED')
approvals_count = count(action == 'APPROVED')
reviews_count = count(action == 'REVIEWED')
total_activities = count(all activities)
```

---

### 7. Pull Request Diff

**GET** `/projects/{projectKey}/repos/{repositorySlug}/pull-requests/{pullRequestId}/diff`

Get diff for entire pull request (all changes between branches).

**Parameters:**
- `projectKey` (path): Project key
- `repositorySlug` (path): Repository slug
- `pullRequestId` (path): PR numeric ID
- `contextLines` (query): Context lines (default: 3, use 0 for minimal)
- `whitespace` (query): Whitespace handling

**Response:**
Same structure as commit diff (see section 4), but includes all changes across all commits in the PR.

**Implementation:** `jira_analyzer/bitbucket_fetcher.py:_fetch_pr_diff_stats()`

**Metrics Calculated:**
```python
files_changed = len(diffs)
lines_added = sum of all ADDED segments
lines_removed = sum of all REMOVED segments
lines_modified = lines_added + lines_removed
```

---

## Rate Limiting

Bitbucket Server API rate limits:
- Default: **900 requests per hour per user**
- Can be configured by admins

**Best Practices:**
1. Use pagination efficiently
2. Cache results when possible
3. Use `contextLines=0` for diffs
4. Implement exponential backoff on errors
5. Batch API calls where possible

**Current Implementation:**
- 10s timeout for regular requests
- 15s timeout for diff requests
- Graceful degradation (returns partial data on failure)
- No automatic retry (to be implemented)

---

## Error Handling

### Common HTTP Status Codes

| Code | Meaning | Handling |
|------|---------|----------|
| 200 | Success | Process response |
| 401 | Unauthorized | Check credentials |
| 403 | Forbidden | Check permissions |
| 404 | Not Found | Resource doesn't exist |
| 429 | Too Many Requests | Rate limited, back off |
| 500 | Server Error | Retry with backoff |

### Current Error Strategy

```python
try:
    response = session.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()
except Exception as e:
    # Log warning but don't fail entire fetch
    return default_empty_response
```

**Benefits:**
- Resilient to individual failures
- Continues fetching other data
- Provides partial results

---

## Data Flow

### Commit Fetching Flow

```
1. fetch_commits()
   ↓
2. For each commit:
   ├── _commit_to_dict() - Basic commit info
   ├── _fetch_commit_changes() - File list
   │   └── API: /commits/{id}/changes
   └── _fetch_commit_diff_stats() - Line counts
       └── API: /commits/{id}/diff
   ↓
3. Filter by user/date
   ↓
4. Return enriched commits list
```

### Pull Request Fetching Flow

```
1. fetch_pull_requests()
   ↓
2. For each PR:
   ├── _pr_to_dict() - Basic PR info
   ├── _fetch_pr_activities() - Comments/reviews
   │   └── API: /pull-requests/{id}/activities
   └── _fetch_pr_diff_stats() - Line counts
       └── API: /pull-requests/{id}/diff
   ↓
3. Filter by date
   ↓
4. Return enriched PRs list
```

---

## Performance Optimization

### Current Optimizations

1. **Minimal Context Lines:**
```python
params = {'contextLines': 0}  # Only fetch changed lines
```

2. **Timeout Management:**
```python
response = session.get(url, timeout=15)  # Prevent hanging
```

3. **Pagination:**
```python
params = {'limit': 100, 'start': next_page_start}
```

4. **Graceful Degradation:**
```python
try:
    stats = fetch_diff()
except:
    stats = {'lines_added': 0, 'lines_removed': 0}
```

### Future Optimizations

1. **Parallel Fetching:**
```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=5) as executor:
    futures = [executor.submit(fetch_diff, commit) for commit in commits]
    results = [f.result() for f in futures]
```

2. **Caching:**
```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def fetch_commit_diff(commit_id):
    ...
```

3. **Incremental Fetching:**
```python
# Store last fetch timestamp
# Only fetch commits since last run
since_timestamp = get_last_fetch_time()
commits = fetch_commits(since=since_timestamp)
```

---

## Testing Endpoints

### Manual Testing with curl

**Get repository info:**
```bash
curl -u username:password \
  "https://bitbucket.company.com/rest/api/1.0/projects/PROJ/repos/myrepo"
```

**Get commits:**
```bash
curl -u username:password \
  "https://bitbucket.company.com/rest/api/1.0/projects/PROJ/repos/myrepo/commits?limit=10"
```

**Get commit changes:**
```bash
curl -u username:password \
  "https://bitbucket.company.com/rest/api/1.0/projects/PROJ/repos/myrepo/commits/abc123/changes?limit=100"
```

**Get commit diff:**
```bash
curl -u username:password \
  "https://bitbucket.company.com/rest/api/1.0/projects/PROJ/repos/myrepo/commits/abc123/diff?contextLines=0"
```

**Get PRs:**
```bash
curl -u username:password \
  "https://bitbucket.company.com/rest/api/1.0/projects/PROJ/repos/myrepo/pull-requests?state=ALL&limit=10"
```

**Get PR activities:**
```bash
curl -u username:password \
  "https://bitbucket.company.com/rest/api/1.0/projects/PROJ/repos/myrepo/pull-requests/1/activities?limit=100"
```

---

## API Documentation References

- **Official Docs:** https://docs.atlassian.com/bitbucket-server/rest/
- **Bitbucket Server REST API:** version 1.0 (current)
- **Supported Versions:** Bitbucket Server/Data Center 5.0+

---

## Summary of Enhancements

| Endpoint | Purpose | Lines Added/Removed | Performance Impact |
|----------|---------|-------------------|-------------------|
| `/commits/{id}/changes` | File-level changes | File list | Low - Fast |
| `/commits/{id}/diff` | Line-level changes | +/- counts | Medium - Can be slow |
| `/pull-requests/{id}/activities` | Review engagement | Comments, approvals | Low - Fast |
| `/pull-requests/{id}/diff` | PR code changes | +/- counts | Medium - Can be slow |

**Total API Calls:**
- Per commit: 3 calls (list, changes, diff)
- Per PR: 3 calls (list, activities, diff)

**For 100 commits + 25 PRs:**
- Total: ~375 API calls
- Estimated time: 2-5 minutes
- With 900/hour limit: Well within limits

---

**Last Updated:** 2025-11-19
**API Version:** Bitbucket Server REST API 1.0
