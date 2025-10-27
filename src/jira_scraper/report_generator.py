"""HTML report generation module."""

from datetime import datetime
from typing import Dict, Any, List, Optional
import json
import polars as pl
from .issue_trends_chart import IssueTrendsChart
from .xray_test_chart import XrayTestChart
from .bug_tracking_chart import BugTrackingChart
from .test_execution_cumulative_chart import TestExecutionCumulativeChart
from .open_issues_status_chart import OpenIssuesStatusChart


class ReportGenerator:
    """Generates HTML reports from analyzed Jira data."""

    def __init__(self, project_name: str, start_date: str, end_date: str, jira_url: str = ""):
        """
        Initialize report generator.

        Args:
            project_name: Jira project key
            start_date: Analysis start date
            end_date: Analysis end date
            jira_url: Base URL of Jira instance for generating ticket links
        """
        self.project_name = project_name
        self.start_date = start_date
        self.end_date = end_date
        self.jira_url = jira_url
        # Clean up URL (remove trailing slash)
        if self.jira_url and self.jira_url.endswith("/"):
            self.jira_url = self.jira_url[:-1]
        self.report_generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def generate_html_report(
        self,
        summary_stats: Dict[str, Any],
        flow_metrics: Dict[str, Any],
        cycle_metrics: Dict[str, Any],
        temporal_trends: pl.DataFrame,
        tickets: Optional[List[Dict[str, Any]]] = None,
        xray_label: Optional[str] = None,
        test_label: Optional[str] = None,
        output_file: str = "jira_report.html",
    ) -> str:
        """
        Generate comprehensive HTML report.

        Args:
            summary_stats: Summary statistics dictionary
            flow_metrics: Flow analysis metrics
            cycle_metrics: Cycle time metrics
            temporal_trends: Temporal trends DataFrame
            tickets: Raw ticket data for generating new charts
            xray_label: Optional label for filtering Xray test executions (legacy)
            test_label: Optional label for filtering test executions
            output_file: Output file path

        Returns:
            Path to generated HTML file
        """
        html = self._build_html_structure(
            summary_stats,
            flow_metrics,
            cycle_metrics,
            temporal_trends,
            tickets,
            xray_label,
            test_label,
        )

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html)

        print(f"Report generated: {output_file}")
        return output_file

    def _build_html_structure(
        self,
        summary_stats: Dict[str, Any],
        flow_metrics: Dict[str, Any],
        cycle_metrics: Dict[str, Any],
        temporal_trends: pl.DataFrame,
        tickets: Optional[List[Dict[str, Any]]] = None,
        xray_label: Optional[str] = None,
        test_label: Optional[str] = None,
    ) -> str:
        """
        Build complete HTML structure.

        Args:
            summary_stats: Summary statistics
            flow_metrics: Flow metrics
            cycle_metrics: Cycle metrics
            temporal_trends: Temporal trends data
            tickets: Raw ticket data for generating new charts
            xray_label: Optional label for filtering Xray test executions (legacy)
            test_label: Optional label for filtering test executions

        Returns:
            Complete HTML string
        """
        # Generate new chart sections if tickets data is provided
        issue_trends_section = ""
        xray_section = ""
        bug_tracking_section = ""
        test_execution_section = ""
        open_issues_section = ""

        if tickets:
            # Generate issue trends charts
            trends_chart = IssueTrendsChart(tickets)
            combined_chart_html = trends_chart.create_combined_chart(
                self.start_date,
                self.end_date,
                "Daily Issue Trends (Raised, Closed, Open)"
            )
            issue_trends_section = f"""
        <div class="section">
            <h2 class="section-title">Daily Issue Trends</h2>
            <div class="chart-container">
                {combined_chart_html}
            </div>
        </div>"""

            # Check for Xray test executions (legacy)
            test_executions = [t for t in tickets if t.get("issue_type") in ["Test Execution", "Test"]]
            if test_executions:
                xray_chart = XrayTestChart(test_executions, xray_label)
                xray_report_html = xray_chart.generate_complete_report()
                xray_section = f"""
        <div class="section">
            <h2 class="section-title">Xray Test Execution Progress (Legacy)</h2>
            {xray_report_html}
        </div>"""

            # Generate bug tracking chart
            bugs = [t for t in tickets if t.get("issue_type", "").lower() in ["bug", "defect"]]
            if bugs:
                bug_chart = BugTrackingChart(tickets, self.jira_url)
                bug_chart_html = bug_chart.create_bug_tracking_chart(
                    self.start_date,
                    self.end_date,
                    "Daily Bug Tracking - Created vs Closed"
                )
                bug_details_html = bug_chart.get_bug_details_table(
                    self.start_date,
                    self.end_date
                )
                bug_stats = bug_chart.get_summary_statistics(self.start_date, self.end_date)

                bug_tracking_section = f"""
        <div class="section">
            <h2 class="section-title">Bug Tracking</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value">{bug_stats['total_created']}</div>
                    <div class="stat-label">Total Bugs Created</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{bug_stats['total_closed']}</div>
                    <div class="stat-label">Total Bugs Closed</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{bug_stats['avg_created_per_day']:.1f}</div>
                    <div class="stat-label">Avg Created/Day</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{bug_stats['final_open_bugs']}</div>
                    <div class="stat-label">Currently Open Bugs</div>
                </div>
            </div>
            <div class="chart-container">
                {bug_chart_html}
            </div>
            {bug_details_html}
        </div>"""

            # Generate test execution cumulative chart
            if test_executions:
                # Use test_label if provided, otherwise fall back to xray_label
                label_filter = test_label or xray_label
                test_exec_chart = TestExecutionCumulativeChart(
                    test_executions,
                    self.jira_url,
                    target_label=label_filter
                )
                test_exec_chart_html = test_exec_chart.create_cumulative_chart(
                    self.start_date,
                    self.end_date
                )
                test_exec_drilldown_html = test_exec_chart.get_test_execution_drilldown(
                    self.start_date,
                    self.end_date
                )
                test_exec_summary = test_exec_chart.get_current_status_summary(self.end_date)

                label_display = f" (Label: {label_filter})" if label_filter else ""

                test_execution_section = f"""
        <div class="section">
            <h2 class="section-title">Test Execution Progress{label_display}</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value">{test_exec_summary['total']}</div>
                    <div class="stat-label">Total Test Executions</div>
                </div>
                <div class="stat-card" style="border-left: 4px solid #2ecc71;">
                    <div class="stat-value">{test_exec_summary['passed']}</div>
                    <div class="stat-label">Passed</div>
                </div>
                <div class="stat-card" style="border-left: 4px solid #e74c3c;">
                    <div class="stat-value">{test_exec_summary['failed']}</div>
                    <div class="stat-label">Failed</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{test_exec_summary['coverage_percent']}%</div>
                    <div class="stat-label">Test Coverage</div>
                </div>
            </div>
            <div class="chart-container">
                {test_exec_chart_html}
            </div>
            {test_exec_drilldown_html}
        </div>"""

            # Generate open issues status chart
            open_issues_chart = OpenIssuesStatusChart(tickets, self.jira_url)
            open_issues_chart_html = open_issues_chart.create_open_issues_chart(
                self.start_date,
                self.end_date,
                "Open Issues by Status Category"
            )
            open_issues_stats = open_issues_chart.get_summary_statistics(
                self.start_date,
                self.end_date
            )

            open_issues_section = f"""
        <div class="section">
            <h2 class="section-title">Open Issues Tracking</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value">{open_issues_stats['avg_open']:.1f}</div>
                    <div class="stat-label">Avg Open Issues</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{open_issues_stats['max_open']}</div>
                    <div class="stat-label">Max Open Issues</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{open_issues_stats['final_open']}</div>
                    <div class="stat-label">Currently Open</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{open_issues_stats['avg_in_progress']:.1f}</div>
                    <div class="stat-label">Avg In Progress</div>
                </div>
            </div>
            <div class="chart-container">
                {open_issues_chart_html}
            </div>
        </div>"""

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Jira Report - {self.project_name}</title>
    {self._get_styles()}
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
</head>
<body>
    <div class="container">
        {self._build_header()}
        {self._build_executive_summary(summary_stats, cycle_metrics)}
        {issue_trends_section}
        {open_issues_section}
        {bug_tracking_section}
        {test_execution_section}
        {xray_section}
        {self._build_flow_analysis(flow_metrics, self.jira_url)}
        {self._build_temporal_trends(temporal_trends)}
        {self._build_cycle_metrics(cycle_metrics)}
        {self._build_status_distribution(summary_stats)}
        {self._build_footer()}
    </div>
    {self._get_scripts(temporal_trends, flow_metrics)}
