# Dodatkowe Metryki - Jira & Bitbucket

Kompletny katalog metryk które można zebrać z Jiry i Bitbucketa, poza tymi już zaimplementowanymi.

---

## 📊 JIRA - Metryki Dodatkowe

### 1. Metryki Czasu (Time Metrics)

#### 1.1 Lead Time Analysis
```python
# Lead Time = czas od utworzenia do zamknięcia
lead_times = []
for issue in issues:
    created = parse_date(issue['created'])
    resolved = parse_date(issue['resolved'])
    if resolved:
        lead_time_days = (resolved - created).days
        lead_times.append(lead_time_days)

metrics = {
    'avg_lead_time': mean(lead_times),
    'median_lead_time': median(lead_times),
    'p85_lead_time': percentile(lead_times, 85),
    'p95_lead_time': percentile(lead_times, 95)
}
```

**Wartość:** SLA tracking, customer expectations

---

#### 1.2 Time to First Response
```python
# Czas od utworzenia do pierwszego komentarza/przypisania
for issue in issues:
    created = parse_date(issue['created'])
    first_comment = parse_date(issue['changelog'][0]['created']) if issue['changelog'] else None
    first_assigned = find_first_assignment(issue['changelog'])

    time_to_response = min(first_comment, first_assigned) - created
```

**Wartość:** Support team performance, customer satisfaction

---

#### 1.3 Time in Each Status (Extended)
```python
# Już masz podstawową wersję, ale możesz dodać:
status_transitions = {
    'time_in_backlog': 0,
    'time_in_analysis': 0,
    'time_in_development': 0,
    'time_in_code_review': 0,
    'time_in_qa': 0,
    'time_in_uat': 0,
    'time_blocked': 0,  # ⚠️ WAŻNE
    'time_waiting': 0    # Statusy typu "Waiting for..."
}

# Dla każdego issue:
for transition in issue['transitions']:
    status = transition['to_status']
    duration = transition['duration_hours']

    if 'block' in status.lower():
        status_transitions['time_blocked'] += duration
    elif 'wait' in status.lower():
        status_transitions['time_waiting'] += duration
```

**Wartość:** Bottleneck identification, process optimization

---

#### 1.4 Response Time by Priority
```python
# Czas reakcji w zależności od priorytetu
response_by_priority = {
    'Blocker': [],
    'Critical': [],
    'Major': [],
    'Minor': []
}

for issue in issues:
    priority = issue['priority']
    response_time = calculate_time_to_first_response(issue)
    response_by_priority[priority].append(response_time)

# SLA compliance
sla_targets = {
    'Blocker': 1,    # 1 hour
    'Critical': 4,   # 4 hours
    'Major': 24,     # 1 day
    'Minor': 72      # 3 days
}

compliance = {}
for priority, times in response_by_priority.items():
    within_sla = [t for t in times if t <= sla_targets[priority]]
    compliance[priority] = len(within_sla) / len(times) * 100
```

**Wartość:** SLA monitoring, priority handling effectiveness

---

### 2. Metryki Jakości (Quality Metrics)

#### 2.1 Defect Escape Rate
```python
# Błędy znalezione w produkcji vs w testach
bugs_in_production = [b for b in bugs if 'production' in b.get('environment', '').lower()]
bugs_in_testing = [b for b in bugs if 'test' in b.get('environment', '').lower()]

defect_escape_rate = len(bugs_in_production) / (len(bugs_in_production) + len(bugs_in_testing)) * 100
```

**Wartość:** QA effectiveness, testing coverage

---

#### 2.2 Bug Reopen Rate
```python
# Już wspomniane, ale szczegóły:
reopened_bugs = []
for bug in bugs:
    reopen_count = 0
    for transition in bug['changelog']:
        if transition['to_status'] == 'Reopened':
            reopen_count += 1

    if reopen_count > 0:
        reopened_bugs.append({
            'key': bug['key'],
            'reopen_count': reopen_count,
            'assignee': bug['assignee'],
            'component': bug['component']
        })

reopen_rate = len(reopened_bugs) / len(bugs) * 100

# Top reopeners (by assignee)
by_assignee = {}
for bug in reopened_bugs:
    assignee = bug['assignee']
    by_assignee[assignee] = by_assignee.get(assignee, 0) + 1
```

