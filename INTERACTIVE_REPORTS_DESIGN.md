# Interactive Jira Reports - Live Filtering

System raportowania z interaktywnymi filtrami pozwalającymi na dynamiczne przefiltrowanie danych bez ponownego odpytywania Jiry.

---

## 🎯 Funkcjonalność

### Możliwości Filtrowania

1. **Filtry Statusów**
   - Checkboxy dla każdego unikalnego statusu
   - "Select All" / "Deselect All"
   - Live update wykresów

2. **Filtry Labelek**
   - Multi-select dropdown
   - Możliwość wyboru wielu labelek
   - AND / OR logic

3. **Filtry Dat**
   - Date range picker
   - Presets (Last 30 days, Last Quarter, etc.)
   - Custom range

4. **Filtry Typu Zadania**
   - Bug / Story / Task / etc.
   - Multiple selection

---

## 🏗️ Architektura

### 1. Data Embedding

Wszystkie issues są osadzone w HTML jako JSON:

```javascript
const rawIssuesData = [
    {
        "key": "PROJ-123",
        "type": "Bug",
        "status": "Done",
        "created": "2024-01-15",
        "resolved": "2024-01-20",
        "labels": ["Sprint-1", "Backend"],
        "assignee": "john.doe",
        "transitions": [
            {"from": "New", "to": "In Progress", "date": "2024-01-16", "duration_hours": 24},
            {"from": "In Progress", "to": "Done", "date": "2024-01-20", "duration_hours": 96}
        ]
    },
    // ... więcej issues
];
```

### 2. Filter State Management

```javascript
const filterState = {
    statuses: new Set(['Done', 'In Progress', 'New']),  // Aktywne statusy
    labels: new Set(['Sprint-1']),                      // Wybrane labelki
    issueTypes: new Set(['Bug', 'Story']),             // Typy zadań
    dateRange: {
        start: '2024-01-01',
        end: '2024-12-31'
    }
};
```

### 3. Filtering Pipeline

```javascript
function filterIssues(rawIssues, filters) {
    return rawIssues.filter(issue => {
        // Status filter
        if (!filters.statuses.has(issue.status)) return false;

        // Label filter (OR logic)
        if (filters.labels.size > 0) {
            const hasLabel = issue.labels.some(label => filters.labels.has(label));
            if (!hasLabel) return false;
        }

        // Issue type filter
        if (!filters.issueTypes.has(issue.type)) return false;

        // Date range filter
        if (issue.created < filters.dateRange.start) return false;
        if (issue.created > filters.dateRange.end) return false;

        return true;
    });
}
```

### 4. Metrics Recalculation

```javascript
function recalculateMetrics(filteredIssues) {
    // Flow patterns
    const flowPatterns = calculateFlowPatterns(filteredIssues);

    // Timeline data
    const timeline = calculateTimeline(filteredIssues);

    // Time in status
    const timeInStatus = calculateTimeInStatus(filteredIssues);

    return {
        flowPatterns,
        timeline,
        timeInStatus,
        totalIssues: filteredIssues.length
    };
}
```

### 5. Chart Redrawing

```javascript
function updateAllCharts(metrics) {
    // Update timeline chart
    Plotly.react('timeline-chart',
        createTimelineData(metrics.timeline),
        timelineLayout
    );

    // Update Sankey diagram
    Plotly.react('sankey-chart',
        createSankeyData(metrics.flowPatterns),
        sankeyLayout
    );

    // Update open bugs chart
    Plotly.react('open-chart',
        createOpenBugsData(metrics.timeline),
        openBugsLayout
    );

    // Update summary stats
    updateSummaryStats(metrics);
}
```

---

## 📝 Implementacja

### Step 1: Modify Reporter to Embed Data

