"""
Report Generation Module.

This module generates HTML reports for commit and pull request statistics
with rankings and detailed breakdowns.

Classes:
    ReportGenerator: Main class for generating HTML reports
"""

from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path


class ReportGenerator:
    """
    Generator for commit statistics HTML reports.

    This class creates comprehensive HTML reports with:
    - Summary statistics
    - Top/bottom rankings by commits, changes, and PRs
    - Detailed per-user statistics tables
    - Optional commit details

    Attributes:
        user_stats: Per-user statistics dictionary
        rankings: Rankings dictionary
        summary: Summary statistics dictionary
        metadata: Report metadata (project, date range, etc.)

    Example:
        >>> generator = ReportGenerator(
        ...     user_stats=stats,
        ...     rankings=rankings,
        ...     summary=summary,
        ...     metadata={'project': 'PROJ', 'repository': 'repo'}
        ... )
        >>> generator.generate_html('output/report.html')
    """

    def __init__(
        self,
        user_stats: Dict[str, Dict],
        rankings: Dict,
        summary: Dict,
        metadata: Dict,
        detailed_commits: Optional[Dict[str, List[Dict]]] = None
    ):
        """
        Initialize the report generator.

        Args:
            user_stats: Per-user statistics from CommitAnalyzer
            rankings: Rankings from CommitAnalyzer
            summary: Summary statistics from CommitAnalyzer
            metadata: Report metadata (project, repository, dates, etc.)
            detailed_commits: Optional dict mapping usernames to commit lists
        """
        self.user_stats = user_stats
        self.rankings = rankings
        self.summary = summary
        self.metadata = metadata
        self.detailed_commits = detailed_commits or {}

    def generate_html(self, output_path: str):
        """
        Generate HTML report and save to file.

        Args:
            output_path: Path where HTML report will be saved

        Example:
            >>> generator.generate_html('reports/commit_stats.html')
        """
        html_content = self._build_html()

        # Ensure output directory exists
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Write HTML file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"\n✅ Report generated: {output_path}")

    def _build_html(self) -> str:
        """Build complete HTML content."""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bitbucket Commit Statistics - {self.metadata.get('project', 'Project')}</title>
    {self._get_css()}
</head>
<body>
    <div class="container">
        {self._build_header()}
        {self._build_summary()}
        {self._build_rankings()}
        {self._build_user_stats_table()}
        {self._build_detailed_commits()}
        {self._build_footer()}
    </div>