**Wartość:** Quality issues identification, developer performance

---

#### 2.3 Bug Severity Trends
```python
# Trend severity bugów w czasie
bugs_by_severity_over_time = {
    'Blocker': defaultdict(int),
    'Critical': defaultdict(int),
    'Major': defaultdict(int),
    'Minor': defaultdict(int)
}

for bug in bugs:
    month = bug['created'][:7]  # YYYY-MM
    severity = bug['priority']
    bugs_by_severity_over_time[severity][month] += 1

# Czy severity rośnie czy maleje?
trend_analysis = calculate_trend(bugs_by_severity_over_time['Blocker'].values())
```

**Wartość:** Quality trends, early warning system

---

#### 2.4 First Time Pass Rate
```python
# % zadań które przeszły QA za pierwszym razem (bez powrotu do Development)
first_time_pass = 0
total_tested = 0

for issue in issues:
    went_to_qa = any(t['to_status'] in ['In Test', 'QA'] for t in issue['transitions'])
    if went_to_qa:
        total_tested += 1
        returned_to_dev = any(
            t['from_status'] in ['In Test', 'QA'] and t['to_status'] in ['In Development', 'Development']
            for t in issue['transitions']
        )
        if not returned_to_dev:
            first_time_pass += 1

first_time_pass_rate = first_time_pass / total_tested * 100
```

**Wartość:** Development quality, testing effectiveness

---

### 3. Metryki Produktywności (Productivity Metrics)

#### 3.1 Work in Progress (WIP) Limits
```python
# WIP limits per team/person
daily_wip = defaultdict(lambda: defaultdict(int))

for issue in issues:
    for transition in issue['transitions']:
        date = transition['date'].split('T')[0]
        if transition['to_status'] in ['In Progress', 'In Development']:
            assignee = issue['assignee']
            daily_wip[date][assignee] += 1

# Violations of WIP limit (e.g., >3 tasks)
wip_violations = {}
for date, assignees in daily_wip.items():
    for assignee, wip_count in assignees.items():
        if wip_count > 3:  # Limit
            if assignee not in wip_violations:
                wip_violations[assignee] = []
            wip_violations[assignee].append({
                'date': date,
                'wip': wip_count
            })
```

**Wartość:** Prevent multitasking, improve focus

---

#### 3.2 Context Switching Rate
```python
# Ile razy developer zmienił zadanie w ciągu dnia
context_switches_per_day = defaultdict(lambda: defaultdict(int))

for issue in issues:
    for transition in issue['transitions']:
        if transition['to_status'] == 'In Progress':
            date = transition['date'].split('T')[0]
            assignee = issue['assignee']
            context_switches_per_day[date][assignee] += 1

# High context switching = low productivity
for date, assignees in context_switches_per_day.items():
    for assignee, switches in assignees.items():
        if switches > 5:  # More than 5 task switches per day
            print(f"⚠️ {assignee} switched {switches} tasks on {date}")
```

**Wartość:** Productivity optimization, workflow improvement

---

#### 3.3 Task Completion Rate
```python
# % zadań ukończonych w planowanym czasie (jeśli są story points/estimates)
completed_on_time = 0
total_with_estimate = 0

for issue in issues:
    if issue.get('original_estimate'):
        total_with_estimate += 1
        actual_time = calculate_actual_time(issue)
        estimated_time = issue['original_estimate']

        if actual_time <= estimated_time * 1.2:  # 20% buffer
            completed_on_time += 1

completion_rate = completed_on_time / total_with_estimate * 100
```

**Wartość:** Estimation accuracy, planning improvement

