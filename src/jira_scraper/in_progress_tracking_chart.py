"""In Progress tracking chart - tracks issues NOT in Done status category on each date."""

from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import polars as pl
import plotly.graph_objects as go
import numpy as np
from .status_definitions import StatusDefinitions


class InProgressTrackingChart:
    """Generates charts for tracking issues not in Done status category day by day."""

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

    def _was_not_done_on_date(self, ticket: Dict[str, Any], target_date: datetime) -> bool:
        """
        Check if a ticket was NOT in Done status category on a specific date.

        This checks if statusCategory != Done on the target date.

        Args:
            ticket: Ticket dictionary
            target_date: Date to check (timezone-aware)

        Returns:
            True if ticket was not done (open/active) on that date
        """
        # Check if ticket was created after target date
        created = datetime.fromisoformat(ticket["created"].replace("Z", "+00:00"))
        if created.date() > target_date.date():
            return False  # Ticket didn't exist yet

        # Get status history from changelog
        status_history = ticket.get("status_history", [])

        if not status_history:
            # If no history, check if ticket was created and what its status is
            # Since we don't have history, we can only check current status
            # This means if the ticket is currently done and was created before target_date,
            # we assume it was done on target_date (not accurate but best we can do)
            current_status = ticket.get("status", "")
            status_category = ticket.get("status_category", "")

            # Use StatusDefinitions for checking
            return StatusDefinitions.is_not_done(current_status, status_category)

        # Find the status that was active on the target date
        # We need to find the most recent status change that happened on or before target_date
        status_at_date = None
        status_category_at_date = None

        # Sort history by date
        sorted_history = sorted(status_history, key=lambda x: x["changed_at"])

        # The initial status is the "from_status" of the first transition
        # or the current status if created before any transition
        if sorted_history:
            first_change = datetime.fromisoformat(sorted_history[0]["changed_at"].replace("Z", "+00:00"))
            if created.date() < first_change.date():
                # There was a status before the first transition
                status_at_date = sorted_history[0].get("from_status", ticket.get("status", ""))

        # Find the status on target_date by walking through history
        for history_entry in sorted_history:
            changed_at = datetime.fromisoformat(history_entry["changed_at"].replace("Z", "+00:00"))

            if changed_at.date() <= target_date.date():
                # This transition happened on or before target_date
                status_at_date = history_entry["to_status"]
                status_category_at_date = history_entry.get("to_status_category")
            else:
                # This transition happened after target_date, stop here
                break

        # If we still don't have a status, use the initial status from first transition
        if status_at_date is None and sorted_history:
            status_at_date = sorted_history[0].get("from_status", ticket.get("status", ""))

        # If still no status found, use current status as fallback
        if status_at_date is None:
            status_at_date = ticket.get("status", "")
            status_category_at_date = ticket.get("status_category", "")

        # Check if status at that date was NOT done
        return StatusDefinitions.is_not_done(status_at_date, status_category_at_date or "")

    def calculate_daily_in_progress(
        self,
        start_date: str,
        end_date: str
    ) -> pl.DataFrame:
        """
        Calculate how many issues were in progress on each date.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            DataFrame with daily in progress counts
        """
        start = datetime.fromisoformat(start_date).replace(tzinfo=timezone.utc)
        end = datetime.fromisoformat(end_date).replace(tzinfo=timezone.utc)

        date_range = pl.datetime_range(start, end, interval="1d", eager=True, time_zone="UTC")

        daily_metrics = []
        tickets_by_date = {}

        for current_date in date_range:
            # Count tickets that were NOT done on this date (statusCategory != Done)
            in_progress_tickets = []

            for ticket in self.tickets:
                # Skip test executions
                if ticket.get("issue_type") in ["Test Execution", "Test"]:
                    continue

                if self._was_not_done_on_date(ticket, current_date):
                    in_progress_tickets.append(ticket["key"])
            
            count = len(in_progress_tickets)
            date_str = current_date.strftime("%Y-%m-%d")
            
            daily_metrics.append({
                "date": current_date,
                "in_progress_count": count,
            })
            
            tickets_by_date[date_str] = in_progress_tickets

        df = pl.DataFrame(daily_metrics)
        df._tickets_by_date = tickets_by_date  # Attach for drilldown
        return df

    @staticmethod
    def calculate_trend_line(dates: List[datetime], values: List[float]) -> List[float]:
        """Calculate linear trend line."""
        if not dates or not values:
            return []

        x = np.array([(d - dates[0]).days for d in dates])
        y = np.array(values)
        coefficients = np.polyfit(x, y, 1)
        trend = np.polyval(coefficients, x)

        return trend.tolist()

    def create_in_progress_chart(
        self,
        start_date: str,
        end_date: str,
        title: str = "Issues Not Done (statusCategory != Done) Day by Day"
    ) -> str:
        """
        Create bar chart showing issues not in Done status category each day.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            title: Chart title

        Returns:
            HTML string of the chart
        """
        metrics_df = self.calculate_daily_in_progress(start_date, end_date)

        if metrics_df.is_empty():
            return "<p>No data available for the specified date range.</p>"

        dates = metrics_df["date"].to_list()
        in_progress = metrics_df["in_progress_count"].to_list()

        # Calculate trend line
        trend = self.calculate_trend_line(dates, in_progress)

        # Create figure
        fig = go.Figure()

        # Not Done bars
        fig.add_trace(go.Bar(
            x=dates,
            y=in_progress,
            name="Not Done",
            marker_color="#f39c12",
            hovertemplate="<b>%{x|%Y-%m-%d}</b><br>Not Done: %{y}<extra></extra>",
        ))

        # Trend line
        fig.add_trace(go.Scatter(
            x=dates,
            y=trend,
            name="Trend",
            mode="lines",
            line=dict(color="#e67e22", width=3, dash="dash"),
            hovertemplate="<b>%{x|%Y-%m-%d}</b><br>Trend: %{y:.1f}<extra></extra>",
        ))

        # Update layout
        fig.update_layout(
            title=title,
            xaxis_title="Date",
            yaxis_title="Number of Issues Not Done",
            hovermode="x unified",
            template="plotly_white",
            height=500,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )

        return fig.to_html(full_html=False, include_plotlyjs="cdn")

    def _get_status_on_date(self, ticket: Dict[str, Any], target_date: datetime) -> str:
        """
        Get the status of a ticket on a specific date.

        Args:
            ticket: Ticket dictionary
            target_date: Date to check (timezone-aware)

        Returns:
            Status string on that date
        """
        status_history = ticket.get("status_history", [])

        if not status_history:
            return ticket.get("status", "Unknown")

        # Sort history by date
        sorted_history = sorted(status_history, key=lambda x: x["changed_at"])

        # Find status on target_date
        status_at_date = None

        # Check if ticket was created and get initial status
        created = datetime.fromisoformat(ticket["created"].replace("Z", "+00:00"))
        if sorted_history:
            first_change = datetime.fromisoformat(sorted_history[0]["changed_at"].replace("Z", "+00:00"))
            if created.date() < first_change.date():
                status_at_date = sorted_history[0].get("from_status", ticket.get("status", ""))

        # Walk through history to find status on target_date
        for history_entry in sorted_history:
            changed_at = datetime.fromisoformat(history_entry["changed_at"].replace("Z", "+00:00"))

            if changed_at.date() <= target_date.date():
                status_at_date = history_entry["to_status"]
            else:
                break

        if status_at_date is None and sorted_history:
            status_at_date = sorted_history[0].get("from_status", ticket.get("status", ""))

        if status_at_date is None:
            status_at_date = ticket.get("status", "Unknown")

        return status_at_date

    def get_in_progress_drilldown(
        self,
        start_date: str,
        end_date: str
    ) -> str:
        """
        Generate HTML with in progress drilldown by date.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            HTML string with in progress details
        """
        metrics_df = self.calculate_daily_in_progress(start_date, end_date)

        if metrics_df.is_empty():
            return ""

        tickets_by_date = getattr(metrics_df, '_tickets_by_date', {})
        dates = metrics_df["date"].to_list()
        counts = metrics_df["in_progress_count"].to_list()

        html = '<h3 data-i18n="in_progress_issues_by_date">In Progress Issues by Date</h3>'
        html += '<p style="font-size: 0.9rem; color: #666; margin-bottom: 15px;" data-i18n="click_to_see_in_progress">Click on a date to see issues that were in progress</p>'

        # Show only dates with issues
        for idx, (date, count) in enumerate(zip(dates, counts)):
            if count == 0:
                continue

            date_str = date.strftime("%Y-%m-%d")
            ticket_keys = tickets_by_date.get(date_str, [])

            html += f'''
            <div class="pattern-row">
                <div class="pattern-header" onclick="togglePattern('progress-date-{idx}')">
                    <span class="pattern-arrow">▶</span>
                    <span class="pattern-text">{date_str}</span>
                    <span class="pattern-count" style="background: #f39c12;">{count} <span data-i18n="in_progress_count">in progress</span></span>
                </div>
                <div id="progress-date-{idx}" class="pattern-details" style="display: none;">
            '''

            if ticket_keys:
                html += '<div class="ticket-list">'
                html += f'<h4 style="color: #f39c12;"><span data-i18n="issues_in_progress_on">Issues In Progress on</span> {date_str} ({count})</h4>'
                html += '<table class="ticket-table">'
                html += '<tr><th data-i18n="key">Key</th><th data-i18n="summary">Summary</th><th data-i18n="status">Status on Date</th><th data-i18n="assignee">Assignee</th></tr>'

                for ticket_key in ticket_keys:
                    ticket = next((t for t in self.tickets if t["key"] == ticket_key), None)
                    if ticket:
                        ticket_link = f"{self.jira_url}/browse/{ticket_key}" if self.jira_url else "#"
                        summary = ticket["summary"][:80] + "..." if len(ticket["summary"]) > 80 else ticket["summary"]
                        # Get the status on this specific date
                        status_on_date = self._get_status_on_date(ticket, date)
                        html += f'''
                        <tr>
                            <td><a href="{ticket_link}" target="_blank" class="ticket-link">{ticket_key}</a></td>
                            <td>{summary}</td>
                            <td>{status_on_date}</td>
                            <td>{ticket.get("assignee", "Unassigned")}</td>
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
        Get summary statistics for in progress issues.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            Dictionary with summary statistics
        """
        metrics_df = self.calculate_daily_in_progress(start_date, end_date)

        if metrics_df.is_empty():
            return {
                "avg_in_progress": 0,
                "max_in_progress": 0,
                "min_in_progress": 0,
                "final_in_progress": 0,
            }

        return {
            "avg_in_progress": metrics_df["in_progress_count"].mean(),
            "max_in_progress": metrics_df["in_progress_count"].max(),
            "min_in_progress": metrics_df["in_progress_count"].min(),
            "final_in_progress": metrics_df["in_progress_count"][-1] if len(metrics_df) > 0 else 0,
        }