</body>
</html>"""

    def _get_css(self) -> str:
        """Get CSS styling for the report."""
        return """<style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            line-height: 1.6;
            padding: 20px;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
            overflow: hidden;
        }

        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }

        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }

        .header p {
            font-size: 1.1em;
            opacity: 0.9;
        }

        .section {
            padding: 40px;
            border-bottom: 1px solid #e0e0e0;
        }

        .section:last-child {
            border-bottom: none;
        }

        .section h2 {
            color: #667eea;
            font-size: 1.8em;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
        }

        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }

        .summary-card {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }

        .summary-card h3 {
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }

        .summary-card p {
            font-size: 2em;
            font-weight: bold;
            color: #333;
        }

        .rankings {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 30px;
            margin-top: 20px;
        }

        .ranking-box {
            background: #f9fafb;
            border-radius: 8px;
            padding: 20px;
            border: 2px solid #e0e0e0;
        }

        .ranking-box h3 {
            color: #667eea;
            font-size: 1.3em;
            margin-bottom: 15px;
            text-align: center;
        }

        .ranking-list {
            list-style: none;
        }

        .ranking-list li {
            padding: 12px;
            margin: 8px 0;
            background: white;
            border-radius: 6px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }

        .ranking-list li.top {
            border-left: 4px solid #10b981;
        }

        .ranking-list li.bottom {
            border-left: 4px solid #ef4444;
        }

        .ranking-list li .rank {
            font-weight: bold;
            color: #667eea;
            margin-right: 10px;
        }

        .ranking-list li .user {
            flex: 1;
        }

        .ranking-list li .value {
            font-weight: bold;
            font-size: 1.1em;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }

        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e0e0e0;
        }

        th {
            background: #667eea;
            color: white;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.9em;
            letter-spacing: 0.5px;
        }

        tr:hover {
            background: #f5f7fa;
        }

        .alias {
            color: #666;
            font-size: 0.9em;
            font-style: italic;
        }

        .number {
            font-weight: bold;
            color: #667eea;
        }

        .commit-details {
            background: #f9fafb;
            padding: 15px;
            border-radius: 6px;
            margin-top: 10px;
        }

        .commit-details h4 {
            color: #667eea;
            margin-bottom: 10px;
        }

        .commit-item {
            background: white;
            padding: 10px;
            margin: 5px 0;
            border-radius: 4px;
            border-left: 3px solid #667eea;
            font-size: 0.9em;
        }

        .commit-item .commit-id {
            font-family: monospace;
            color: #666;
        }

        .commit-item .commit-message {
            color: #333;
            margin: 5px 0;
        }

        .commit-item .commit-stats {
            color: #666;
            font-size: 0.85em;
        }

        .commit-stats .added { color: #10b981; }
        .commit-stats .deleted { color: #ef4444; }
        .commit-stats .modified { color: #f59e0b; }

        .footer {
            background: #f9fafb;
            padding: 20px;
            text-align: center;
            color: #666;
            font-size: 0.9em;
        }

        @media print {
            body {
                background: white;
                padding: 0;
            }
            .container {
                box-shadow: none;
            }
        }
    </style>"""

    def _build_header(self) -> str:
        """Build header section."""
        project = self.metadata.get('project', 'Unknown')
        repository = self.metadata.get('repository', 'Unknown')
        start_date = self.metadata.get('start_date', 'N/A')
        end_date = self.metadata.get('end_date', 'N/A')

        return f"""<div class="header">
        <h1>📊 Bitbucket Commit Statistics</h1>
        <p><strong>Project:</strong> {project} | <strong>Repository:</strong> {repository}</p>
        <p><strong>Period:</strong> {start_date} to {end_date}</p>
    </div>"""

    def _build_summary(self) -> str:
        """Build summary statistics section."""
        return f"""<div class="section">
        <h2>Summary Statistics</h2>
        <div class="summary-grid">
            <div class="summary-card">
                <h3>Total Users</h3>
                <p>{self.summary.get('total_users', 0)}</p>
            </div>
            <div class="summary-card">
                <h3>Total Commits</h3>
                <p>{self.summary.get('total_commits', 0)}</p>
            </div>
            <div class="summary-card">
                <h3>Total Changes</h3>
                <p>{self.summary.get('total_changes', 0):,}</p>
            </div>
            <div class="summary-card">
                <h3>Lines Added</h3>
                <p class="added">{self.summary.get('total_lines_added', 0):,}</p>
            </div>
            <div class="summary-card">
                <h3>Lines Deleted</h3>
                <p class="deleted">{self.summary.get('total_lines_deleted', 0):,}</p>
            </div>
            <div class="summary-card">
                <h3>Lines Modified</h3>
                <p class="modified">{self.summary.get('total_lines_modified', 0):,}</p>
            </div>
            <div class="summary-card">
                <h3>Pull Requests</h3>
                <p>{self.summary.get('total_pull_requests', 0)}</p>
            </div>
            <div class="summary-card">
                <h3>Avg Commits/User</h3>
                <p>{self.summary.get('average_commits_per_user', 0):.1f}</p>
            </div>
        </div>
    </div>"""

    def _build_rankings(self) -> str:
        """Build rankings section."""
        html = '<div class="section"><h2>Rankings</h2><div class="rankings">'

        # Top/Bottom by Commits
        html += self._build_ranking_box(
            "By Commits",
            self.rankings.get('by_commits', {}),
            "commits"
        )

        # Top/Bottom by Changes
        html += self._build_ranking_box(
            "By Total Changes",
            self.rankings.get('by_changes', {}),
            "lines"
        )

        # Top/Bottom by PRs
        html += self._build_ranking_box(
            "By Pull Requests",
            self.rankings.get('by_pull_requests', {}),
            "PRs"
        )

        html += '</div></div>'
        return html

    def _build_ranking_box(self, title: str, ranking: Dict, unit: str) -> str:
        """Build a single ranking box."""
        top = ranking.get('top', [])
        bottom = ranking.get('bottom', [])

        html = f'<div class="ranking-box"><h3>{title}</h3>'

        # Top 3
        if top:
            html += '<h4 style="color: #10b981; margin-top: 10px;">🏆 Top 3</h4><ul class="ranking-list">'
            for i, (user, value) in enumerate(top, 1):
                alias = self.user_stats.get(user, {}).get('alias', '')
                alias_text = f' ({alias})' if alias else ''
                html += f'''<li class="top">
                    <span class="rank">#{i}</span>
                    <span class="user">{user}{alias_text}</span>
                    <span class="value">{value:,} {unit}</span>
                </li>'''
            html += '</ul>'

        # Bottom 3
        if bottom:
            html += '<h4 style="color: #ef4444; margin-top: 20px;">📉 Bottom 3</h4><ul class="ranking-list">'
            for i, (user, value) in enumerate(bottom, 1):
                alias = self.user_stats.get(user, {}).get('alias', '')
                alias_text = f' ({alias})' if alias else ''
                html += f'''<li class="bottom">
                    <span class="rank">#{i}</span>
                    <span class="user">{user}{alias_text}</span>
                    <span class="value">{value:,} {unit}</span>
                </li>'''
            html += '</ul>'

        html += '</div>'
        return html

    def _build_user_stats_table(self) -> str:
        """Build detailed user statistics table."""
        html = '''<div class="section">
        <h2>Detailed User Statistics</h2>
        <table>
            <thead>
                <tr>
                    <th>User</th>
                    <th>Commits</th>
                    <th>Added</th>
                    <th>Deleted</th>
                    <th>Modified</th>
                    <th>Total Changes</th>
                    <th>Pull Requests</th>
                    <th>Files Changed</th>
                </tr>
            </thead>
            <tbody>'''

        # Sort by total changes (descending)
        sorted_users = sorted(
            self.user_stats.items(),
            key=lambda x: x[1]['total_changes'],
            reverse=True
        )

        for user, stats in sorted_users:
            alias = stats.get('alias', '')
            alias_text = f'<br><span class="alias">{alias}</span>' if alias else ''

            html += f'''<tr>
                <td>{user}{alias_text}</td>
                <td class="number">{stats['commits']}</td>
                <td class="number added">{stats['lines_added']:,}</td>
                <td class="number deleted">{stats['lines_deleted']:,}</td>
                <td class="number modified">{stats['lines_modified']:,}</td>
                <td class="number">{stats['total_changes']:,}</td>
                <td class="number">{stats['pull_requests']}</td>
                <td class="number">{stats['files_changed']}</td>
            </tr>'''

        html += '</tbody></table></div>'
        return html

    def _build_detailed_commits(self) -> str:
        """Build detailed commit lists (if available)."""
        if not self.detailed_commits:
            return ''

        html = '<div class="section"><h2>Detailed Commit Lists</h2>'

        for username, commits in self.detailed_commits.items():
            if not commits:
                continue

            alias = self.user_stats.get(username, {}).get('alias', '')
            alias_text = f' ({alias})' if alias else ''

            html += f'<div class="commit-details"><h4>{username}{alias_text} - {len(commits)} commits</h4>'

            for commit in commits[:50]:  # Limit to 50 commits per user
                html += f'''<div class="commit-item">
                    <div class="commit-id">{commit['short_id']}</div>
                    <div class="commit-message">{commit['message']}</div>
                    <div class="commit-stats">
                        {commit['date']} |
                        <span class="added">+{commit['added']}</span>
                        <span class="deleted">-{commit['deleted']}</span>
                        <span class="modified">~{commit['modified']}</span> |
                        {commit['files_changed']} files
                    </div>
                </div>'''

            html += '</div>'

        html += '</div>'
        return html

    def _build_footer(self) -> str:
        """Build footer section."""
        generated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return f'''<div class="footer">
        <p>Report generated on {generated_at}</p>
        <p>Bitbucket Analyzer | Commit Statistics Report</p>
    </div>'''