---

#### 3.4 Blocked Time Ratio
```python
# % czasu spędzonego w statusie "Blocked"
total_blocked_hours = 0
total_active_hours = 0

for issue in issues:
    for transition in issue['transitions']:
        duration = transition['duration_hours']
        status = transition['to_status']

        if 'block' in status.lower():
            total_blocked_hours += duration

        if status in ['In Progress', 'In Development', 'Review', 'QA']:
            total_active_hours += duration

blocked_ratio = total_blocked_hours / (total_active_hours + total_blocked_hours) * 100

# By blocker reason (z komentarzy)
blocker_reasons = extract_blocker_reasons(issues)
top_blockers = Counter(blocker_reasons).most_common(10)
```

**Wartość:** Remove impediments, improve flow

---

### 4. Metryki Planowania (Planning Metrics)

#### 4.1 Sprint Commitment Accuracy
```python
# % zadań z początku sprintu które zostały ukończone
for sprint in sprints:
    committed = [i for i in issues if sprint['label'] in i['labels'] and i['sprint_added'] == 'start']
    completed = [i for i in committed if i['status'] in ['Done', 'Closed']]

    commitment_accuracy = len(completed) / len(committed) * 100

    sprint_metrics[sprint['name']] = {
        'committed': len(committed),
        'completed': len(completed),
        'accuracy': commitment_accuracy,
        'added_mid_sprint': len([i for i in issues if sprint['label'] in i['labels'] and i['sprint_added'] == 'mid'])
    }
```

**Wartość:** Planning accuracy, scope creep detection

---

#### 4.2 Estimation Accuracy
```python
# Porównanie estimate vs actual
estimation_variance = []

for issue in issues:
    if issue.get('original_estimate') and issue.get('time_spent'):
        estimate = issue['original_estimate']
        actual = issue['time_spent']
        variance = (actual - estimate) / estimate * 100

        estimation_variance.append({
            'issue': issue['key'],
            'estimate': estimate,
            'actual': actual,
            'variance_pct': variance
        })

# Średni variance per typ zadania
by_type = defaultdict(list)
for item in estimation_variance:
    issue_type = get_issue_type(item['issue'])
    by_type[issue_type].append(item['variance_pct'])

avg_variance_by_type = {
    issue_type: mean(variances)
    for issue_type, variances in by_type.items()
}
```

**Wartość:** Improve estimation, better planning

---

#### 4.3 Epic Completion Prediction
```python
# Predykcja kiedy Epic będzie ukończony
for epic in epics:
    total_stories = count_stories_in_epic(epic)
    completed_stories = count_completed_stories_in_epic(epic)
    remaining_stories = total_stories - completed_stories

    # Historical velocity for this epic
    completed_per_sprint = calculate_completion_rate(epic)

    if completed_per_sprint > 0:
        sprints_remaining = remaining_stories / completed_per_sprint
        estimated_completion = today + timedelta(weeks=sprints_remaining * 2)

    epic_predictions[epic['key']] = {
        'total_stories': total_stories,
        'completed': completed_stories,
        'remaining': remaining_stories,
        'completion_rate': completed_per_sprint,
        'estimated_completion': estimated_completion
    }
```

**Wartość:** Epic tracking, stakeholder communication

---

### 5. Metryki Zespołowe (Team Metrics)

#### 5.1 Collaboration Score
```python
# Ile razy ludzie współpracują (reassignments, watchers, comments)
collaboration_matrix = defaultdict(lambda: defaultdict(int))

for issue in issues:
    # Reassignments
    assignees = extract_all_assignees(issue)
    for i, assignee1 in enumerate(assignees):
        for assignee2 in assignees[i+1:]:
            collaboration_matrix[assignee1][assignee2] += 1
            collaboration_matrix[assignee2][assignee1] += 1

    # Comments
    commenters = [c['author'] for c in issue.get('comments', [])]
    unique_commenters = set(commenters) - {issue['assignee']}
    for commenter in unique_commenters:
        collaboration_matrix[issue['assignee']][commenter] += 1

# Top collaborators
for person1, partners in collaboration_matrix.items():
    top_partners = sorted(partners.items(), key=lambda x: x[1], reverse=True)[:5]
    print(f"{person1} collaborates most with: {top_partners}")
```