```python
# jira_analyzer/interactive_reporter.py
class InteractiveReportGenerator(ReportGenerator):
    """Enhanced report generator with interactive filtering."""

    def _embed_raw_data(self) -> str:
        """Embed all issues as JSON for client-side filtering."""
        # Prepare simplified issue data
        simplified_issues = []

        for issue in self.all_issues:  # Not just filtered_issues!
            simplified_issues.append({
                'key': issue['key'],
                'type': issue['type'],
                'status': issue['status'],
                'created': issue['created'].split('T')[0],
                'resolved': issue.get('resolved', '').split('T')[0] if issue.get('resolved') else None,
                'labels': issue.get('labels', []),
                'assignee': issue.get('assignee', 'Unassigned'),
                'priority': issue.get('priority', ''),
                'summary': issue.get('summary', ''),
                'transitions': self._extract_transitions(issue)
            })

        return f"const rawIssuesData = {json.dumps(simplified_issues, ensure_ascii=False)};"

    def _extract_transitions(self, issue) -> list:
        """Extract transition data from issue changelog."""
        transitions = []

        if 'changelog' in issue:
            for entry in issue['changelog']:
                for item in entry.get('items', []):
                    if item.get('field') == 'status':
                        transitions.append({
                            'from': item.get('fromString', ''),
                            'to': item.get('toString', ''),
                            'date': entry['created'].split('T')[0],
                            'author': entry['author']['displayName']
                        })

        return transitions
```

### Step 2: Add Filter UI

```html
<!-- Filter Control Panel -->
<div class="filter-panel">
    <h3>🔍 Filtry Interaktywne</h3>

    <!-- Status Filters -->
    <div class="filter-section">
        <h4>Statusy</h4>
        <div id="status-filters">
            <!-- Dynamically generated checkboxes -->
        </div>
        <button onclick="selectAllStatuses()">Zaznacz wszystkie</button>
        <button onclick="deselectAllStatuses()">Odznacz wszystkie</button>
    </div>

    <!-- Label Filters -->
    <div class="filter-section">
        <h4>Labelki</h4>
        <select id="label-filter" multiple>
            <!-- Dynamically generated options -->
        </select>
    </div>

    <!-- Issue Type Filters -->
    <div class="filter-section">
        <h4>Typ Zadania</h4>
        <div id="type-filters">
            <!-- Checkboxes for Bug, Story, Task, etc. -->
        </div>
    </div>

    <!-- Date Range Filter -->
    <div class="filter-section">
        <h4>Zakres Dat</h4>
        <label>Od: <input type="date" id="date-start" onchange="applyFilters()"></label>
        <label>Do: <input type="date" id="date-end" onchange="applyFilters()"></label>

        <!-- Presets -->
        <button onclick="setDatePreset('last30days')">Ostatnie 30 dni</button>
        <button onclick="setDatePreset('lastQuarter')">Ostatni kwartał</button>
        <button onclick="setDatePreset('all')">Wszystkie</button>
    </div>

    <!-- Apply/Reset -->
    <div class="filter-actions">
        <button class="btn-primary" onclick="applyFilters()">Zastosuj Filtry</button>
        <button class="btn-secondary" onclick="resetFilters()">Resetuj</button>
    </div>

    <!-- Filter Summary -->
    <div class="filter-summary">
        <strong>Filtrowane zadania:</strong> <span id="filtered-count">0</span> / <span id="total-count">0</span>
    </div>
</div>
```

### Step 3: Client-Side Filtering Logic

