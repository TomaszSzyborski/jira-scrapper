"""
Bitbucket Repository Report Generator Module.

This module generates HTML reports with visualizations for Bitbucket
repository analysis.

Classes:
    BitbucketReportGenerator: Main class for generating Bitbucket repository reports
"""

import json
from typing import Optional


class BitbucketReportGenerator:
    """
    Generator for Bitbucket repository analysis reports.

    Creates interactive HTML reports with Plotly.js visualizations showing
    commit activity, contributor statistics, and pull request metrics.

    Attributes:
        metadata (dict): Repository metadata
        metrics (dict): Analyzed repository metrics
        bitbucket_url (str): Bitbucket instance URL

    Example:
        >>> generator = BitbucketReportGenerator(metadata, metrics)
        >>> generator.generate_html('repo_report.html')
    """

    def __init__(
        self,
        metadata: dict,
        metrics: dict,
        bitbucket_url: Optional[str] = None
    ):
        """
        Initialize the report generator.

        Args:
            metadata: Repository metadata dictionary
            metrics: Metrics dictionary from BitbucketAnalyzer
            bitbucket_url: Bitbucket instance URL (optional)
        """
        self.metadata = metadata
        self.metrics = metrics
        self.bitbucket_url = bitbucket_url or ''

    def generate_html(self, output_file: str = 'bitbucket_report.html'):
        """
        Generate HTML report with interactive visualizations.

        Args:
            output_file: Path to output HTML file

        Returns:
            Path to generated report file
        """
        html_content = self._build_html()

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"Report generated: {output_file}")
        return output_file

    def _build_html(self) -> str:
        """
        Build complete HTML report.

        Returns:
            HTML string for the report
        """
        summary_section = self._generate_summary_section()
        commit_timeline_chart = self._generate_commit_timeline_chart()
        contributor_chart = self._generate_contributor_chart()
        pr_metrics_section = self._generate_pr_metrics_section()

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bitbucket Repository Report - {self.metadata.get('repository', 'Repository')}</title>
    <script src="https://cdn.plot.ly/plotly-2.20.0.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #0052CC 0%, #2684FF 50%, #4C9AFF 100%);
            min-height: 100vh;
            padding: 20px;
            color: #fff;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}

        .header {{
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 16px;
            padding: 30px;
            margin-bottom: 30px;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }}

        h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
        }}

        .subtitle {{
            font-size: 1.1em;
            opacity: 0.9;
        }}

        .section {{
            background: white;
            border-radius: 16px;
            padding: 30px;
            margin-bottom: 20px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
            color: #172B4D;
        }}

        .section h2 {{
            color: #0052CC;
            margin-bottom: 20px;
            font-size: 1.8em;
            border-bottom: 3px solid #2684FF;
            padding-bottom: 10px;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}

        .stat-card {{
            background: linear-gradient(135deg, #F4F5F7 0%, #EBECF0 100%);
            padding: 20px;
            border-radius: 12px;
            border-left: 4px solid #2684FF;
        }}

        .stat-value {{
            font-size: 2.5em;
            font-weight: bold;
            color: #0052CC;
            margin-bottom: 5px;
        }}

        .stat-label {{
            font-size: 0.9em;
            color: #5E6C84;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .chart-container {{
            margin: 30px 0;
            background: #FAFBFC;
            padding: 20px;
            border-radius: 12px;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}

        th {{
            background: #0052CC;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }}

        td {{
            padding: 12px;
            border-bottom: 1px solid #DFE1E6;
        }}

        tr:hover {{
            background: #F4F5F7;
        }}

        .info-box {{
            background: #E6FCFF;
            border-left: 4px solid #00B8D9;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
        }}

        .info-box p {{
            color: #0052CC;
            margin: 5px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Bitbucket Repository Report</h1>
            <p class="subtitle">{self.metadata.get('project', '')}/{self.metadata.get('repository', '')}</p>
        </div>

        {summary_section}
        {commit_timeline_chart}
        {contributor_chart}
        {pr_metrics_section}

    </div>
</body>
</html>
"""
        return html

    def _generate_summary_section(self) -> str:
        """Generate summary statistics section."""
        total_commits = self.metrics.get('total_commits', 0)
        total_contributors = self.metrics.get('total_contributors', 0)
        total_prs = self.metrics.get('total_pull_requests', 0)

        activity = self.metrics.get('activity_summary', {})
        busiest_day = activity.get('busiest_day', 'N/A')
        busiest_day_commits = activity.get('busiest_day_commits', 0)
        avg_commits = activity.get('avg_commits_per_day', 0)

        date_range = self.metrics.get('date_range', {})
        start_date = date_range.get('start', 'N/A')
        end_date = date_range.get('end', 'N/A')

        return f"""
        <div class="section">
            <h2>📈 Summary Statistics</h2>

            <div class="info-box">
                <p><strong>Analysis Period:</strong> {start_date} to {end_date}</p>
                <p><strong>Project:</strong> {self.metadata.get('project', 'N/A')}</p>
                <p><strong>Repository:</strong> {self.metadata.get('repository', 'N/A')}</p>
            </div>

            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value">{total_commits}</div>
                    <div class="stat-label">Total Commits</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{total_contributors}</div>
                    <div class="stat-label">Contributors</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{total_prs}</div>
                    <div class="stat-label">Pull Requests</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{avg_commits:.1f}</div>
                    <div class="stat-label">Avg Commits/Day</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{busiest_day_commits}</div>
                    <div class="stat-label">Busiest Day Commits</div>
                </div>
            </div>

            {self._generate_busiest_contributor_info()}
        </div>
        """

    def _generate_busiest_contributor_info(self) -> str:
        """Generate busiest contributor information."""
        activity = self.metrics.get('activity_summary', {})
        contributor = activity.get('busiest_contributor')

        if not contributor:
            return ""

        return f"""
        <div class="info-box">
            <p><strong>Most Active Contributor:</strong> {contributor.get('name', 'N/A')}
            ({contributor.get('email', 'N/A')}) with {contributor.get('commits', 0)} commits</p>
        </div>
        """

    def _generate_commit_timeline_chart(self) -> str:
        """Generate commit timeline bar chart."""
        timeline = self.metrics.get('commit_timeline', {})

        if not timeline:
            return ""

        dates = list(timeline.keys())
        counts = list(timeline.values())

        chart_data = {
            'x': dates,
            'y': counts,
            'type': 'bar',
            'marker': {'color': '#2684FF'},
            'name': 'Commits'
        }

        layout = {
            'title': 'Commit Timeline',
            'xaxis': {'title': 'Date'},
            'yaxis': {'title': 'Number of Commits'},
            'plot_bgcolor': '#FAFBFC',
            'paper_bgcolor': '#FAFBFC',
            'font': {'family': 'Arial, sans-serif'}
        }

        return f"""
        <div class="section">
            <h2>📅 Commit Timeline</h2>
            <div class="chart-container">
                <div id="timelineChart"></div>
            </div>
        </div>

        <script>
            var timelineData = [{json.dumps(chart_data)}];
            var timelineLayout = {json.dumps(layout)};
            Plotly.newPlot('timelineChart', timelineData, timelineLayout, {{responsive: true}});
        </script>
        """

    def _generate_contributor_chart(self) -> str:
        """Generate contributor statistics chart and table."""
        contributor_stats = self.metrics.get('contributor_stats', [])

        if not contributor_stats:
            return ""

        # Top 10 contributors for chart
        top_contributors = contributor_stats[:10]
        names = [c['name'] or c['email'] for c in top_contributors]
        commits = [c['commits'] for c in top_contributors]

        chart_data = {
            'x': names,
            'y': commits,
            'type': 'bar',
            'marker': {'color': '#0052CC'},
            'name': 'Commits'
        }

        layout = {
            'title': 'Top 10 Contributors',
            'xaxis': {'title': 'Contributor'},
            'yaxis': {'title': 'Number of Commits'},
            'plot_bgcolor': '#FAFBFC',
            'paper_bgcolor': '#FAFBFC',
            'font': {'family': 'Arial, sans-serif'}
        }

        # Generate table rows
        table_rows = ""
        for i, contributor in enumerate(contributor_stats[:20], 1):
            table_rows += f"""
            <tr>
                <td>{i}</td>
                <td>{contributor.get('name', 'N/A')}</td>
                <td>{contributor.get('email', 'N/A')}</td>
                <td>{contributor.get('commits', 0)}</td>
                <td>{contributor.get('first_commit_date', 'N/A')}</td>
                <td>{contributor.get('last_commit_date', 'N/A')}</td>
            </tr>
            """

        return f"""
        <div class="section">
            <h2>👥 Contributors</h2>
            <div class="chart-container">
                <div id="contributorChart"></div>
            </div>

            <h3 style="margin-top: 30px; color: #0052CC;">Top 20 Contributors</h3>
            <table>
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Name</th>
                        <th>Email</th>
                        <th>Commits</th>
                        <th>First Commit</th>
                        <th>Last Commit</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
        </div>

        <script>
            var contributorData = [{json.dumps(chart_data)}];
            var contributorLayout = {json.dumps(layout)};
            Plotly.newPlot('contributorChart', contributorData, contributorLayout, {{responsive: true}});
        </script>
        """

    def _generate_pr_metrics_section(self) -> str:
        """Generate pull request metrics section."""
        pr_metrics = self.metrics.get('pr_metrics', {})

        if pr_metrics.get('total', 0) == 0:
            return ""

        total = pr_metrics.get('total', 0)
        merged = pr_metrics.get('merged', 0)
        declined = pr_metrics.get('declined', 0)
        open_prs = pr_metrics.get('open', 0)
        avg_merge_time = pr_metrics.get('avg_time_to_merge_hours')

        # PR state distribution pie chart
        labels = ['Merged', 'Declined', 'Open']
        values = [merged, declined, open_prs]
        colors = ['#36B37E', '#FF5630', '#2684FF']

        pie_data = {
            'labels': labels,
            'values': values,
            'type': 'pie',
            'marker': {'colors': colors},
            'textinfo': 'label+percent',
            'textposition': 'outside'
        }

        pie_layout = {
            'title': 'Pull Request Distribution',
            'plot_bgcolor': '#FAFBFC',
            'paper_bgcolor': '#FAFBFC',
            'font': {'family': 'Arial, sans-serif'}
        }

        avg_merge_display = f"{avg_merge_time:.1f} hours" if avg_merge_time else "N/A"

        return f"""
        <div class="section">
            <h2>🔀 Pull Request Metrics</h2>

            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value">{total}</div>
                    <div class="stat-label">Total PRs</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{merged}</div>
                    <div class="stat-label">Merged</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{declined}</div>
                    <div class="stat-label">Declined</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{open_prs}</div>
                    <div class="stat-label">Open</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{avg_merge_display}</div>
                    <div class="stat-label">Avg Time to Merge</div>
                </div>
            </div>

            <div class="chart-container">
                <div id="prDistChart"></div>
            </div>
        </div>

        <script>
            var prDistData = [{json.dumps(pie_data)}];
            var prDistLayout = {json.dumps(pie_layout)};
            Plotly.newPlot('prDistChart', prDistData, prDistLayout, {{responsive: true}});
        </script>
        """