**Wartość:** Team dynamics, knowledge sharing

---

#### 5.2 Knowledge Distribution
```python
# Które komponenty/obszary zna każda osoba
knowledge_map = defaultdict(lambda: defaultdict(int))

for issue in issues:
    component = issue.get('component', 'Unknown')
    assignee = issue['assignee']
    knowledge_map[assignee][component] += 1

# Bus factor - ile osób zna każdy komponent
bus_factor = {}
for component in all_components:
    experts = [person for person, comps in knowledge_map.items() if comps[component] > 5]
    bus_factor[component] = len(experts)

    if len(experts) == 1:
        print(f"⚠️ Risk: {component} tylko {experts[0]} zna!")
```

**Wartość:** Risk management, knowledge transfer planning

---

#### 5.3 Load Balancing
```python
# Równomierność rozłożenia pracy
workload_distribution = {}

for assignee in all_assignees:
    assigned_issues = [i for i in issues if i['assignee'] == assignee]
    workload_distribution[assignee] = {
        'total': len(assigned_issues),
        'in_progress': len([i for i in assigned_issues if i['status'] in ['In Progress', 'In Development']]),
        'story_points': sum(i.get('story_points', 0) for i in assigned_issues)
    }

# Calculate standard deviation
total_loads = [w['total'] for w in workload_distribution.values()]
std_dev = statistics.stdev(total_loads)
mean_load = statistics.mean(total_loads)

imbalance_score = std_dev / mean_load * 100  # CV - coefficient of variation
```

**Wartość:** Fair work distribution, prevent burnout

---

### 6. Metryki Procesu (Process Metrics)

#### 6.1 Definition of Done Compliance
```python
# Czy checklist DoD został wypełniony (z custom fields)
dod_compliance = 0
total_checked = 0

for issue in issues:
    if issue.get('dod_checklist'):
        total_checked += 1
        checklist = issue['dod_checklist']

        # All items checked?
        if all(item['checked'] for item in checklist):
            dod_compliance += 1

compliance_rate = dod_compliance / total_checked * 100
```

**Wartość:** Process adherence, quality assurance

---

#### 6.2 Rollback Rate
```python
# Ile razy deployment został wycofany (z labels "rollback")
deployments = [i for i in issues if 'deployment' in i.get('labels', [])]
rollbacks = [i for i in issues if 'rollback' in i.get('labels', [])]

rollback_rate = len(rollbacks) / len(deployments) * 100

# By release
by_release = defaultdict(lambda: {'deployments': 0, 'rollbacks': 0})
for deployment in deployments:
    release = deployment.get('fix_version')
    by_release[release]['deployments'] += 1

for rollback in rollbacks:
    release = rollback.get('fix_version')
    by_release[release]['rollbacks'] += 1
```

**Wartość:** Deployment quality, CI/CD effectiveness

---

## 💻 BITBUCKET - Metryki Dodatkowe

### 1. Metryki Kodu (Code Metrics)

#### 1.1 Code Coverage Trends
```python
# Jeśli commity zawierają coverage data (np. z CI/CD)
coverage_over_time = []

for commit in commits:
    if 'coverage' in commit.get('metadata', {}):
        coverage_over_time.append({
            'date': commit['date'],
            'coverage': commit['metadata']['coverage'],
            'author': commit['author']
        })

# Trend
coverage_trend = calculate_trend([c['coverage'] for c in coverage_over_time])
```

**Wartość:** Test quality tracking

---

