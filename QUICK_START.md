# Quick Start Guide - Xray & Bitbucket Scrapers

> **Note:** Bitbucket components have been reorganized into a dedicated `bitbucket_analyzer` package.
> See [MIGRATION_SUMMARY.md](MIGRATION_SUMMARY.md) for details.

## Prerequisites

1. Python 3.13+ installed
2. Virtual environment set up
3. Dependencies installed

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```bash
# For Jira/Xray (On-premise)
JIRA_URL=https://jira.yourcompany.com
JIRA_USERNAME=your_username
JIRA_PASSWORD=your_password

# For Bitbucket (On-premise)
BITBUCKET_URL=https://bitbucket.yourcompany.com
BITBUCKET_USERNAME=your_username
BITBUCKET_PASSWORD=your_password
```

## Testing

Verify everything works:

```bash
python test_scrapers.py --all
```

Expected output:
```
✅ Xray Fetcher: PASSED
✅ Xray Analyzer: PASSED
✅ Bitbucket Fetcher: PASSED
✅ Bitbucket Analyzer: PASSED

🎉 All tests PASSED!
```

## Usage

### Xray Test Execution Analysis

**Basic analysis:**
```bash
python xray_main.py --project MYPROJ --report
```

**With date range:**
```bash
python xray_main.py --project MYPROJ \
  --start-date 2024-01-01 \
  --end-date 2024-12-31 \
  --report
```

**For specific test plan:**
```bash
python xray_main.py --project MYPROJ \
  --test-plan MYPROJ-123 \
  --report
```

**Output:**
- Console: Test metrics summary (pass/fail rates, defects, duration)
- File: `xray_test_report.html` - Comprehensive HTML report
- Cache: `xray_test_executions.json` - Raw data cache

**Key Metrics:**
- Pass/fail rates
- Test execution trends
- Test duration statistics
- Defect detection
- Test coverage (tests not run in 30/60/90 days)
- Execution efficiency

---

### Bitbucket Repository Analysis

**Basic commit analysis:**
```bash
python bitbucket_main.py --project PROJ --repository myrepo --report
```

**With PR analysis:**
```bash
python bitbucket_main.py --project PROJ --repository myrepo \
  --fetch-prs \
  --report
```

**Filter by date:**
```bash
python bitbucket_main.py --project PROJ --repository myrepo \
  --start-date 2024-01-01 \
  --end-date 2024-12-31 \
  --fetch-prs \
  --report
```

**Filter by contributors:**
```bash
python bitbucket_main.py --project PROJ --repository myrepo \
  --user-emails john@example.com,jane@example.com \
  --fetch-prs \
  --report
```

**Output:**
- Console: Comprehensive repository metrics
- File: `bitbucket_report.html` - HTML report with visualizations
- Cache: `bitbucket_data.json` - Raw data cache

**Key Metrics:**

📊 **Summary:**
- Total commits, contributors, pull requests
- Date range covered

💻 **Code Churn:**
- Lines added/removed/modified
- Net code change
- Files changed
- Commit size distribution (small/medium/large)
- Average lines & files per commit

🔍 **Pull Request Analysis:**
- PR lines modified
- Average PR size
- Comments and approvals per PR
- Review engagement rate
- PR size distribution

👥 **Contributor Stats:**
- Commits per contributor
- Lines added/removed per contributor
- Files changed per contributor
- Activity timeline

📈 **Activity:**
- Busiest days
- Commits per day
- Top contributors

---

## Common Scenarios

### 1. Monthly Team Performance Review

```bash
# Get last month's data
python bitbucket_main.py --project PROJ --repository myrepo \
  --start-date 2024-10-01 \
  --end-date 2024-10-31 \
  --fetch-prs \
  --report
```

Review:
- Total code changes (lines added/removed)
- Contributor productivity
- PR review quality (engagement rate)
- Commit patterns (size distribution)

### 2. Test Execution Health Check

```bash
# Check test health for last quarter
python xray_main.py --project MYPROJ \
  --start-date 2024-07-01 \
  --end-date 2024-09-30 \
  --report
```

Review:
- Pass/fail trends
- Tests not executed recently
- Test duration changes
- Defect detection rate

### 3. Code Review Quality Analysis

```bash
# Focus on PR analysis with review metrics
python bitbucket_main.py --project PROJ --repository myrepo \
  --fetch-prs \
  --pr-state ALL \
  --report
```

Review:
- Review engagement rate
- Comments per PR
- Approvals per PR
- Review time
- PR size vs engagement correlation

### 4. Individual Contributor Analysis

```bash
# Analyze specific contributor's work
python bitbucket_main.py --project PROJ --repository myrepo \
  --user-emails john.doe@company.com \
  --fetch-prs \
  --report
```

Review:
- Commit frequency and patterns
- Code churn (lines added/removed)
- PR participation
- Files touched

---

## Advanced Options

### Xray Options

```bash
python xray_main.py --help
```

Key flags:
- `--project` / `-p`: Project key (required)
- `--start-date` / `-s`: Start date (YYYY-MM-DD)
- `--end-date` / `-e`: End date (YYYY-MM-DD)
- `--test-plan` / `-t`: Filter by test plan
- `--batch-size` / `-b`: Batch size for API calls (default: 100)
- `--output` / `-o`: Cache file path (default: xray_test_executions.json)
- `--report` / `-r`: Generate HTML report
- `--report-output`: HTML report path (default: xray_test_report.html)
- `--force-fetch` / `-f`: Ignore cache, fetch fresh data

### Bitbucket Options

