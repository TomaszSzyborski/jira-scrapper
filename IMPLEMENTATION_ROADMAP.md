# Implementation Roadmap - New Analytics Features

Roadmapa implementacji nowych funkcji analitycznych dla Jira Analyzer i Bitbucket Analyzer.

---

## 📅 Phase 1: Foundation (Week 1-2) - PRIORITY 1

### 1.1 Team Workload Analysis (Jira)

**Objective:** Provide managers visibility into team workload distribution

**Implementation:**

```python
# jira_analyzer/team_analyzer.py
class TeamAnalyzer:
    """Analyze team workload and performance metrics."""

    def __init__(self, issues: list):
        self.issues = issues

    def calculate_workload(self) -> dict:
        """Calculate workload metrics per assignee."""
        workload = {}

        for issue in self.issues:
            assignee = issue.get('assignee', 'Unassigned')
            status = issue.get('status', '')
            issue_type = issue.get('type', '')

            if assignee not in workload:
                workload[assignee] = {
                    'total': 0,
                    'in_progress': 0,
                    'completed': 0,
                    'by_type': {}
                }

            workload[assignee]['total'] += 1

            # Count by status
            if status in ['In Progress', 'In Development', 'Review']:
                workload[assignee]['in_progress'] += 1
            elif status in ['Done', 'Closed', 'Resolved']:
                workload[assignee]['completed'] += 1

            # Count by type
            if issue_type not in workload[assignee]['by_type']:
                workload[assignee]['by_type'][issue_type] = 0
            workload[assignee]['by_type'][issue_type] += 1

        return workload

    def identify_overloaded(self, threshold: int = 10) -> list:
        """Identify team members with excessive WIP."""
        workload = self.calculate_workload()
        overloaded = []

        for assignee, metrics in workload.items():
            if metrics['in_progress'] > threshold:
                overloaded.append({
                    'assignee': assignee,
                    'wip': metrics['in_progress'],
                    'total': metrics['total']
                })

        return sorted(overloaded, key=lambda x: x['wip'], reverse=True)
```

**CLI Integration:**
```bash
# Add to main.py
python main.py --project PROJ --analyze-team --report
```

**Expected Output:** `team_workload_report.html`

---

### 1.2 Commit Quality Metrics (Bitbucket)

**Objective:** Measure code commit quality and patterns

**Implementation:**

```python
# bitbucket_analyzer/commit_quality.py
import re
from datetime import datetime
from collections import Counter

class CommitQualityAnalyzer:
    """Analyze commit message quality and patterns."""

    def __init__(self, commits: list):
        self.commits = commits

    def analyze_message_quality(self) -> dict:
        """Analyze commit message quality."""
        total = len(self.commits)
        good_messages = 0
        has_issue_ref = 0
        conventional_commits = 0

        # Conventional Commits pattern: type(scope): message
        conventional_pattern = r'^(feat|fix|docs|style|refactor|test|chore)(\(.+\))?: .+'
        issue_pattern = r'[A-Z]+-\d+'

        for commit in self.commits:
            message = commit.get('message', '').split('\n')[0]  # First line

            # Check message length (good practice: 50-72 chars)
            if 10 <= len(message) <= 72:
                good_messages += 1

            # Check for issue reference
            if re.search(issue_pattern, message):
                has_issue_ref += 1

            # Check conventional commits format
            if re.match(conventional_pattern, message):
                conventional_commits += 1

        return {
            'total_commits': total,
            'good_length': good_messages,
            'good_length_pct': (good_messages / total * 100) if total > 0 else 0,
            'has_issue_ref': has_issue_ref,
            'has_issue_ref_pct': (has_issue_ref / total * 100) if total > 0 else 0,
            'conventional': conventional_commits,
            'conventional_pct': (conventional_commits / total * 100) if total > 0 else 0
        }

    def analyze_commit_sizes(self) -> dict:
        """Analyze commit size distribution."""
        sizes = {
            'tiny': 0,      # < 10 lines
            'small': 0,     # 10-50 lines
            'medium': 0,    # 50-200 lines
            'large': 0,     # 200-500 lines
            'huge': 0       # > 500 lines
        }

        for commit_id, diff in self.commit_diffs.items():
            total_lines = diff['added'] + diff['deleted'] + diff['modified']

            if total_lines < 10:
                sizes['tiny'] += 1
            elif total_lines < 50:
                sizes['small'] += 1
            elif total_lines < 200:
                sizes['medium'] += 1
            elif total_lines < 500:
                sizes['large'] += 1
            else:
                sizes['huge'] += 1

        return sizes

    def analyze_timing_patterns(self) -> dict:
        """Analyze when commits are made."""
        hours = [0] * 24
        weekdays = [0] * 7
        weekend_commits = 0

        for commit in self.commits:
            timestamp = commit.get('authorTimestamp', 0) / 1000
            dt = datetime.fromtimestamp(timestamp)

            hours[dt.hour] += 1
            weekdays[dt.weekday()] += 1

            if dt.weekday() >= 5:  # Saturday or Sunday
                weekend_commits += 1

        return {
            'by_hour': hours,
            'by_weekday': weekdays,
            'weekend_commits': weekend_commits,
            'weekend_pct': (weekend_commits / len(self.commits) * 100) if self.commits else 0
        }
```

