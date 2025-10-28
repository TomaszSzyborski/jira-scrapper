"""Bug tracking visualization module - daily created/closed bugs with trend lines."""

from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
import polars as pl
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np


class BugTrackingChart:
    """Generates charts for bug creation and closure tracking."""

    def __init__(self, tickets: List[Dict[str, Any]], jira_url: str = ""):
        """
        Initialize with ticket data.

        Args:
            tickets: List of ticket dictionaries from JiraScraper
            jira_url: Base URL of Jira instance for generating links
        """
        self.tickets = tickets
        self.jira_url = jira_url
        if self.jira_url and self.jira_url.endswith("/"):
            self.jira_url = self.jira_url[:-1]
        self.df: Optional[pl.DataFrame] = None

    def build_dataframe(self) -> pl.DataFrame:
        """
        Convert raw ticket data into Polars DataFrame filtering only bugs.

        Returns:
            DataFrame with bug ticket data
        """
        bug_records = []
        for ticket in self.tickets:
            # Only include bugs (English and Polish)
            issue_type = ticket.get("issue_type", "")
            if issue_type.lower() in ["bug", "defect"] or issue_type == "Błąd w programie":
                bug_records.append({
                    "key": ticket["key"],
                    "summary": ticket["summary"],
                    "created": datetime.fromisoformat(ticket["created"].replace("Z", "+00:00")),
                    "updated": datetime.fromisoformat(ticket["updated"].replace("Z", "+00:00")),
                    "resolved": datetime.fromisoformat(ticket["resolved"].replace("Z", "+00:00"))
                    if ticket.get("resolved") else None,
                    "status": ticket["status"],
                    "priority": ticket.get("priority", ""),
                    "assignee": ticket.get("assignee", ""),
                })

        self.df = pl.DataFrame(bug_records) if bug_records else pl.DataFrame()
        return self.df

    def calculate_daily_bug_metrics(
        self,
        start_date: str,
        end_date: str
    ) -> pl.DataFrame:
        """
        Calculate daily metrics for bugs created and closed.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            DataFrame with daily bug metrics
        """
        if self.df is None or self.df.is_empty():
            self.build_dataframe()

        if self.df.is_empty():
            return pl.DataFrame()

        # Create timezone-aware datetimes
        start = datetime.fromisoformat(start_date).replace(tzinfo=timezone.utc)
        end = datetime.fromisoformat(end_date).replace(tzinfo=timezone.utc)

        # Generate date range with timezone
        date_range = pl.datetime_range(start, end, interval="1d", eager=True, time_zone="UTC")

        daily_metrics = []
        bugs_by_date = {"created": {}, "closed": {}}

        for current_date in date_range:
            # Bugs created on this day
            created_bugs = self.df.filter(
                pl.col("created").dt.date() == current_date.date()
            )
            bugs_created = created_bugs.height

            # Store bug keys for drilldown
            created_bug_keys = created_bugs["key"].to_list() if bugs_created > 0 else []
            bugs_by_date["created"][current_date.strftime("%Y-%m-%d")] = created_bug_keys

            # Bugs closed on this day
            closed_bugs = self.df.filter(
                (pl.col("resolved").is_not_null()) &
                (pl.col("resolved").dt.date() == current_date.date())
            )
            bugs_closed = closed_bugs.height

            # Store bug keys for drilldown
            closed_bug_keys = closed_bugs["key"].to_list() if bugs_closed > 0 else []
            bugs_by_date["closed"][current_date.strftime("%Y-%m-%d")] = closed_bug_keys

            # Total bugs created up to this day
            total_created = self.df.filter(
                pl.col("created") <= current_date
            ).height

            # Total bugs resolved up to this day
            total_resolved = self.df.filter(
                (pl.col("resolved").is_not_null()) &
                (pl.col("resolved") <= current_date)
            ).height

            # Open bugs at end of this day
            open_bugs = total_created - total_resolved

            daily_metrics.append({
                "date": current_date,
                "bugs_created": bugs_created,
                "bugs_closed": bugs_closed,
                "open_bugs": open_bugs,
            })

        result_df = pl.DataFrame(daily_metrics)
        result_df._bugs_by_date = bugs_by_date  # Attach for drilldown
        return result_df

    @staticmethod
    def calculate_trend_line(dates: List[datetime], values: List[float]) -> List[float]:
        """
        Calculate linear trend line using least squares regression.

        Args:
            dates: List of datetime objects
            values: List of corresponding values

        Returns:
            List of trend line values
        """
        if not dates or not values:
            return []

        x = np.array([(d - dates[0]).days for d in dates])
        y = np.array(values)

        coefficients = np.polyfit(x, y, 1)
        trend = np.polyval(coefficients, x)

        return trend.tolist()

    def create_bug_tracking_chart(
        self,
        start_date: str,
        end_date: str,
        title: str = "Daily Bug Tracking"
    ) -> str:
        """
        Create chart showing bugs created and closed daily with trend lines.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            title: Chart title

        Returns:
            HTML string of the chart
        """
        metrics_df = self.calculate_daily_bug_metrics(start_date, end_date)

        if metrics_df.is_empty():
            return "<p>No bug data available for the specified date range.</p>"

        dates = metrics_df["date"].to_list()
        created = metrics_df["bugs_created"].to_list()
        closed = metrics_df["bugs_closed"].to_list()

        # Calculate trend lines
        created_trend = self.calculate_trend_line(dates, created)
        closed_trend = self.calculate_trend_line(dates, closed)

        # Create figure
        fig = go.Figure()

        # Bugs Created
        fig.add_trace(go.Bar(
            x=dates,
            y=created,
            name="Bugs Created",
            marker_color="#e74c3c",
            hovertemplate="<b>%{x|%Y-%m-%d}</b><br>Bugs Created: %{y}<extra></extra>",
        ))

        # Bugs Closed
        fig.add_trace(go.Bar(
            x=dates,
            y=closed,
            name="Bugs Closed",
            marker_color="#2ecc71",
            hovertemplate="<b>%{x|%Y-%m-%d}</b><br>Bugs Closed: %{y}<extra></extra>",
        ))

        # Created Trend
        fig.add_trace(go.Scatter(
            x=dates,
            y=created_trend,
            name="Created Trend",
            mode="lines",
            line=dict(color="#c0392b", width=2, dash="dash"),
            showlegend=True,
        ))

        # Closed Trend
        fig.add_trace(go.Scatter(
            x=dates,
            y=closed_trend,
            name="Closed Trend",
            mode="lines",
            line=dict(color="#27ae60", width=2, dash="dash"),
            showlegend=True,
        ))

        # Update layout
        fig.update_layout(
            title=title,
            xaxis_title="Date",
            yaxis_title="Number of Bugs",
            hovermode="x unified",
            template="plotly_white",
            height=500,
            barmode='group',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )

        return fig.to_html(full_html=False, include_plotlyjs="cdn")

    def get_bug_details_table(
        self,
        start_date: str,
        end_date: str
    ) -> str:
        """
        Generate HTML table with bug details grouped by date.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            HTML string with bug details table
        """
        metrics_df = self.calculate_daily_bug_metrics(start_date, end_date)

        if metrics_df.is_empty():
            return ""

        bugs_by_date = getattr(metrics_df, '_bugs_by_date', {"created": {}, "closed": {}})

        html = '<h3>Bug Details by Date</h3>'
        html += '<p style="font-size: 0.9rem; color: #666; margin-bottom: 15px;">Click on a date to see bug details</p>'

        dates = metrics_df["date"].to_list()
        created_counts = metrics_df["bugs_created"].to_list()
        closed_counts = metrics_df["bugs_closed"].to_list()

        for idx, (date, created_count, closed_count) in enumerate(zip(dates, created_counts, closed_counts)):
            if created_count == 0 and closed_count == 0:
                continue

            date_str = date.strftime("%Y-%m-%d")

            html += f'''
            <div class="pattern-row">
                <div class="pattern-header" onclick="togglePattern('bug-date-{idx}')">
                    <span class="pattern-arrow">▶</span>
                    <span class="pattern-text">{date_str}</span>
                    <span class="pattern-count" style="background: #e74c3c;">Created: {created_count}</span>
                    <span class="pattern-count" style="background: #2ecc71;">Closed: {closed_count}</span>
                </div>
                <div id="bug-date-{idx}" class="pattern-details" style="display: none;">
            '''

            # Created bugs
            if created_count > 0:
                created_keys = bugs_by_date["created"].get(date_str, [])
                html += '<div class="ticket-list" style="margin-bottom: 20px;">'
                html += f'<h4 style="color: #e74c3c;">Bugs Created on {date_str} ({created_count})</h4>'
                html += '<table class="ticket-table">'
                html += '<tr><th>Key</th><th>Summary</th><th>Status</th><th>Priority</th><th>Assignee</th></tr>'

                for bug_key in created_keys:
                    bug = next((t for t in self.tickets if t["key"] == bug_key), None)
                    if bug:
                        bug_link = f"{self.jira_url}/browse/{bug_key}" if self.jira_url else "#"
                        summary = bug["summary"][:80] + "..." if len(bug["summary"]) > 80 else bug["summary"]
                        html += f'''
                        <tr>
                            <td><a href="{bug_link}" target="_blank" class="ticket-link">{bug_key}</a></td>
                            <td>{summary}</td>
                            <td>{bug["status"]}</td>
                            <td>{bug.get("priority", "N/A")}</td>
                            <td>{bug.get("assignee", "Unassigned")}</td>
                        </tr>'''

                html += '</table></div>'

            # Closed bugs
            if closed_count > 0:
                closed_keys = bugs_by_date["closed"].get(date_str, [])
                html += '<div class="ticket-list">'
                html += f'<h4 style="color: #2ecc71;">Bugs Closed on {date_str} ({closed_count})</h4>'
                html += '<table class="ticket-table">'
                html += '<tr><th>Key</th><th>Summary</th><th>Status</th><th>Priority</th><th>Assignee</th></tr>'

                for bug_key in closed_keys:
                    bug = next((t for t in self.tickets if t["key"] == bug_key), None)
                    if bug:
                        bug_link = f"{self.jira_url}/browse/{bug_key}" if self.jira_url else "#"
                        summary = bug["summary"][:80] + "..." if len(bug["summary"]) > 80 else bug["summary"]
                        html += f'''
                        <tr>
                            <td><a href="{bug_link}" target="_blank" class="ticket-link">{bug_key}</a></td>
                            <td>{summary}</td>
                            <td>{bug["status"]}</td>
                            <td>{bug.get("priority", "N/A")}</td>
                            <td>{bug.get("assignee", "Unassigned")}</td>
                        </tr>'''

                html += '</table></div>'

            html += '</div></div>'

        return html

    def get_summary_statistics(
        self,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """
        Get summary statistics for bugs.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            Dictionary with summary statistics
        """
        metrics_df = self.calculate_daily_bug_metrics(start_date, end_date)

        if metrics_df.is_empty():
            return {
                "total_created": 0,
                "total_closed": 0,
                "avg_created_per_day": 0,
                "avg_closed_per_day": 0,
                "max_open_bugs": 0,
                "final_open_bugs": 0,
            }

        return {
            "total_created": metrics_df["bugs_created"].sum(),
            "total_closed": metrics_df["bugs_closed"].sum(),
            "avg_created_per_day": metrics_df["bugs_created"].mean(),
            "avg_closed_per_day": metrics_df["bugs_closed"].mean(),
            "max_open_bugs": metrics_df["open_bugs"].max(),
            "final_open_bugs": metrics_df["open_bugs"][-1] if len(metrics_df) > 0 else 0,
        }
