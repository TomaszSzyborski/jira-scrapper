"""
Xray Test Execution Report Generator Module.

This module generates HTML reports for Xray test execution data with
interactive Plotly.js visualizations.

Classes:
    XrayReportGenerator: Main class for generating HTML reports
"""

import json
from datetime import datetime
from pathlib import Path


class XrayReportGenerator:
    """
    HTML report generator for Xray test execution data.

    Creates comprehensive HTML reports displaying test execution analysis
    with interactive visualizations.

    Attributes:
        metadata (dict): Project metadata
        test_metrics (dict): Test metrics from XrayAnalyzer

    Example:
        >>> generator = XrayReportGenerator(metadata, test_metrics)
        >>> report_path = generator.generate_html('xray_report.html')
    """

    def __init__(self, metadata: dict, test_metrics: dict, jira_url: str = None):
        """
        Initialize report generator.

        Args:
            metadata: Project metadata dictionary
            test_metrics: Test metrics from XrayAnalyzer.calculate_test_metrics()
            jira_url: Optional Jira instance URL for creating ticket links
        """
        self.metadata = metadata
        self.test_metrics = test_metrics
        self.jira_url = jira_url

    def generate_html(self, output_file: str = 'xray_test_report.html') -> str:
        """
        Generate comprehensive HTML report with test execution visualizations.

        Args:
            output_file: Output HTML file path

        Returns:
            Absolute path to the generated HTML report
        """
        timeline_data = self.test_metrics.get('timeline', {}).get('daily_data', [])

        # Prepare timeline chart data
        dates = [d['date'] for d in timeline_data]
        passed_counts = [d['passed'] for d in timeline_data]
        failed_counts = [d['failed'] for d in timeline_data]
        other_counts = [d['other'] for d in timeline_data]

        # Status distribution
        status_dist = self.test_metrics.get('status_distribution', {})
        statuses = list(status_dist.keys())
        status_counts = [status_dist[s] for s in statuses]

        # Duration stats
        duration_stats = self.test_metrics.get('test_duration_stats', {})
        avg_duration_min = duration_stats.get('avg_duration_seconds', 0) / 60
        total_duration_hours = duration_stats.get('total_duration_hours', 0)

        html_content = f"""<!DOCTYPE html>
<html lang="pl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Raport Testów Xray - {self.metadata['project']}</title>
<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
<style>
* {{
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}}
body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
    padding: 20px;
}}
.container {{
    max-width: 1600px;
    margin: 0 auto;
}}
.header {{
    background: white;
    border-radius: 12px;
    padding: 30px;
    margin-bottom: 20px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}}
h1 {{
    color: #2d3748;
    font-size: 2.5em;
    margin-bottom: 10px;
}}
.metadata {{
    color: #718096;
    font-size: 0.95em;
    line-height: 1.6;
}}
.stats {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 15px;
    margin-bottom: 20px;
}}
.stat-card {{
    background: white;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}}
.stat-card.success {{
    border-left: 4px solid #10b981;
}}
.stat-card.error {{
    border-left: 4px solid #ef4444;
}}
.stat-card.info {{
    border-left: 4px solid #3b82f6;
}}
.stat-label {{
    color: #718096;
    font-size: 0.85em;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 8px;
}}
.stat-value {{
    color: #2d3748;
    font-size: 2em;
    font-weight: 700;
}}
.chart-container {{
    background: white;
    border-radius: 12px;
    padding: 30px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    margin-bottom: 20px;
}}
.chart-title {{
    color: #2d3748;
    font-size: 1.3em;
    margin-bottom: 15px;
    font-weight: 600;
}}
.footer {{
    background: white;
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    color: #718096;
    font-size: 0.9em;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}}
</style>
</head>
<body>
<div class="container">
<div class="header">
    <h1>🧪 Raport Testów Xray</h1>
    <div class="metadata">
        <strong>Projekt:</strong> {self.metadata['project']}<br>
        <strong>Pobrano:</strong> {self.metadata.get('fetched_at', 'N/A')}<br>
        <strong>Łącznie wykonań testów:</strong> {self.test_metrics.get('total_executions', 0)}<br>
        <strong>Łącznie testów:</strong> {self.test_metrics.get('total_test_runs', 0)}
    </div>
</div>

<div class="stats">
    <div class="stat-card success">
        <div class="stat-label">Testy Zakończone Sukcesem</div>
        <div class="stat-value">{self.test_metrics.get('pass_count', 0)}</div>
        <div class="stat-label">({self.test_metrics.get('pass_rate', 0):.1f}%)</div>
    </div>
    <div class="stat-card error">
        <div class="stat-label">Testy Zakończone Niepowodzeniem</div>
        <div class="stat-value">{self.test_metrics.get('fail_count', 0)}</div>
        <div class="stat-label">({self.test_metrics.get('fail_rate', 0):.1f}%)</div>
    </div>
    <div class="stat-card info">
        <div class="stat-label">Średni Czas Testu</div>
        <div class="stat-value">{avg_duration_min:.1f}m</div>
    </div>
    <div class="stat-card info">
        <div class="stat-label">Łączny Czas Testów</div>
        <div class="stat-value">{total_duration_hours:.1f}h</div>
    </div>
</div>

<div class="chart-container">
    <div class="chart-title">📊 Trend Wykonań Testów w Czasie</div>
    <div id="timeline-chart"></div>
</div>

<div class="chart-container">
    <div class="chart-title">📈 Rozkład Statusów Testów</div>
    <div id="status-chart"></div>
</div>

<div class="footer">
    Wygenerowano {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Xray Test Report v1.0
</div>
</div>

<script>
// Timeline chart
const timelineData = [
    {{
        x: {json.dumps(dates)},
        y: {json.dumps(passed_counts)},
        name: 'Passed',
        type: 'bar',
        marker: {{ color: '#10b981' }}
    }},
    {{
        x: {json.dumps(dates)},
        y: {json.dumps(failed_counts)},
        name: 'Failed',
        type: 'bar',
        marker: {{ color: '#ef4444' }}
    }},
    {{
        x: {json.dumps(dates)},
        y: {json.dumps(other_counts)},
        name: 'Other',
        type: 'bar',
        marker: {{ color: '#94a3b8' }}
    }}
];

const timelineLayout = {{
    barmode: 'stack',
    xaxis: {{ title: 'Data' }},
    yaxis: {{ title: 'Liczba Testów' }},
    height: 400
}};

Plotly.newPlot('timeline-chart', timelineData, timelineLayout, {{responsive: true}});

// Status distribution pie chart
const statusData = [{{
    labels: {json.dumps(statuses)},
    values: {json.dumps(status_counts)},
    type: 'pie',
    marker: {{
        colors: ['#10b981', '#ef4444', '#f59e0b', '#3b82f6', '#94a3b8']
    }}
}}];

const statusLayout = {{
    height: 400
}};

Plotly.newPlot('status-chart', statusData, statusLayout, {{responsive: true}});
</script>
</body>
</html>
"""

        # Write to file
        output_path = Path(output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        return str(output_path.absolute())