```javascript
// Global state
let currentFilters = {
    statuses: new Set(),
    labels: new Set(),
    issueTypes: new Set(),
    dateRange: { start: null, end: null }
};

let filteredIssues = [];

// Initialize filters on page load
function initializeFilters() {
    // Extract all unique statuses
    const allStatuses = [...new Set(rawIssuesData.map(i => i.status))];
    const statusContainer = document.getElementById('status-filters');

    allStatuses.forEach(status => {
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.id = `status-${status}`;
        checkbox.value = status;
        checkbox.checked = true;  // All selected by default
        checkbox.onchange = () => applyFilters();

        const label = document.createElement('label');
        label.htmlFor = `status-${status}`;
        label.textContent = status;

        const div = document.createElement('div');
        div.appendChild(checkbox);
        div.appendChild(label);
        statusContainer.appendChild(div);

        currentFilters.statuses.add(status);
    });

    // Extract all unique labels
    const allLabels = [...new Set(rawIssuesData.flatMap(i => i.labels))];
    const labelSelect = document.getElementById('label-filter');

    allLabels.forEach(label => {
        const option = document.createElement('option');
        option.value = label;
        option.textContent = label;
        labelSelect.appendChild(option);
    });

    // Extract all issue types
    const allTypes = [...new Set(rawIssuesData.map(i => i.type))];
    const typeContainer = document.getElementById('type-filters');

    allTypes.forEach(type => {
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.id = `type-${type}`;
        checkbox.value = type;
        checkbox.checked = true;
        checkbox.onchange = () => applyFilters();

        const label = document.createElement('label');
        label.htmlFor = `type-${type}`;
        label.textContent = type;

        const div = document.createElement('div');
        div.appendChild(checkbox);
        div.appendChild(label);
        typeContainer.appendChild(div);

        currentFilters.issueTypes.add(type);
    });

    // Set initial date range
    const dates = rawIssuesData.map(i => i.created).filter(d => d);
    if (dates.length > 0) {
        currentFilters.dateRange.start = dates.sort()[0];
        currentFilters.dateRange.end = dates.sort().reverse()[0];

        document.getElementById('date-start').value = currentFilters.dateRange.start;
        document.getElementById('date-end').value = currentFilters.dateRange.end;
    }

    // Initial filter application
    applyFilters();
}

// Apply all filters
function applyFilters() {
    // Update filter state from UI
    updateFilterState();

    // Filter issues
    filteredIssues = rawIssuesData.filter(issue => {
        // Status filter
        if (!currentFilters.statuses.has(issue.status)) return false;

        // Label filter (if any labels selected)
        if (currentFilters.labels.size > 0) {
            const hasMatchingLabel = issue.labels.some(label =>
                currentFilters.labels.has(label)
            );
            if (!hasMatchingLabel) return false;
        }

        // Issue type filter
        if (!currentFilters.issueTypes.has(issue.type)) return false;

        // Date range filter
        if (currentFilters.dateRange.start && issue.created < currentFilters.dateRange.start) {
            return false;
        }
        if (currentFilters.dateRange.end && issue.created > currentFilters.dateRange.end) {
            return false;
        }

        return true;
    });

    // Update UI
    updateFilteredCount();

    // Recalculate metrics
    const metrics = recalculateMetrics(filteredIssues);

    // Redraw all charts
    updateAllCharts(metrics);
}

// Update filter state from UI
function updateFilterState() {
    // Update statuses
    currentFilters.statuses.clear();
    document.querySelectorAll('#status-filters input:checked').forEach(cb => {
        currentFilters.statuses.add(cb.value);
    });

    // Update labels
    currentFilters.labels.clear();
    const labelSelect = document.getElementById('label-filter');
    Array.from(labelSelect.selectedOptions).forEach(option => {
        currentFilters.labels.add(option.value);
    });

    // Update issue types
    currentFilters.issueTypes.clear();
    document.querySelectorAll('#type-filters input:checked').forEach(cb => {
        currentFilters.issueTypes.add(cb.value);
    });

    // Update date range
    currentFilters.dateRange.start = document.getElementById('date-start').value;
    currentFilters.dateRange.end = document.getElementById('date-end').value;
}

// Recalculate all metrics from filtered issues
function recalculateMetrics(issues) {
    // Calculate flow patterns
    const flowPatterns = {};
    issues.forEach(issue => {
        issue.transitions.forEach(transition => {
            const key = `${transition.from} → ${transition.to}`;
            flowPatterns[key] = (flowPatterns[key] || 0) + 1;
        });
    });

    // Calculate timeline (daily created/closed)
    const timeline = {};
    issues.forEach(issue => {
        // Created
        if (!timeline[issue.created]) {
            timeline[issue.created] = { created: 0, closed: 0 };
        }
        timeline[issue.created].created++;

        // Resolved
        if (issue.resolved) {
            if (!timeline[issue.resolved]) {
                timeline[issue.resolved] = { created: 0, closed: 0 };
            }
            timeline[issue.resolved].closed++;
        }
    });

    // Calculate time in status
    const timeInStatus = {};
    issues.forEach(issue => {
        issue.transitions.forEach(transition => {
            if (!timeInStatus[transition.to]) {
                timeInStatus[transition.to] = [];
            }
            // Calculate duration (simplified)
            timeInStatus[transition.to].push(1);  // Placeholder
        });
    });

    return {
        flowPatterns,
        timeline,
        timeInStatus,
        totalIssues: issues.length
    };
}

// Helper functions
function selectAllStatuses() {
    document.querySelectorAll('#status-filters input').forEach(cb => cb.checked = true);
    applyFilters();
}

function deselectAllStatuses() {
    document.querySelectorAll('#status-filters input').forEach(cb => cb.checked = false);
    applyFilters();
}

function resetFilters() {
    // Reset to initial state (all selected)
    document.querySelectorAll('#status-filters input').forEach(cb => cb.checked = true);
    document.querySelectorAll('#type-filters input').forEach(cb => cb.checked = true);
    document.getElementById('label-filter').selectedIndex = -1;

    // Reset date range
    const dates = rawIssuesData.map(i => i.created).filter(d => d);
    document.getElementById('date-start').value = dates.sort()[0];
    document.getElementById('date-end').value = dates.sort().reverse()[0];

    applyFilters();
}

function setDatePreset(preset) {
    const today = new Date();
    let startDate, endDate;

    switch(preset) {
        case 'last30days':
            startDate = new Date(today.setDate(today.getDate() - 30));
            endDate = new Date();
            break;
        case 'lastQuarter':
            startDate = new Date(today.setMonth(today.getMonth() - 3));
            endDate = new Date();
            break;
        case 'all':
            const dates = rawIssuesData.map(i => i.created).filter(d => d);
            startDate = new Date(dates.sort()[0]);
            endDate = new Date(dates.sort().reverse()[0]);
            break;
    }

    document.getElementById('date-start').value = startDate.toISOString().split('T')[0];
    document.getElementById('date-end').value = endDate.toISOString().split('T')[0];

    applyFilters();
}

function updateFilteredCount() {
    document.getElementById('filtered-count').textContent = filteredIssues.length;
    document.getElementById('total-count').textContent = rawIssuesData.length;
}

// Initialize on page load
window.addEventListener('DOMContentLoaded', initializeFilters);
```