**CLI Integration:**
```bash
python bitbucket_main.py --project PROJ --repository repo \
    --analyze-quality
```

---

### 1.3 Simple Issue-Commit Linking (Integration)

**Objective:** Link Jira issues to Bitbucket commits

**Implementation:**

```python
# integrations/__init__.py
from .jira_bitbucket_linker import JiraBitbucketLinker

# integrations/jira_bitbucket_linker.py
import re
from collections import defaultdict

class JiraBitbucketLinker:
    """Link Jira issues with Bitbucket commits."""

    def __init__(self, jira_issues: list, bitbucket_commits: list):
        self.jira_issues = jira_issues
        self.bitbucket_commits = bitbucket_commits

    def link_commits_to_issues(self) -> dict:
        """Parse commit messages and link to Jira issues."""
        issue_pattern = r'([A-Z]+-\d+)'
        linked = defaultdict(list)

        for commit in self.bitbucket_commits:
            message = commit.get('message', '')
            matches = re.findall(issue_pattern, message)

            for issue_key in matches:
                linked[issue_key].append({
                    'commit_id': commit.get('id', '')[:8],
                    'message': message.split('\n')[0],
                    'author': commit.get('author', {}).get('name', ''),
                    'date': commit.get('authorTimestamp', 0),
                    'added': commit.get('stats', {}).get('added', 0),
                    'deleted': commit.get('stats', {}).get('deleted', 0)
                })

        return dict(linked)

    def calculate_code_metrics_per_issue(self) -> dict:
        """Calculate code metrics for each Jira issue."""
        linked = self.link_commits_to_issues()
        metrics = {}

        for issue_key, commits in linked.items():
            total_commits = len(commits)
            total_added = sum(c['added'] for c in commits)
            total_deleted = sum(c['deleted'] for c in commits)
            authors = set(c['author'] for c in commits)

            metrics[issue_key] = {
                'commit_count': total_commits,
                'lines_added': total_added,
                'lines_deleted': total_deleted,
                'net_lines': total_added - total_deleted,
                'authors': list(authors),
                'author_count': len(authors)
            }

        return metrics

    def generate_traceability_report(self, output_file: str = 'traceability_report.csv'):
        """Generate CSV report linking issues to commits."""
        import csv

        linked = self.link_commits_to_issues()

        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Issue Key', 'Commit ID', 'Author', 'Date', 'Message', 'Added', 'Deleted'])

            for issue_key, commits in linked.items():
                for commit in commits:
                    writer.writerow([
                        issue_key,
                        commit['commit_id'],
                        commit['author'],
                        commit['date'],
                        commit['message'],
                        commit['added'],
                        commit['deleted']
                    ])

        print(f"Traceability report saved to: {output_file}")
```