```bash
python bitbucket_main.py --help
```

Key flags:
- `--project`: Project key (required)
- `--repository`: Repository slug (required)
- `--start-date`: Start date (YYYY-MM-DD)
- `--end-date`: End date (YYYY-MM-DD)
- `--user-emails`: Filter by user emails (comma-separated)
- `--user-names`: Filter by usernames (comma-separated)
- `--fetch-prs`: Include pull request analysis
- `--pr-state`: PR state filter (ALL, OPEN, MERGED, DECLINED)
- `--batch-size`: Batch size for API calls (default: 100)
- `--output`: Cache file path (default: bitbucket_data.json)
- `--report`: Generate HTML report
- `--report-output`: HTML report path (default: bitbucket_report.html)
- `--force-fetch`: Ignore cache, fetch fresh data

---

## Performance Tips

### For Large Repositories

1. **Use date ranges** to limit data:
```bash
--start-date 2024-10-01 --end-date 2024-10-31
```

2. **Filter by users** for team-specific analysis:
```bash
--user-emails team1@company.com,team2@company.com
```

3. **Use caching** - Run without `--force-fetch` to reuse cached data

4. **Adjust batch size** if hitting rate limits:
```bash
--batch-size 50
```

### For Diff Fetching (Bitbucket)

The scraper fetches diffs for every commit and PR, which can be slow for large repos:

- **First run**: Will be slower as it fetches all diffs
- **Subsequent runs**: Use cached data with `--report` only
- **For analysis only**: Use cached data, don't re-fetch

---

## Troubleshooting

### Authentication Issues

**Error:** `ValueError: Missing credentials`

**Solution:** Check `.env` file has correct credentials

### API Connection Issues

**Error:** `ConnectionError` or timeout

**Solutions:**
- Verify URL is correct (no trailing slash)
- Check network connectivity
- Verify credentials are valid
- Check if VPN is required

### Rate Limiting

**Error:** `429 Too Many Requests`

**Solutions:**
- Reduce `--batch-size`
- Add delays between requests
- Check with admin about rate limits

### Xray On-Premise API Issues

**Error:** `Could not fetch test runs`

**Solutions:**
- Ensure Xray is installed and configured
- Verify you have permissions to access test executions
- Check Xray version (should be 3.0+)
- The scraper will automatically try Cloud API as fallback

### Bitbucket Diff Fetch Slow

**Symptom:** Very slow fetching

**Solutions:**
- Use date filters to reduce commit count
- Use user filters to focus on specific contributors
- Consider fetching without `--fetch-prs` for faster results
- The scraper uses `contextLines=0` to minimize diff size

---

## Understanding the Output

### Console Output Example

```
================================================================================
Bitbucket Repository Analyzer
================================================================================

Fetching commits from PROJ/myrepo...
  Fetched 100 commits (total: 100)
Total commits fetched: 100

================================================================================
Analyzing repository data...
================================================================================

📊 Summary:
  Total Commits: 100
  Total Contributors: 8
  Total Pull Requests: 25

📈 Activity:
  Busiest Day: 2024-10-15 (12 commits)
  Avg Commits/Day: 2.50
  Top Contributor: John Doe (45 commits)

💻 Code Churn:
  Total Lines Added: 8,234
  Total Lines Removed: 2,456
  Total Lines Modified: 10,690
  Net Lines Change: +5,778
  Total Files Changed: 523
  Avg Lines/Commit: 106.9
  Avg Files/Commit: 5.2
  Commit Sizes: 60 small, 30 medium, 10 large

🔍 Pull Request Analysis:
  Total PR Lines Modified: 4,567
  Avg PR Size: 182.7 lines
  Avg Comments/PR: 3.2
  Avg Approvals/PR: 2.1
  Review Engagement Rate: 84.0%
  PR Sizes: 10 small, 12 medium, 3 large

👥 Top 5 Contributors:
  1. John Doe (john@example.com)
      45 commits | +3,456/-987 lines | 234 files
  2. Jane Smith (jane@example.com)
      28 commits | +2,345/-678 lines | 156 files
  ...

================================================================================
Done!
================================================================================
```

### HTML Report Features

Both HTML reports include:
- Interactive charts and graphs
- Detailed tables with sortable columns
- Trend analysis over time
- Downloadable data
- Print-friendly formatting

---

## Examples for Different Use Cases

### Sprint Review
```bash
# Analyze last 2 weeks of work
python bitbucket_main.py --project PROJ --repository myrepo \
  --start-date 2024-10-21 \
  --end-date 2024-11-04 \
  --fetch-prs --report
```

### Quality Assurance
```bash
# Check test execution health
python xray_main.py --project QA --report

# Review test coverage
# Check "Tests not executed" metrics in report
```

### Team Productivity
```bash
# Analyze team's monthly contribution
python bitbucket_main.py --project PROJ --repository myrepo \
  --start-date 2024-10-01 \
  --end-date 2024-10-31 \
  --user-emails team@company.com \
  --fetch-prs --report
```

### Code Review Process
```bash
# Analyze PR review patterns
python bitbucket_main.py --project PROJ --repository myrepo \
  --fetch-prs --pr-state MERGED --report

# Focus on engagement rate and review time metrics
```

---

## Getting Help

- **For Xray issues**: Check `xray_main.py --help`
- **For Bitbucket issues**: Check `bitbucket_main.py --help`
- **For test failures**: Run `python test_scrapers.py --all` to diagnose
- **For detailed changes**: See `SCRAPER_FIXES_SUMMARY.md`

---

**Last Updated:** 2025-11-19