---

## 🎨 CSS Styling

```css
.filter-panel {
    background: white;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 20px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.filter-panel h3 {
    margin-bottom: 20px;
    color: #2d3748;
}

.filter-section {
    margin-bottom: 20px;
    padding-bottom: 15px;
    border-bottom: 1px solid #e2e8f0;
}

.filter-section:last-of-type {
    border-bottom: none;
}

.filter-section h4 {
    margin-bottom: 10px;
    color: #4a5568;
    font-size: 0.95em;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.filter-section input[type="checkbox"] {
    margin-right: 8px;
}

.filter-section label {
    margin-right: 15px;
    cursor: pointer;
}

.filter-section select {
    width: 100%;
    padding: 8px;
    border: 1px solid #cbd5e1;
    border-radius: 4px;
    min-height: 100px;
}

.filter-section input[type="date"] {
    padding: 6px 10px;
    border: 1px solid #cbd5e1;
    border-radius: 4px;
    margin-right: 10px;
}

.filter-actions {
    display: flex;
    gap: 10px;
    margin-top: 20px;
}

.btn-primary {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 6px;
    cursor: pointer;
    font-weight: 600;
}

.btn-primary:hover {
    opacity: 0.9;
}

.btn-secondary {
    background: #e2e8f0;
    color: #2d3748;
    border: none;
    padding: 10px 20px;
    border-radius: 6px;
    cursor: pointer;
}

.btn-secondary:hover {
    background: #cbd5e1;
}

.filter-summary {
    margin-top: 15px;
    padding: 10px;
    background: #f7fafc;
    border-radius: 4px;
    text-align: center;
}

.filter-summary strong {
    color: #2d3748;
}

.filter-summary span {
    color: #667eea;
    font-weight: bold;
    font-size: 1.1em;
}

/* Collapsible filter panel */
.filter-panel.collapsed .filter-section,
.filter-panel.collapsed .filter-actions {
    display: none;
}

.filter-toggle {
    cursor: pointer;
    user-select: none;
}

.filter-toggle:hover {
    opacity: 0.7;
}
```