</body>
</html>"""

    def _get_styles(self) -> str:
        """Get CSS styles for the report."""
        return """
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            color: #333;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }

        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }

        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
            font-weight: 700;
        }

        .header .subtitle {
            font-size: 1.1rem;
            opacity: 0.9;
        }

        .section {
            padding: 40px;
            border-bottom: 1px solid #e0e0e0;
        }

        .section:last-child {
            border-bottom: none;
        }

        .section-title {
            font-size: 1.8rem;
            margin-bottom: 20px;
            color: #667eea;
            font-weight: 600;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .stat-card {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            padding: 25px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }

        .stat-card h3 {
            font-size: 0.9rem;
            color: #666;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .stat-card .value {
            font-size: 2.5rem;
            font-weight: 700;
            color: #667eea;
        }

        .stat-card .subvalue {
            font-size: 0.9rem;
            color: #888;
            margin-top: 5px;
        }

        .chart-container {
            margin: 30px 0;
            padding: 20px;
            background: #f9f9f9;
            border-radius: 8px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }

        table th {
            background: #667eea;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }

        table td {
            padding: 12px;
            border-bottom: 1px solid #e0e0e0;
        }

        table tr:hover {
            background: #f5f5f5;
        }

        .footer {
            padding: 20px 40px;
            background: #f5f5f5;
            text-align: center;
            color: #666;
            font-size: 0.9rem;
        }

        .metric-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px 0;
            border-bottom: 1px solid #e0e0e0;
        }

        .metric-label {
            font-weight: 600;
            color: #555;
        }

        .metric-value {
            font-size: 1.2rem;
            color: #667eea;
            font-weight: 700;
        }

        /* Flow pattern drilldown styles */
        .pattern-row {
            margin: 15px 0;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            overflow: hidden;
            background: white;
        }

        .pattern-header {
            padding: 15px 20px;
            background: #f8f9fa;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 15px;
            transition: background 0.2s;
        }

        .pattern-header:hover {
            background: #e9ecef;
        }

        .pattern-arrow {
            color: #667eea;
            font-size: 0.8rem;
            transition: transform 0.3s;
            display: inline-block;
            min-width: 15px;
        }

        .pattern-arrow.expanded {
            transform: rotate(90deg);
        }

        .pattern-text {
            flex: 1;
            font-weight: 600;
            color: #333;
            font-size: 1rem;
        }

        .pattern-count {
            background: #667eea;
            color: white;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85rem;
            font-weight: 600;
        }

        .pattern-details {
            padding: 0;
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.3s ease-out, padding 0.3s;
        }

        .pattern-details.expanded {
            padding: 20px;
            max-height: 2000px;
        }

        .ticket-list h4 {
            margin: 0 0 15px 0;
            color: #667eea;
            font-size: 1.1rem;
        }

        .ticket-table {
            width: 100%;
            border-collapse: collapse;
            margin: 0;
            font-size: 0.9rem;
        }

        .ticket-table th {
            background: #667eea;
            color: white;
            padding: 10px;
            text-align: left;
            font-weight: 600;
            font-size: 0.85rem;
        }

        .ticket-table td {
            padding: 10px;
            border-bottom: 1px solid #e0e0e0;
        }

        .ticket-table tr:hover {
            background: #f8f9fa;
        }

        .ticket-link {
            color: #667eea;
            text-decoration: none;
            font-weight: 600;
            transition: color 0.2s;
        }

        .ticket-link:hover {
            color: #764ba2;
            text-decoration: underline;
        }

        .ticket-table tr:last-child td {
            border-bottom: none;
        }
    </style>"""

    def _build_header(self) -> str:
        """Build report header."""
        return f"""
    <div class="header">
        <h1>Jira Analytics Report</h1>
        <div class="subtitle">
            Project: {self.project_name} |
            Period: {self.start_date} to {self.end_date} |
            Generated: {self.report_generated_at}
        </div>
    </div>"""

    def _build_executive_summary(
        self,
        summary_stats: Dict[str, Any],
        cycle_metrics: Dict[str, Any]
    ) -> str:
        """Build executive summary section."""
        total = summary_stats.get("total_tickets", 0)
        resolved = summary_stats.get("resolved_tickets", 0)
        in_progress = summary_stats.get("in_progress_tickets", 0)
        completion_rate = (resolved / total * 100) if total > 0 else 0

        return f"""
    <div class="section">
        <h2 class="section-title">Executive Summary</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <h3>Total Tickets</h3>
                <div class="value">{total}</div>
            </div>
            <div class="stat-card">
                <h3>Resolved</h3>
                <div class="value">{resolved}</div>
                <div class="subvalue">{completion_rate:.1f}% completion rate</div>
            </div>
            <div class="stat-card">
                <h3>In Progress</h3>
                <div class="value">{in_progress}</div>
            </div>
            <div class="stat-card">
                <h3>Avg Lead Time</h3>
                <div class="value">{cycle_metrics.get('avg_lead_time', 0):.1f}</div>
                <div class="subvalue">days</div>
            </div>
            <div class="stat-card">
                <h3>Avg Cycle Time</h3>
                <div class="value">{cycle_metrics.get('avg_cycle_time', 0):.1f}</div>
                <div class="subvalue">days</div>
            </div>
            <div class="stat-card">
                <h3>Throughput</h3>
                <div class="value">{cycle_metrics.get('throughput', 0)}</div>
                <div class="subvalue">tickets completed</div>
            </div>
        </div>
    </div>"""

    def _build_flow_analysis(self, flow_metrics: Dict[str, Any], jira_url: str = "") -> str:
        """Build flow analysis section with ticket drilldown."""
        if "error" in flow_metrics:
            return f"""
    <div class="section">
        <h2 class="section-title">Ticket Flow Analysis</h2>
        <p>No transition data available for analysis.</p>
    </div>"""

        regressions = flow_metrics.get("regressions", {})
        patterns = flow_metrics.get("flow_patterns", [])

        patterns_html = ""
        if patterns:
            patterns_html = '<h3>Most Common Flow Patterns</h3>'
            patterns_html += '<p style="font-size: 0.9rem; color: #666; margin-bottom: 15px;">Click on a pattern to see the tickets</p>'

            for idx, pattern in enumerate(patterns[:10]):
                pattern_text = pattern['pattern']
                pattern_count = pattern['count']
                tickets = pattern.get('tickets', [])

                # Create ticket list HTML
                ticket_list_html = ""
                if tickets:
                    ticket_list_html = '<div class="ticket-list">'
                    ticket_list_html += f'<h4>Tickets following pattern: {pattern_text} ({len(tickets)} tickets)</h4>'
                    ticket_list_html += '<table class="ticket-table">'
                    ticket_list_html += '<tr><th>Key</th><th>Summary</th><th>Status</th><th>Priority</th><th>Assignee</th></tr>'

                    for ticket in tickets:
                        ticket_key = ticket['key']
                        ticket_link = f"{jira_url}/browse/{ticket_key}" if jira_url else "#"
                        ticket_summary = ticket['summary'][:80] + "..." if len(ticket['summary']) > 80 else ticket['summary']

                        ticket_list_html += f'''
                        <tr>
                            <td><a href="{ticket_link}" target="_blank" class="ticket-link">{ticket_key}</a></td>
                            <td>{ticket_summary}</td>
                            <td>{ticket['status']}</td>
                            <td>{ticket['priority'] or 'N/A'}</td>
                            <td>{ticket['assignee'] or 'Unassigned'}</td>
                        </tr>'''

                    ticket_list_html += '</table></div>'

                # Create collapsible pattern row
                patterns_html += f'''
                <div class="pattern-row">
                    <div class="pattern-header" onclick="togglePattern('pattern-{idx}')">
                        <span class="pattern-arrow">▶</span>
                        <span class="pattern-text">{pattern_text}</span>
                        <span class="pattern-count">{pattern_count} tickets</span>
                    </div>
                    <div id="pattern-{idx}" class="pattern-details" style="display: none;">
                        {ticket_list_html}
                    </div>
                </div>
                '''

        return f"""
    <div class="section">
        <h2 class="section-title">Ticket Flow Analysis</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <h3>Total Transitions</h3>
                <div class="value">{flow_metrics.get('total_transitions', 0)}</div>
            </div>
            <div class="stat-card">
                <h3>Regressions</h3>
                <div class="value">{regressions.get('count', 0)}</div>
                <div class="subvalue">{regressions.get('bounce_rate', 0):.1%} bounce rate</div>
            </div>
        </div>
        <div class="chart-container">
            <div id="flowChart"></div>
        </div>
        {patterns_html}
    </div>"""

    def _build_temporal_trends(self, temporal_trends: pl.DataFrame) -> str:
        """Build temporal trends section."""
        return """
    <div class="section">
        <h2 class="section-title">Temporal Trends</h2>
        <div class="chart-container">
            <div id="trendsChart"></div>
        </div>
    </div>"""

    def _build_cycle_metrics(self, cycle_metrics: Dict[str, Any]) -> str:
        """Build cycle metrics section."""
        return f"""
    <div class="section">
        <h2 class="section-title">Cycle Metrics</h2>
        <div class="metric-row">
            <span class="metric-label">Average Lead Time</span>
            <span class="metric-value">{cycle_metrics.get('avg_lead_time', 0):.2f} days</span>
        </div>
        <div class="metric-row">
            <span class="metric-label">Median Lead Time</span>
            <span class="metric-value">{cycle_metrics.get('median_lead_time', 0):.2f} days</span>
        </div>
        <div class="metric-row">
            <span class="metric-label">Average Cycle Time</span>
            <span class="metric-value">{cycle_metrics.get('avg_cycle_time', 0):.2f} days</span>
        </div>
        <div class="metric-row">
            <span class="metric-label">Median Cycle Time</span>
            <span class="metric-value">{cycle_metrics.get('median_cycle_time', 0):.2f} days</span>
        </div>
    </div>"""

    def _build_status_distribution(self, summary_stats: Dict[str, Any]) -> str:
        """Build status distribution section."""
        status_dist = summary_stats.get("status_distribution", {})

        rows = ""
        for status, count in status_dist.items():
            rows += f"<tr><td>{status}</td><td>{count}</td></tr>"

        return f"""
    <div class="section">
        <h2 class="section-title">Status Distribution</h2>
        <table>
            <tr>
                <th>Status</th>
                <th>Count</th>
            </tr>
            {rows}
        </table>
    </div>"""

    def _build_footer(self) -> str:
        """Build report footer."""
        return """
    <div class="footer">
        Generated by Jira Scraper & Analytics Tool
    </div>"""

    def _get_scripts(self, temporal_trends: pl.DataFrame, flow_metrics: Dict[str, Any]) -> str:
        """Generate JavaScript for interactive charts."""
        # Prepare temporal trends data
        trends_data = []
        if not temporal_trends.is_empty():
            for row in temporal_trends.iter_rows(named=True):
                trends_data.append({
                    "date": row["date"].strftime("%Y-%m-%d"),
                    "created": row["tickets_created"],
                    "resolved": row["tickets_resolved"],
                    "in_progress": row["tickets_in_progress"],
                })

        # Prepare flow data
        transitions = flow_metrics.get("transitions", [])

        return f"""
    <script>
        // Temporal trends chart
        const trendsData = {json.dumps(trends_data)};

        const createdTrace = {{
            x: trendsData.map(d => d.date),
            y: trendsData.map(d => d.created),
            name: 'Created (Cumulative)',
            type: 'scatter',
            mode: 'lines',
            line: {{color: '#667eea', width: 3}}
        }};

        const resolvedTrace = {{
            x: trendsData.map(d => d.date),
            y: trendsData.map(d => d.resolved),
            name: 'Resolved (Cumulative)',
            type: 'scatter',
            mode: 'lines',
            line: {{color: '#51cf66', width: 3}}
        }};

        const inProgressTrace = {{
            x: trendsData.map(d => d.date),
            y: trendsData.map(d => d.in_progress),
            name: 'In Progress',
            type: 'scatter',
            mode: 'lines',
            line: {{color: '#ff6b6b', width: 3}}
        }};

        const trendsLayout = {{
            title: 'Ticket Trends Over Time',
            xaxis: {{title: 'Date'}},
            yaxis: {{title: 'Number of Tickets'}},
            hovermode: 'x unified'
        }};

        Plotly.newPlot('trendsChart', [createdTrace, resolvedTrace, inProgressTrace], trendsLayout);

        // Flow chart (Sankey diagram)
        const transitions = {json.dumps(transitions[:20])};  // Top 20 transitions

        if (transitions.length > 0) {{
            const nodes = [];
            const nodeMap = new Map();
            let nodeIndex = 0;

            transitions.forEach(t => {{
                if (!nodeMap.has(t.from_status)) {{
                    nodeMap.set(t.from_status, nodeIndex++);
                    nodes.push(t.from_status);
                }}
                if (!nodeMap.has(t.to_status)) {{
                    nodeMap.set(t.to_status, nodeIndex++);
                    nodes.push(t.to_status);
                }}
            }});

            const flowData = [{{
                type: "sankey",
                node: {{
                    pad: 15,
                    thickness: 20,
                    line: {{color: "black", width: 0.5}},
                    label: nodes
                }},
                link: {{
                    source: transitions.map(t => nodeMap.get(t.from_status)),
                    target: transitions.map(t => nodeMap.get(t.to_status)),
                    value: transitions.map(t => t.count)
                }}
            }}];

            const flowLayout = {{
                title: "Status Transition Flow",
                height: 600
            }};

            Plotly.newPlot('flowChart', flowData, flowLayout);
        }}

        // Toggle pattern drilldown
        function togglePattern(patternId) {{
            const details = document.getElementById(patternId);
            const arrow = details.previousElementSibling.querySelector('.pattern-arrow');

            if (details.style.display === 'none' || details.style.display === '') {{
                details.style.display = 'block';
                details.classList.add('expanded');
                arrow.classList.add('expanded');
            }} else {{
                details.style.display = 'none';
                details.classList.remove('expanded');
                arrow.classList.remove('expanded');
            }}
        }}
    </script>"""