**CLI Tool:**
```bash
# integration_report.py
python integration_report.py \
    --jira-cache jira_bug_cached.json \
    --bitbucket-cache data/bitbucket_cache/PROJ_repo_*.json \
    --output traceability_report.csv
```

---

## 📅 Phase 2: Advanced Analytics (Week 3-4) - PRIORITY 2

### 2.1 Velocity & Predictability (Jira)

**Implementation:**

```python
# jira_analyzer/velocity_analyzer.py
import statistics
from datetime import datetime, timedelta

class VelocityAnalyzer:
    """Analyze velocity and predict completion dates."""

    def __init__(self, issues: list, sprint_duration_days: int = 14):
        self.issues = issues
        self.sprint_duration = sprint_duration_days

    def calculate_throughput(self, start_date: str, end_date: str) -> int:
        """Calculate number of issues completed in date range."""
        completed = 0

        for issue in self.issues:
            resolved = issue.get('resolved', '')
            if resolved:
                resolved_date = resolved.split('T')[0]
                if start_date <= resolved_date <= end_date:
                    completed += 1

        return completed

    def calculate_historical_velocity(self, num_sprints: int = 5) -> list:
        """Calculate velocity for last N sprints."""
        today = datetime.now()
        velocities = []

        for i in range(num_sprints):
            sprint_end = today - timedelta(days=i * self.sprint_duration)
            sprint_start = sprint_end - timedelta(days=self.sprint_duration)

            throughput = self.calculate_throughput(
                sprint_start.strftime('%Y-%m-%d'),
                sprint_end.strftime('%Y-%m-%d')
            )

            velocities.append({
                'sprint': f"Sprint {num_sprints - i}",
                'start': sprint_start.strftime('%Y-%m-%d'),
                'end': sprint_end.strftime('%Y-%m-%d'),
                'throughput': throughput
            })

        return list(reversed(velocities))

    def predict_completion_date(self, remaining_items: int) -> dict:
        """Predict completion date based on historical velocity."""
        velocities = self.calculate_historical_velocity()
        throughputs = [v['throughput'] for v in velocities]

        avg_velocity = statistics.mean(throughputs) if throughputs else 0
        std_velocity = statistics.stdev(throughputs) if len(throughputs) > 1 else 0

        if avg_velocity == 0:
            return {
                'error': 'Insufficient historical data'
            }

        # Calculate sprints needed
        sprints_needed = remaining_items / avg_velocity

        # Predict date
        today = datetime.now()
        predicted_date = today + timedelta(days=sprints_needed * self.sprint_duration)

        # Calculate confidence intervals (±1 std dev)
        optimistic_velocity = avg_velocity + std_velocity
        pessimistic_velocity = max(avg_velocity - std_velocity, avg_velocity * 0.5)

        optimistic_sprints = remaining_items / optimistic_velocity if optimistic_velocity > 0 else sprints_needed
        pessimistic_sprints = remaining_items / pessimistic_velocity if pessimistic_velocity > 0 else sprints_needed

        optimistic_date = today + timedelta(days=optimistic_sprints * self.sprint_duration)
        pessimistic_date = today + timedelta(days=pessimistic_sprints * self.sprint_duration)

        return {
            'avg_velocity': round(avg_velocity, 2),
            'std_velocity': round(std_velocity, 2),
            'remaining_items': remaining_items,
            'sprints_needed': round(sprints_needed, 1),
            'predicted_date': predicted_date.strftime('%Y-%m-%d'),
            'optimistic_date': optimistic_date.strftime('%Y-%m-%d'),
            'pessimistic_date': pessimistic_date.strftime('%Y-%m-%d'),
            'confidence': 'Medium' if std_velocity < avg_velocity * 0.3 else 'Low'
        }
```

---

### 2.2 PR Quality Metrics (Bitbucket)

**Implementation:**