#### 1.2 Cyclomatic Complexity per Commit
```python
# Jeśli używasz narzędzi do analizy statycznej
complexity_changes = []

for commit in commits:
    diff = get_commit_diff(commit)

    # Prosty heurystyk - liczba if/for/while dodanych
    added_complexity = count_complexity_keywords(diff['added_lines'])
    removed_complexity = count_complexity_keywords(diff['deleted_lines'])

    net_complexity = added_complexity - removed_complexity

    complexity_changes.append({
        'commit': commit['id'],
        'net_complexity': net_complexity,
        'author': commit['author']
    })

# Top complexity adders
by_author = defaultdict(int)
for change in complexity_changes:
    by_author[change['author']] += change['net_complexity']
```

**Wartość:** Code maintainability tracking

---

#### 1.3 Code Duplication Rate
```python
# Liczba commitów które dodają zduplikowany kod
# (wymaga integracji z narzędziami typu SonarQube)
duplication_commits = 0

for commit in commits:
    if 'duplication_added' in commit.get('quality_metrics', {}):
        if commit['quality_metrics']['duplication_added'] > 0:
            duplication_commits += 1

duplication_rate = duplication_commits / len(commits) * 100
```

**Wartość:** Code quality, refactoring needs

---

### 2. Metryki Współpracy (Collaboration Metrics)

#### 2.1 PR Approval Network
```python
# Kto zatwierdza czyje PRy
approval_network = defaultdict(lambda: defaultdict(int))

for pr in pull_requests:
    author = pr['author']
    approvers = [r['user'] for r in pr.get('reviewers', []) if r.get('approved')]

    for approver in approvers:
        approval_network[approver][author] += 1

# Czy są "approval bubbles" (tylko w ramach podgrupy)?
# Graph analysis - detect clusters
```

**Wartość:** Review quality, team structure insights

---

#### 2.2 Cross-Team Contributions
```python
# Contributions poza własnym zespołem
team_mapping = {
    'Backend': ['user1', 'user2'],
    'Frontend': ['user3', 'user4'],
    'Mobile': ['user5', 'user6']
}

cross_team_commits = defaultdict(lambda: defaultdict(int))

for commit in commits:
    author = commit['author']
    author_team = get_team(author, team_mapping)

    files_changed = commit['files']
    for file in files_changed:
        file_team = infer_team_from_path(file)  # backend/, frontend/, mobile/

        if file_team and file_team != author_team:
            cross_team_commits[author][file_team] += 1

# Who contributes most across teams?
cross_team_champions = sorted(
    [(author, sum(teams.values())) for author, teams in cross_team_commits.items()],
    key=lambda x: x[1],
    reverse=True
)
```

**Wartość:** Knowledge sharing, team integration

---

#### 2.3 Pair Programming Frequency
```python
# Co-authored commits (jeśli używacie Co-authored-by)
pair_programming_sessions = 0

for commit in commits:
    message = commit['message']
    if 'Co-authored-by:' in message:
        pair_programming_sessions += 1

        # Extract co-authors
        coauthors = extract_coauthors(message)

        for coauthor in coauthors:
            pair_frequency[(commit['author'], coauthor)] += 1

pair_programming_rate = pair_programming_sessions / len(commits) * 100
```

**Wartość:** Knowledge sharing, code quality

---

### 3. Metryki PR (Pull Request Metrics)

#### 3.1 PR Size Distribution
```python
# Już wspomniałem, ale szczegóły:
pr_sizes = {
    'xs': 0,    # < 10 lines
    's': 0,     # 10-50 lines
    'm': 0,     # 50-200 lines
    'l': 0,     # 200-500 lines
    'xl': 0     # > 500 lines
}

for pr in pull_requests:
    total_changes = pr.get('additions', 0) + pr.get('deletions', 0)

    if total_changes < 10:
        pr_sizes['xs'] += 1
    elif total_changes < 50:
        pr_sizes['s'] += 1
    elif total_changes < 200:
        pr_sizes['m'] += 1
    elif total_changes < 500:
        pr_sizes['l'] += 1
    else:
        pr_sizes['xl'] += 1

# Ideal distribution: most PRs should be S or M
ideal_ratio = (pr_sizes['s'] + pr_sizes['m']) / sum(pr_sizes.values()) * 100
```