---

## 🚀 Usage Example

### Generate Interactive Report

```bash
# Standard report generation - now includes interactive filtering
python main.py --project PROJ --issue-types Bug Story --report

# The generated HTML will have:
# - All raw issue data embedded
# - Interactive filter panel
# - Dynamic chart updates
```

### User Workflow

1. **Open Report** - `bug_flow_report.html`
2. **See Filter Panel** at top of page
3. **Adjust Filters**:
   - Uncheck "Closed" status → see only active bugs
   - Select label "Sprint-5" → see only current sprint
   - Change date range → see specific period
4. **Click "Zastosuj Filtry"** → Charts instantly update!
5. **No Jira Query** - Everything runs client-side

---

## 📊 Performance Considerations

### Data Size Limits

- **< 1000 issues**: Instant filtering, no issues
- **1000-5000 issues**: ~1-2s filtering time, acceptable
- **> 5000 issues**: Consider pagination or server-side filtering

### Optimization Techniques

```javascript
// Debounce filter application
let filterTimeout;
function applyFiltersDebounced() {
    clearTimeout(filterTimeout);
    filterTimeout = setTimeout(() => applyFilters(), 300);
}

// Use Web Workers for heavy calculations
const worker = new Worker('metrics-calculator.js');
worker.postMessage({ issues: filteredIssues });
worker.onmessage = (e) => {
    const metrics = e.data;
    updateAllCharts(metrics);
};
```

---

## ✅ Benefits

1. **No Server Round-trips** - instant filtering
2. **Offline Capable** - report works without internet
3. **Exploratory Analysis** - users can slice data any way
4. **Shareable** - single HTML file with all data
5. **No Additional Tools** - works in any browser

---

## 🔄 Integration with Existing System

### Modify main.py

```python
# main.py
if args.report:
    from jira_analyzer.interactive_reporter import InteractiveReportGenerator

    generator = InteractiveReportGenerator(
        report_metadata,
        flow_metrics,
        all_issues=cached_data['issues'],  # Pass ALL issues
        start_date=args.start_date,
        end_date=args.end_date,
        jira_url=os.getenv('JIRA_URL'),
        label=args.label
    )
    report_path = generator.generate_html(args.report_output)
```

---

## 📝 Next Steps

1. **Implement InteractiveReportGenerator** class
2. **Test with real data** (100-1000 issues)
3. **Add loading indicators** for large datasets
4. **Implement advanced filters**:
   - Assignee filter
   - Priority filter
   - Component filter
5. **Add export functionality** (filtered data to CSV)
6. **Add filter presets** (save/load filter combinations)

---

**Ready to implement!** This design provides a complete blueprint for interactive, client-side filtering without requiring additional Jira queries. 🎯