```python
# bitbucket_analyzer/pr_analyzer.py
from datetime import datetime
import statistics

class PullRequestAnalyzer:
    """Analyze Pull Request quality metrics."""

    def __init__(self, pull_requests: list):
        self.prs = pull_requests

    def calculate_review_metrics(self) -> dict:
        """Calculate PR review quality metrics."""
        review_times = []
        comment_counts = []
        multi_reviewer_prs = 0

        for pr in self.prs:
            # Calculate review time (created → merged)
            created = pr.get('createdDate', 0) / 1000
            updated = pr.get('updatedDate', 0) / 1000

            if created and updated:
                review_time_hours = (updated - created) / 3600
                review_times.append(review_time_hours)

            # Count reviewers
            reviewers = pr.get('reviewers', [])
            if len(reviewers) >= 2:
                multi_reviewer_prs += 1

        return {
            'total_prs': len(self.prs),
            'avg_review_time_hours': statistics.mean(review_times) if review_times else 0,
            'median_review_time_hours': statistics.median(review_times) if review_times else 0,
            'multi_reviewer_pct': (multi_reviewer_prs / len(self.prs) * 100) if self.prs else 0
        }
```

---

## 📅 Phase 3: Integration & Automation (Week 5-6) - PRIORITY 3

### 3.1 Automated Release Notes Generator

**Implementation:**

```python
# integrations/release_notes_generator.py
from datetime import datetime
from .jira_bitbucket_linker import JiraBitbucketLinker

class ReleaseNotesGenerator:
    """Generate automated release notes from Jira and Bitbucket."""

    def __init__(self, jira_issues: list, bitbucket_commits: list,
                 sprint_name: str, start_date: str, end_date: str):
        self.jira_issues = jira_issues
        self.bitbucket_commits = bitbucket_commits
        self.sprint_name = sprint_name
        self.start_date = start_date
        self.end_date = end_date
        self.linker = JiraBitbucketLinker(jira_issues, bitbucket_commits)

    def generate_markdown(self) -> str:
        """Generate release notes in Markdown format."""
        # Filter completed issues
        completed_issues = [
            issue for issue in self.jira_issues
            if issue.get('status') in ['Done', 'Closed', 'Resolved']
        ]

        # Group by type
        features = [i for i in completed_issues if i.get('type') == 'Story']
        bugs = [i for i in completed_issues if i.get('type') in ['Bug', 'Błąd w programie']]
        tasks = [i for i in completed_issues if i.get('type') in ['Task', 'Zadanie Dev']]

        # Get code metrics
        code_metrics = self.linker.calculate_code_metrics_per_issue()

        # Build release notes
        notes = f"""# Release Notes - {self.sprint_name} ({self.start_date} to {self.end_date})

## ✨ New Features ({len(features)})

"""
        for issue in features:
            key = issue['key']
            summary = issue.get('summary', 'No summary')
            assignee = issue.get('assignee', 'Unassigned')
            lines = code_metrics.get(key, {}).get('net_lines', 0)

            notes += f"- [{key}] {summary} (@{assignee}, {lines:+d} lines)\n"

        notes += f"""

## 🐛 Bug Fixes ({len(bugs)})

"""
        for issue in bugs:
            key = issue['key']
            summary = issue.get('summary', 'No summary')
            assignee = issue.get('assignee', 'Unassigned')

            notes += f"- [{key}] {summary} (@{assignee})\n"

        # Statistics
        total_commits = len(self.bitbucket_commits)
        total_lines_added = sum(c.get('stats', {}).get('added', 0) for c in self.bitbucket_commits)
        total_lines_deleted = sum(c.get('stats', {}).get('deleted', 0) for c in self.bitbucket_commits)

        notes += f"""

## 📊 Statistics

- Total Issues Completed: {len(completed_issues)}
- Total Commits: {total_commits}
- Lines Added: {total_lines_added:,}
- Lines Deleted: {total_lines_deleted:,}
- Net Change: {total_lines_added - total_lines_deleted:+,} lines

"""

        return notes
```

