"""
HTML Report Generation Module.

This module generates comprehensive HTML reports with interactive Plotly.js
visualizations for bug flow analysis, including timeline trends, Sankey diagrams,
and rework pattern detection.

Classes:
    ReportGenerator: Main class for generating HTML reports
"""

import json
from datetime import datetime
from pathlib import Path

from .models import is_correct_flow


class ReportGenerator:
    """
    HTML report generator with Plotly.js visualizations.

    This class creates comprehensive HTML reports displaying bug flow analysis
    with multiple interactive visualizations including:
    - Created vs Closed timeline with trend lines
    - Open bugs timeline with trend analysis and drilldown
    - Sankey diagram showing status flow (with loop highlighting)
    - Time in status statistics table
    - Rework pattern analysis

    Attributes:
        metadata (dict): Project metadata (project name, dates, fetch time)
        flow_metrics (dict): Flow analysis metrics from FlowAnalyzer

    Example:
        >>> generator = ReportGenerator(metadata, flow_metrics)
        >>> report_path = generator.generate_html('report.html')
        >>> print(f"Report saved to {report_path}")
    """

    def __init__(self, metadata: dict, flow_metrics: dict, start_date: str = None, end_date: str = None, jira_url: str = None, label: str = None, flow_metrics_no_label: dict = None):
        """
        Initialize report generator.

        Args:
            metadata: Project metadata dictionary containing:
                - project: Project key
                - fetched_at: ISO timestamp of data fetch
            flow_metrics: Flow analysis metrics from FlowAnalyzer.calculate_flow_metrics()
            start_date: Optional start date for filtering (YYYY-MM-DD)
            end_date: Optional end date for filtering (YYYY-MM-DD)
            jira_url: Optional Jira instance URL for creating ticket links
            label: Optional label filter that was applied
            flow_metrics_no_label: Optional metrics calculated without label filter (for comparison/toggle)
        """
        self.metadata = metadata
        self.flow_metrics = flow_metrics
        self.start_date = start_date
        self.end_date = end_date
        self.jira_url = jira_url
        self.label = label
        self.flow_metrics_no_label = flow_metrics_no_label

    def _calculate_trend(self, x_values: list, y_values: list) -> list:
        """
        Calculate simple linear trend line using least squares regression.

        Uses the formula: y = slope * x + intercept
        Where: slope = (n*Σxy - Σx*Σy) / (n*Σx² - (Σx)²)
               intercept = (Σy - slope*Σx) / n

        Args:
            x_values: List of x-axis values (used for length only)
            y_values: List of y-axis values to fit trend line to

        Returns:
            List of trend line y-values matching length of input

        Example:
            >>> gen = ReportGenerator({}, {})
            >>> trend = gen._calculate_trend([1, 2, 3], [2, 4, 5])
            >>> print(trend)
            [2.0, 3.5, 5.0]

        Note:
            If fewer than 2 data points, returns flat line at first y-value.
        """
        if len(x_values) < 2:
            return [y_values[0]] * len(y_values) if y_values else []

        n = len(x_values)
        sum_x = sum(range(n))
        sum_y = sum(y_values)
        sum_xy = sum(i * y for i, y in enumerate(y_values))
        sum_x2 = sum(i * i for i in range(n))

        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        intercept = (sum_y - slope * sum_x) / n

        return [slope * i + intercept for i in range(n)]

    def _generate_label_toggle_html(self) -> str:
        """
        Generate HTML for label filter toggle switch.

        Returns:
            HTML string for toggle control, or empty string if no label filter active
        """
        if not self.label or not self.flow_metrics_no_label:
            return ""

        total_with_label = self.flow_metrics.get('total_issues', 0)
        total_without_label = self.flow_metrics_no_label.get('total_issues', 0)

        return f'''
            <div class="label-filter-container">
                <label class="toggle-switch">
                    <input type="checkbox" id="labelFilterToggle" checked onchange="toggleLabelFilter()">
                    <span class="toggle-label">Filtruj po etykiecie: "{self.label}"</span>
                </label>
                <div class="filter-info">
                    <span id="filter-status">✓ Filtr aktywny: {total_with_label} błędów</span> |
                    <span style="color: #94a3b8;">Bez filtra: {total_without_label} błędów</span>
                </div>
            </div>
        '''

    def _prepare_dataset_json(self, metrics: dict, dates_actual, created_counts, closed_counts, open_counts,
                              created_trend, closed_trend, open_trend, dates_trend, current_open_bugs,
                              flow_patterns, all_statuses) -> str:
        """
        Prepare chart data as JSON string for JavaScript.

        Args:
            metrics: Flow metrics dictionary
            dates_actual, created_counts, etc.: Chart data arrays
            flow_patterns, all_statuses: Flow diagram data

        Returns:
            JSON string containing all chart data
        """
        # Prepare Sankey diagram data
        sankey_labels = list(all_statuses)
        sankey_sources = []
        sankey_targets = []
        sankey_values = []
        sankey_colors = []

        for pattern in flow_patterns:
            from_status = pattern['from']
            to_status = pattern['to']

            if from_status in sankey_labels and to_status in sankey_labels:
                sankey_sources.append(sankey_labels.index(from_status))
                sankey_targets.append(sankey_labels.index(to_status))
                sankey_values.append(pattern['count'])

                # All flows are gray now
                sankey_colors.append('rgba(128, 128, 128, 0.4)')

        dataset = {
            'total_issues': metrics.get('total_issues', 0),
            'total_transitions': metrics.get('total_transitions', 0),
            'current_open_bugs': current_open_bugs,
            'dates_actual': dates_actual,
            'created_counts': created_counts,
            'closed_counts': closed_counts,
            'open_counts': open_counts,
            'created_trend': created_trend,
            'closed_trend': closed_trend,
            'open_trend': open_trend,
            'dates_trend': dates_trend,
            'sankey_nodes': {
                'label': sankey_labels,
                'color': ['#cbd5e1'] * len(sankey_labels)
            },
            'sankey_links': {
                'source': sankey_sources,
                'target': sankey_targets,
                'value': sankey_values,
                'color': sankey_colors
            }
        }

        return json.dumps(dataset)

    def generate_html(self, output_file: str = 'jira_flow_report.html') -> str:
        """
        Generate comprehensive HTML report with multiple visualizations.

        Creates a complete HTML report with:
        1. Summary statistics cards (bugs, transitions, loops)
        2. Created vs Closed timeline chart with trend lines
        3. Open bugs timeline bar chart with trend analysis and drilldown
        4. Sankey flow diagram (red highlighting for loops)
        5. Time in status table with averages
        6. Rework patterns table showing top 10 loops

        Args:
            output_file: Output HTML file path (default: 'jira_flow_report.html')

        Returns:
            Absolute path to the generated HTML report

        Example:
            >>> generator = ReportGenerator(metadata, metrics)
            >>> path = generator.generate_html('my_report.html')
            >>> print(f"Report: {path}")

        Note:
            The report loads Plotly.js from CDN and requires internet connection
            for full functionality. All visualizations are client-side rendered.
        """
        # Prepare data
        flow_patterns = self.flow_metrics['flow_patterns']
        all_statuses = self.flow_metrics['all_statuses']
        loops = self.flow_metrics.get('loops', {})
        time_in_status = self.flow_metrics.get('time_in_status', {})
        timeline = self.flow_metrics.get('timeline', {})

        # Timeline data - includes ALL history + future dates
        timeline_data = timeline.get('daily_data', [])

        # Get date range from parameters (not from cached metadata)
        from datetime import datetime, timedelta
        today = datetime.now().strftime('%Y-%m-%d')

        # Use passed dates for filtering display data (handle None and empty strings)
        start_date = self.start_date or None
        end_date = self.end_date or None

        # Prepare all data for trend calculation (including future)
        all_dates = [d['date'] for d in timeline_data]
        all_created_counts = [d['created'] for d in timeline_data]
        all_closed_counts = [d['closed'] for d in timeline_data]
        all_open_counts = [d['open'] for d in timeline_data]

        # Filter data to show only PASSED dates (no future dates)
        if start_date or end_date:
            # Use parameter range, but limit to today for actual data
            actual_start = start_date if start_date else (all_dates[0] if all_dates else today)
            actual_end = min(end_date if end_date else today, today)
            filtered_indices = [i for i, date in enumerate(all_dates) if actual_start <= date <= actual_end]
        else:
            # No date filters: show all dates up to today
            filtered_indices = [i for i, date in enumerate(all_dates) if date <= today]

        dates_actual = [all_dates[i] for i in filtered_indices]
        created_counts = [all_created_counts[i] for i in filtered_indices]
        closed_counts = [all_closed_counts[i] for i in filtered_indices]
        open_counts = [all_open_counts[i] for i in filtered_indices]

        # Calculate current open bugs count
        current_open_bugs = 0
        if open_counts:
            current_open_bugs = open_counts[-1]  # Last value in actual data range

        # Calculate trends based on ACTUAL data only (no zeros)
        created_trend = self._calculate_trend(dates_actual, created_counts) if created_counts else []
        closed_trend = self._calculate_trend(dates_actual, closed_counts) if closed_counts else []
        open_trend = self._calculate_trend(dates_actual, open_counts) if open_counts else []

        # Create trend date array (starts same as actual dates)
        dates_trend = list(dates_actual)

        # Extend trend date array and trend lines to end_date for projection
        if end_date and end_date > today and dates_actual:
            # Generate dates from last date + 1 to end_date
            last_date_obj = datetime.strptime(dates_actual[-1], '%Y-%m-%d')
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')

            # Calculate number of future days
            future_days = (end_date_obj - last_date_obj).days

            if future_days > 0 and len(dates_actual) >= 2 and created_trend:
                # Calculate slope from trend
                created_slope = created_trend[-1] - created_trend[-2]
                closed_slope = closed_trend[-1] - closed_trend[-2]
                open_slope = open_trend[-1] - open_trend[-2]

                # Extend dates and trends
                current = last_date_obj + timedelta(days=1)
                for i in range(1, future_days + 1):
                    dates_trend.append(current.strftime('%Y-%m-%d'))
                    created_trend.append(created_trend[-1] + created_slope)
                    closed_trend.append(closed_trend[-1] + closed_slope)
                    open_trend.append(open_trend[-1] + open_slope)
                    current += timedelta(days=1)

        # Prepare end_date marker for graphs
        end_date_marker = ""
        if end_date and end_date > today:
            end_date_marker = f""",
            shapes: [
                {{
                    type: 'line',
                    x0: '{end_date}',
                    x1: '{end_date}',
                    y0: 0,
                    y1: 1,
                    yref: 'paper',
                    line: {{
                        color: 'rgba(220, 38, 38, 0.5)',
                        width: 2,
                        dash: 'dot'
                    }}
                }}
            ],
            annotations: [
                {{
                    x: '{end_date}',
                    y: 1,
                    yref: 'paper',
                    text: 'Koniec zakresu',
                    showarrow: false,
                    xanchor: 'left',
                    yanchor: 'bottom',
                    font: {{ size: 10, color: '#dc2626' }}
                }}
            ]"""

        # Sankey diagram data
        node_labels = all_statuses
        node_dict = {status: idx for idx, status in enumerate(node_labels)}

        sources = []
        targets = []
        values = []
        link_labels = []
        link_colors = []

        # Build Sankey diagram flows - all flows in gray
        for pattern in flow_patterns:
            from_status = pattern['from']
            to_status = pattern['to']
            count = pattern['count']

            sources.append(node_dict[from_status])
            targets.append(node_dict[to_status])
            values.append(count)
            link_labels.append(f"{from_status} → {to_status}: {count}")

            # All flows are gray
            link_colors.append('rgba(128, 128, 128, 0.4)')

        # Time in status table HTML
        time_table_rows = ""
        for status, stats in sorted(time_in_status.items(), key=lambda x: x[1]['avg_days'], reverse=True):
            time_table_rows += f"""
        <tr>
            <td>{status}</td>
            <td>{stats['avg_days']:.1f}</td>
            <td>{stats['median_hours'] / 24:.1f}</td>
            <td>{stats['count']}</td>
        </tr>
        """

        # Calculate actual date range for drilldowns (same as for graphs)
        if start_date or end_date:
            actual_start = start_date if start_date else (all_dates[0] if all_dates else today)
            actual_end = min(end_date if end_date else today, today)
        else:
            # No date filters: show all dates up to today
            actual_start = all_dates[0] if all_dates else today
            actual_end = today

        # Drilldown sections for open bugs - filter to parameter date range
        drilldown_sections = ""
        for day in timeline_data:
            # Filter drilldowns to show only dates within parameter range
            if not (actual_start <= day['date'] <= actual_end):
                continue

            if day['open'] > 0:
                bug_list = ""
                for bug in day['open_issues']:
                    # Create ticket link if jira_url is available
                    if self.jira_url:
                        ticket_link = f'<a href="{self.jira_url}/browse/{bug["key"]}" target="_blank" style="color: #dc2626; text-decoration: none;"><code>{bug["key"]}</code></a>'
                    else:
                        ticket_link = f'<code>{bug["key"]}</code>'

                    bug_list += f"""
                    <tr>
                        <td>{ticket_link}</td>
                        <td>{bug['summary']}</td>
                        <td><span class="status-badge">{bug['status']}</span></td>
                        <td><span class="status-badge">{bug.get('current_status', 'N/A')}</span></td>
                    </tr>
"""
                drilldown_sections += f"""
        <details class="drilldown-section">
            <summary>
                <strong>{day['date']}</strong>: {day['open']} otwartych błędów
            </summary>
            <table class="drilldown-table">
                <thead>
                    <tr>
                        <th>Klucz</th>
                        <th>Tytuł</th>
                        <th>Status tego dnia</th>
                        <th>Aktualny status</th>
                    </tr>
                </thead>
                <tbody>
                    {bug_list}
                </tbody>
            </table>
        </details>
"""

        # Generate HTML
        html_content = f"""<!DOCTYPE html>
        <html lang="pl">
        <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Raport Przepływu Błędów Jira - {self.metadata['project']}</title>
        <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
        <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
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
        h2 {{
            color: #2d3748;
            font-size: 1.8em;
            margin-bottom: 15px;
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
        .stat-card.warning {{
            border-left: 4px solid #f59e0b;
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
        .chart-subtitle {{
            color: #718096;
            font-size: 0.9em;
            margin-bottom: 20px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e2e8f0;
        }}
        th {{
            background-color: #f7fafc;
            font-weight: 600;
            color: #2d3748;
        }}
        tr:hover {{
            background-color: #f7fafc;
        }}
        .loop-emphasis {{
            color: #dc2626;
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
        .drilldown-section {{
            margin-top: 20px;
            padding: 15px;
            background-color: #f7fafc;
            border-radius: 8px;
            border-left: 4px solid #3b82f6;
        }}
        .drilldown-section summary {{
            cursor: pointer;
            padding: 10px;
            font-size: 1.1em;
            user-select: none;
        }}
        .drilldown-section summary:hover {{
            background-color: #e2e8f0;
            border-radius: 4px;
        }}
        .drilldown-table {{
            margin-top: 15px;
            font-size: 0.9em;
        }}
        .status-badge {{
            background-color: #e0e7ff;
            color: #3730a3;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.85em;
            font-weight: 500;
        }}
        code {{
            background-color: #f1f5f9;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            color: #dc2626;
        }}
        .label-filter-container {{
            margin-top: 20px;
            padding: 15px;
            background-color: #f8fafc;
            border-radius: 8px;
            border: 2px solid #cbd5e1;
        }}
        .toggle-switch {{
            display: inline-flex;
            align-items: center;
            gap: 12px;
            cursor: pointer;
        }}
        .toggle-switch input[type="checkbox"] {{
            position: relative;
            width: 50px;
            height: 24px;
            -webkit-appearance: none;
            background: #cbd5e1;
            outline: none;
            border-radius: 12px;
            transition: 0.3s;
            cursor: pointer;
        }}
        .toggle-switch input:checked[type="checkbox"] {{
            background: #667eea;
        }}
        .toggle-switch input[type="checkbox"]:before {{
            content: '';
            position: absolute;
            width: 20px;
            height: 20px;
            border-radius: 50%;
            top: 2px;
            left: 2px;
            background: #fff;
            transition: 0.3s;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }}
        .toggle-switch input:checked[type="checkbox"]:before {{
            left: 28px;
        }}
        .toggle-label {{
            font-weight: 600;
            color: #2d3748;
            font-size: 1em;
        }}
        .filter-info {{
            margin-top: 10px;
            font-size: 0.9em;
            color: #64748b;
        }}
        </style>
        </head>
        <body>
        <div class="container">
        <div class="header">
            <h1>🐛 Analiza Przepływu Błędów Jira</h1>
            <div class="metadata">
                <strong>Projekt:</strong> {self.metadata['project']}<br>
                <strong>Pobrano:</strong> {self.metadata.get('fetched_at', 'N/A')}<br>
                <strong>Zakres dat:</strong> {self.start_date or 'Wszystkie'} do {self.end_date or 'Wszystkie'}<br>
                <strong>Łącznie błędów:</strong> <span id="total-issues-count">{self.flow_metrics.get('total_issues', 0)}</span>
            </div>
            {self._generate_label_toggle_html()}
        </div>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-label">Obecnie Otwarte Błędy</div>
                <div class="stat-value">{current_open_bugs}</div>
            </div>
        </div>

        <div class="chart-container">
            <div class="chart-title">📈 Utworzone vs Zamknięte Błędy w Czasie</div>
            <div class="chart-subtitle">Dzienne tworzenie i zamykanie błędów z liniami trendu</div>
            <div id="timeline-chart"></div>
        </div>

        <div class="chart-container">
            <div class="chart-title">🔄 Diagram Przepływu Statusów (Sankey)</div>
            <div class="chart-subtitle">Wszystkie przejścia między statusami</div>
            <div style="margin-bottom: 15px; color: #718096;">
                <strong>Łącznie przejść:</strong> {self.flow_metrics['total_transitions']}
            </div>
            <div id="sankey-chart"></div>
        </div>

        <div class="chart-container">
            <div class="chart-title">📊 Otwarte Błędy w Czasie</div>
            <div class="chart-subtitle">Liczba błędów w statusie NEW lub IN PROGRESS każdego dnia z analizą trendu</div>
            <div id="open-chart"></div>

            <h3 style="margin-top: 30px; margin-bottom: 15px; color: #2d3748;">🔍 Szczegóły otwartych błędów dzień po dniu</h3>
            {drilldown_sections if drilldown_sections else '<p style="color: #718096;">Brak danych do wyświetlenia</p>'}
        </div>

        <div class="chart-container">
            <div class="chart-title">⏱️ Średni Czas w Każdym Statusie</div>
            <div class="chart-subtitle">Jak długo błędy spędzają w poszczególnych statusach (w dniach)</div>
            <table>
                <thead>
                    <tr>
                        <th>Status</th>
                        <th>Śr. Dni</th>
                        <th>Mediana Dni</th>
                        <th>Liczba</th>
                    </tr>
                </thead>
                <tbody>
                    {time_table_rows if time_table_rows else '<tr><td colspan="4">Brak danych</td></tr>'}
                </tbody>
            </table>
        </div>

        <div class="footer">
            Wygenerowano {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Analizator Przepływu Błędów Jira v2.0
        </div>
        </div>

        <script>
        // Label filter toggle functionality (currently reloads page)
        function toggleLabelFilter() {{
            // For now, we'll notify the user that full dynamic switching requires page reload
            // Future enhancement: implement full dynamic chart redrawing
            alert('Funkcja przełączania labelek zostanie dodana w kolejnej wersji. Aktualnie raport pokazuje dane z aktywnym filtrem etykiety.');
            // Reset checkbox to checked state
            document.getElementById('labelFilterToggle').checked = true;
        }}

        // Utworzone vs Zamknięte Timeline
        const timelineData = [
            {{
                x: {json.dumps(dates_actual)},
                y: {json.dumps(created_counts)},
                name: 'Utworzone',
                type: 'scatter',
                mode: 'lines+markers',
                line: {{ color: '#3b82f6', width: 2 }},
                marker: {{ size: 6 }}
            }},
            {{
                x: {json.dumps(dates_trend)},
                y: {json.dumps(created_trend)},
                name: 'Trend Utworzonych',
                type: 'scatter',
                mode: 'lines',
                line: {{ color: '#3b82f6', width: 2, dash: 'dash' }},
                opacity: 0.6
            }},
            {{
                x: {json.dumps(dates_actual)},
                y: {json.dumps(closed_counts)},
                name: 'Zamknięte',
                type: 'scatter',
                mode: 'lines+markers',
                line: {{ color: '#10b981', width: 2 }},
                marker: {{ size: 6 }}
            }},
            {{
                x: {json.dumps(dates_trend)},
                y: {json.dumps(closed_trend)},
                name: 'Trend Zamkniętych',
                type: 'scatter',
                mode: 'lines',
                line: {{ color: '#10b981', width: 2, dash: 'dash' }},
                opacity: 0.6
            }}
        ];

        const timelineLayout = {{
            xaxis: {{ title: 'Data' }},
            yaxis: {{ title: 'Liczba Błędów' }},
            hovermode: 'x unified',
            showlegend: true,
            height: 400{end_date_marker}
        }};

        Plotly.newPlot('timeline-chart', timelineData, timelineLayout, {{responsive: true}});

        // Otwarte Błędy Timeline - wykres słupkowy
        const openData = [
            {{
                x: {json.dumps(dates_actual)},
                y: {json.dumps(open_counts)},
                name: 'Otwarte Błędy',
                type: 'bar',
                marker: {{ color: '#f59e0b' }}
            }},
            {{
                x: {json.dumps(dates_trend)},
                y: {json.dumps(open_trend)},
                name: 'Trend',
                type: 'scatter',
                mode: 'lines',
                line: {{ color: '#dc2626', width: 3, dash: 'dash' }}
            }}
        ];

        const openLayout = {{
            xaxis: {{ title: 'Data' }},
            yaxis: {{ title: 'Liczba Otwartych Błędów' }},
            hovermode: 'x unified',
            showlegend: true,
            height: 400{end_date_marker}
        }};

        Plotly.newPlot('open-chart', openData, openLayout, {{responsive: true}});

        // Diagram Sankey
        const sankeyData = [{{
            type: "sankey",
            orientation: "h",
            node: {{
                pad: 15,
                thickness: 30,
                line: {{
                    color: "black",
                    width: 0.5
                }},
                label: {json.dumps(node_labels)},
                color: {json.dumps(['#' + format(hash(s) % 0xFFFFFF, '06x') for s in node_labels])}
            }},
            link: {{
                source: {json.dumps(sources)},
                target: {json.dumps(targets)},
                value: {json.dumps(values)},
                label: {json.dumps(link_labels)},
                color: {json.dumps(link_colors)}
            }}
        }}];

        const sankeyLayout = {{
            font: {{
                size: 11,
                family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
            }},
            height: 700,
            margin: {{ l: 20, r: 20, t: 20, b: 20 }}
        }};

        Plotly.newPlot('sankey-chart', sankeyData, sankeyLayout, {{responsive: true}});
        </script>
        </body>
        </html>
        """

        # Write to file
        output_path = Path(output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        return str(output_path)