**Wartość:** Review effectiveness, merge velocity

---

#### 3.2 PR Merge Time by Size
```python
# Korelacja wielkości PR vs czas do merge
merge_times_by_size = defaultdict(list)

for pr in pull_requests:
    if pr.get('merged_at'):
        size = calculate_pr_size(pr)
        merge_time = (pr['merged_at'] - pr['created_at']).total_seconds() / 3600  # hours

        merge_times_by_size[size].append(merge_time)

# Large PRs take longer?
for size, times in merge_times_by_size.items():
    print(f"{size}: avg {mean(times):.1f}h, median {median(times):.1f}h")
```

**Wartość:** Optimize PR size strategy

---

#### 3.3 Review Comments Density
```python
# Liczba komentarzy per 100 linii kodu
comment_density = []

for pr in pull_requests:
    total_changes = pr.get('additions', 0) + pr.get('deletions', 0)
    num_comments = len(pr.get('comments', []))

    if total_changes > 0:
        density = (num_comments / total_changes) * 100
        comment_density.append(density)

avg_density = mean(comment_density)

# High density = thorough review OR problematic code
# Low density = rubber stamping OR clean code
```

**Wartość:** Review quality assessment

---

#### 3.4 PR Approval Speed
```python
# Jak szybko PR dostaje pierwszą approval
first_approval_times = []

for pr in pull_requests:
    created = pr['created_at']
    approvals = sorted([a for a in pr.get('approvals', [])], key=lambda x: x['date'])

    if approvals:
        first_approval = approvals[0]['date']
        time_to_approval = (first_approval - created).total_seconds() / 3600
        first_approval_times.append(time_to_approval)

# By team
by_team = defaultdict(list)
for pr in pull_requests:
    team = get_team(pr['author'])
    # ... calculate time_to_approval
    by_team[team].append(time_to_approval)
```

**Wartość:** Review responsiveness, team efficiency

---

### 4. Metryki Bezpieczeństwa (Security Metrics)

#### 4.1 Secrets in Commits
```python
# Wykrywanie potencjalnych sekretów w commitach
secrets_pattern = re.compile(r'(password|api_key|secret|token)\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE)

commits_with_secrets = []

for commit in commits:
    diff = get_commit_diff(commit)

    for line in diff['added_lines']:
        if secrets_pattern.search(line):
            commits_with_secrets.append({
                'commit': commit['id'],
                'author': commit['author'],
                'line': line
            })

# Alert rate
alert_rate = len(commits_with_secrets) / len(commits) * 100
```

**Wartość:** Security compliance, risk prevention

---

#### 4.2 Dependency Updates
```python
# Jak często są aktualizowane zależności
dependency_updates = []

for commit in commits:
    message = commit['message'].lower()
    files = commit.get('files', [])

    # package.json, requirements.txt, pom.xml, etc.
    if any(f in files for f in ['package.json', 'requirements.txt', 'pom.xml', 'build.gradle']):
        if 'update' in message or 'upgrade' in message or 'bump' in message:
            dependency_updates.append(commit)

# Frequency
updates_per_month = len(dependency_updates) / months_in_period
```

**Wartość:** Security updates, technical debt management

---

### 5. Metryki Wydajności (Performance Metrics)

#### 5.1 Build Break Rate
```python
# Ile commitów powoduje broken build (z CI/CD webhooks)
broken_builds = []

for commit in commits:
    if 'ci_status' in commit.get('metadata', {}):
        if commit['metadata']['ci_status'] == 'failed':
            broken_builds.append(commit)

build_break_rate = len(broken_builds) / len(commits) * 100

# By author
by_author = defaultdict(lambda: {'total': 0, 'broken': 0})
for commit in commits:
    author = commit['author']
    by_author[author]['total'] += 1
    if commit in broken_builds:
        by_author[author]['broken'] += 1

# Who breaks builds most often?
break_rates = {
    author: (stats['broken'] / stats['total'] * 100)
    for author, stats in by_author.items()
}
```