**CLI Tool:**
```bash
python generate_release_notes.py \
    --sprint "Sprint 5" \
    --start-date 2024-11-01 \
    --end-date 2024-11-14 \
    --output release_notes_sprint5.md
```

---

## 📋 Implementation Checklist

### Phase 1 (Weeks 1-2)

- [ ] Create `jira_analyzer/team_analyzer.py`
- [ ] Create `bitbucket_analyzer/commit_quality.py`
- [ ] Create `integrations/` directory
- [ ] Create `integrations/jira_bitbucket_linker.py`
- [ ] Add CLI arguments to `main.py` for team analysis
- [ ] Add CLI arguments to `bitbucket_main.py` for quality analysis
- [ ] Create `integration_report.py` CLI tool
- [ ] Update tests
- [ ] Update documentation

### Phase 2 (Weeks 3-4)

- [ ] Create `jira_analyzer/velocity_analyzer.py`
- [ ] Create `bitbucket_analyzer/pr_analyzer.py`
- [ ] Integrate with existing reporters
- [ ] Add visualization for velocity trends
- [ ] Add visualization for PR metrics
- [ ] Update tests
- [ ] Update documentation

### Phase 3 (Weeks 5-6)

- [ ] Create `integrations/release_notes_generator.py`
- [ ] Create `generate_release_notes.py` CLI tool
- [ ] Add templates for release notes (Markdown, HTML, PDF)
- [ ] Create automation scripts (`scripts/` directory)
- [ ] Add scheduled job examples (cron, GitHub Actions)
- [ ] Update tests
- [ ] Final documentation

---

## 🚀 Deployment Strategy

### 1. Development

```bash
# Create feature branch
git checkout -b feature/team-workload-analysis

# Implement
# ... code ...

# Test
pytest tests/test_team_analyzer.py

# Commit
git commit -m "feat: Add team workload analysis"

# Push
git push origin feature/team-workload-analysis
```

### 2. Testing

```bash
# Run full test suite
pytest --cov=jira_analyzer --cov=bitbucket_analyzer --cov=integrations

# Generate coverage report
pytest --cov-report=html
```

### 3. Documentation

```bash
# Update README with new features
# Add examples to EXAMPLE_REPORTS.md
# Update NEW_ANALYSES_PROPOSALS.md with "Implemented" status
```

### 4. Release

```bash
# Merge to main
git checkout main
git merge feature/team-workload-analysis

# Tag release
git tag -a v1.1.0 -m "Release v1.1.0: Team Workload Analysis"
git push origin v1.1.0
```

---

## 📈 Success Metrics

### Phase 1 Success Criteria

- [ ] Team workload report generates successfully
- [ ] Commit quality metrics calculated correctly
- [ ] Issue-commit linking works for 95%+ of commits with issue refs
- [ ] Reports load in < 2 seconds
- [ ] Test coverage > 80%

### Phase 2 Success Criteria

- [ ] Velocity predictions within ±20% accuracy
- [ ] PR metrics match manual inspection
- [ ] Visualization performance acceptable (< 3s load time)
- [ ] Test coverage > 85%

### Phase 3 Success Criteria

- [ ] Release notes generation automated
- [ ] Automation scripts work in CI/CD
- [ ] Documentation complete
- [ ] Test coverage > 90%

---

## 🔄 Feedback Loop

### Weekly Review

1. **What worked well?**
2. **What didn't work?**
3. **What to improve?**
4. **Adjust roadmap based on feedback**

### User Feedback Channels

- GitHub Issues
- Slack channel: #jira-analyzer-feedback
- Email: team@company.com
- Retrospective meetings

---

## 📞 Contact

Questions or suggestions about this roadmap?

- Open a GitHub issue
- Slack: #jira-analyzer-dev
- Email: dev-team@company.com

---

**Last Updated:** 2024-11-18
**Next Review:** 2024-12-01
