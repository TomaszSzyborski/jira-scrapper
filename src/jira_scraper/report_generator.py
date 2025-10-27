"""HTML report generation module."""

from datetime import datetime
from typing import Dict, Any, List, Optional
import json
import polars as pl
from .issue_trends_chart import IssueTrendsChart
from .xray_test_chart import XrayTestChart


class ReportGenerator:
    """Generates HTML reports from analyzed Jira data."""

    def __init__(self, project_name: str, start_date: str, end_date: str):
        """
        Initialize report generator.

        Args:
            project_name: Jira project key
            start_date: Analysis start date
            end_date: Analysis end date
        """
        self.project_name = project_name
        self.start_date = start_date
        self.end_date = end_date
        self.report_generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def generate_html_report(
        self,
        summary_stats: Dict[str, Any],
        flow_metrics: Dict[str, Any],
        cycle_metrics: Dict[str, Any],
        temporal_trends: pl.DataFrame,
        tickets: Optional[List[Dict[str, Any]]] = None,
        xray_label: Optional[str] = None,
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
            xray_label: Optional label for filtering Xray test executions
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
    ) -> str:
        """
        Build complete HTML structure.

        Args:
            summary_stats: Summary statistics
            flow_metrics: Flow metrics
            cycle_metrics: Cycle metrics
            temporal_trends: Temporal trends data
            tickets: Raw ticket data for generating new charts
            xray_label: Optional label for filtering Xray test executions

        Returns:
            Complete HTML string
        """
        # Generate new chart sections if tickets data is provided
        issue_trends_section = ""
        xray_section = ""

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

            # Check for Xray test executions
            test_executions = [t for t in tickets if t.get("issue_type") in ["Test Execution", "Test"]]
            if test_executions:
                xray_chart = XrayTestChart(test_executions, xray_label)
                xray_report_html = xray_chart.generate_complete_report()
                xray_section = f"""
        <div class="section">
            <h2 class="section-title">Xray Test Execution Progress</h2>
            {xray_report_html}
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
        {xray_section}
        {self._build_flow_analysis(flow_metrics)}
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

    def _build_flow_analysis(self, flow_metrics: Dict[str, Any]) -> str:
        """Build flow analysis section."""
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
            patterns_html = "<h3>Most Common Flow Patterns</h3><table><tr><th>Pattern</th><th>Count</th></tr>"
            for pattern in patterns[:10]:
                patterns_html += f"<tr><td>{pattern['pattern']}</td><td>{pattern['count']}</td></tr>"
            patterns_html += "</table>"

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
    </script>"""