**Wartość:** CI/CD health, developer discipline

---

#### 5.2 Hotfix Frequency
```python
# Commits do master/main poza normalnym flow
hotfix_commits = []

for commit in commits:
    branch = commit.get('branch', '')
    message = commit.get('message', '').lower()

    # Direct commits to master/main OR hotfix branches
    if branch in ['master', 'main'] or 'hotfix' in branch or 'hotfix' in message:
        hotfix_commits.append(commit)

hotfix_rate = len(hotfix_commits) / len(commits) * 100

# Trend over time
hotfix_by_month = defaultdict(int)
for commit in hotfix_commits:
    month = commit['date'][:7]
    hotfix_by_month[month] += 1

# Is hotfix rate increasing? (quality degrading)
```

**Wartość:** Process quality, planning effectiveness

---

### 6. Metryki Techniczne (Technical Metrics)

#### 6.1 Code Churn by File
```python
# Files z największym churnem (często zmieniane)
file_churn = defaultdict(lambda: {'commits': 0, 'lines_changed': 0, 'authors': set()})

for commit in commits:
    diff = get_commit_diff(commit)

    for file_change in diff['files']:
        file = file_change['path']
        file_churn[file]['commits'] += 1
        file_churn[file]['lines_changed'] += file_change['additions'] + file_change['deletions']
        file_churn[file]['authors'].add(commit['author'])

# Top 10 churned files
top_churn = sorted(
    file_churn.items(),
    key=lambda x: x[1]['lines_changed'],
    reverse=True
)[:10]

# High churn + multiple authors = refactoring candidate
```

**Wartość:** Refactoring priorities, code smell detection

---

#### 6.2 Dead Code Detection
```python
# Pliki które nie były zmieniane od > 6 miesięcy
stale_files = []

for file in all_files:
    last_modified = get_last_commit_date(file)
    age_days = (today - last_modified).days

    if age_days > 180:  # 6 months
        stale_files.append({
            'file': file,
            'last_modified': last_modified,
            'age_days': age_days
        })

# Potential dead code (or very stable code)
```

**Wartość:** Code cleanup, technical debt reduction

---

#### 6.3 Language Distribution Trends
```python
# Zmiana używanych języków programowania w czasie
language_by_month = defaultdict(lambda: defaultdict(int))

for commit in commits:
    month = commit['date'][:7]

    for file in commit.get('files', []):
        lang = detect_language(file)
        lines_changed = file.get('additions', 0) + file.get('deletions', 0)
        language_by_month[month][lang] += lines_changed

# Are we migrating from one tech stack to another?
# Is JavaScript growing? Is Java shrinking?
```

**Wartość:** Tech stack evolution tracking

---

## 🔗 Metryki Integracyjne (Cross-System)

### 1. Jira-Bitbucket Correlation

#### 1.1 Issue Resolution Time vs Commit Activity
```python
# Czy więcej commitów = szybsze rozwiązanie?
correlation_data = []

for issue in jira_issues:
    if issue['status'] in ['Done', 'Closed']:
        linked_commits = get_commits_for_issue(issue['key'])

        resolution_time = (issue['resolved'] - issue['created']).days
        num_commits = len(linked_commits)
        total_lines = sum(c.get('additions', 0) + c.get('deletions', 0) for c in linked_commits)

        correlation_data.append({
            'resolution_time': resolution_time,
            'num_commits': num_commits,
            'total_lines': total_lines
        })

# Calculate correlation coefficient
from scipy.stats import pearsonr
r_commits, p_commits = pearsonr(
    [d['resolution_time'] for d in correlation_data],
    [d['num_commits'] for d in correlation_data]
)

# More commits = longer resolution time? (scope creep)
# OR more commits = better decomposition?
```

---

#### 1.2 Code Review Time vs QA Rejection Rate
```python
# Czy szybkie code review prowadzą do więcej bugów?
review_quality_data = []

for pr in bitbucket_prs:
    issue_key = extract_issue_key(pr['title'])

    if issue_key:
        jira_issue = get_jira_issue(issue_key)

        # PR review time
        review_time = (pr['merged_at'] - pr['created_at']).total_seconds() / 3600

        # Was issue reopened after QA?
        was_reopened = any(t['to_status'] == 'Reopened' for t in jira_issue['transitions'])

        review_quality_data.append({
            'review_time': review_time,
            'was_reopened': was_reopened
        })

# Fast reviews + high reopen rate = rubber stamping
```

---

### 2. Developer Performance Index

#### 2.1 Combined Productivity Score
```python
# Composite metric z Jiry i Bitbucketa
developer_scores = {}

for developer in all_developers:
    # Jira metrics
    jira_metrics = {
        'issues_completed': count_completed_issues(developer),
        'avg_cycle_time': calculate_avg_cycle_time(developer),
        'reopen_rate': calculate_reopen_rate(developer)
    }

    # Bitbucket metrics
    bitbucket_metrics = {
        'commits': count_commits(developer),
        'lines_changed': sum_lines_changed(developer),
        'pr_reviews': count_pr_reviews(developer),
        'commit_quality': calculate_commit_quality_score(developer)
    }

    # Composite score (0-100)
    score = calculate_composite_score(jira_metrics, bitbucket_metrics)

    developer_scores[developer] = {
        'score': score,
        'jira': jira_metrics,
        'bitbucket': bitbucket_metrics
    }
```

---

## 📊 Podsumowanie - Top 20 Najważniejszych Metryk

### Tier 1: Must-Have (Krytyczne)

1. **Lead Time** (Jira) - end-to-end time
2. **Cycle Time** (Jira) - development time
3. **Throughput** (Jira) - issues per sprint
4. **Defect Escape Rate** (Jira) - quality
5. **PR Review Time** (Bitbucket) - collaboration
6. **Commit Quality Score** (Bitbucket) - code standards
7. **Issue-Commit Traceability** (Integration) - visibility

### Tier 2: Important (Istotne)

8. **WIP Limits** (Jira) - flow optimization
9. **Blocked Time Ratio** (Jira) - bottleneck detection
10. **Bug Reopen Rate** (Jira) - quality issues
11. **PR Size Distribution** (Bitbucket) - review effectiveness
12. **Code Churn** (Bitbucket) - stability
13. **Cross-Team Contributions** (Bitbucket) - knowledge sharing

### Tier 3: Nice-to-Have (Dodatkowe)

14. **First Time Pass Rate** (Jira) - development quality
15. **Context Switching Rate** (Jira) - productivity
16. **Pair Programming Frequency** (Bitbucket) - collaboration
17. **Build Break Rate** (Bitbucket) - CI/CD health
18. **Review Comments Density** (Bitbucket) - review thoroughness
19. **Developer Performance Index** (Integration) - holistic view
20. **Hotfix Frequency** (Bitbucket) - process stability

---

## 🚀 Quick Implementation Guide

### Start with These 5 Metrics (1 day implementation):

1. **Lead Time** - already have data
2. **WIP Count** - simple aggregation
3. **Blocked Time** - already tracking statuses
4. **Commit Quality** - regex patterns
5. **PR Size** - simple calculation

### Add These 5 Next (2-3 days):

6. **Bug Reopen Rate** - changelog parsing
7. **Code Churn** - file-level aggregation
8. **Review Time** - PR timestamps
9. **Issue-Commit Linking** - regex + join
10. **Throughput Trends** - time series

---

Wszystkie te metryki można zaimplementować używając istniejących danych z Jiry i Bitbucketa! 🎯
