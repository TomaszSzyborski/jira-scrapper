"""In Progress tracking chart - tracks issues NOT in Done status category on each date."""

from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import polars as pl
import plotly.graph_objects as go
import numpy as np


class InProgressTrackingChart:
    """Generates charts for tracking issues not in Done status category day by day."""

    # Status category mappings for "Done"
    DONE_STATUSES = [
        "Done",
        "Closed",
        "Resolved",
        "Complete",
        "Completed",
        "Finished",
        "Cancelled",
        "Canceled",
        "Rejected",
    ]

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
            True if ticket was not done (in progress) on that date
        """
        # Check if ticket was created before or on target date
        created = datetime.fromisoformat(ticket["created"].replace("Z", "+00:00"))
        if created.date() > target_date.date():
            return False  # Ticket didn't exist yet

        # Check if ticket was resolved after target date (or not resolved at all)
        resolved = ticket.get("resolved")
        if resolved:
            resolved_date = datetime.fromisoformat(resolved.replace("Z", "+00:00"))
            if resolved_date.date() <= target_date.date():
                # Check if resolved status is actually "Done"
                status = ticket.get("status", "")
                if self._is_done_status(status):
                    return False  # Was already done

        # Get status history from changelog
        status_history = ticket.get("status_history", [])

        if not status_history:
            # If no history, check current status
            current_status = ticket.get("status", "")
            status_category = ticket.get("status_category", "")

            # Check status category first
            if status_category and status_category.lower() == "done":
                return False

            # Fallback to status name
            return not self._is_done_status(current_status)

        # Find the status at the target date
        status_at_date = None
        for history_entry in sorted(status_history, key=lambda x: x["changed_at"]):
            changed_at = datetime.fromisoformat(history_entry["changed_at"].replace("Z", "+00:00"))

            if changed_at.date() <= target_date.date():
                status_at_date = history_entry["to_status"]
            else:
                break

        if status_at_date is None:
            # No status change before target date, use current status
            status_at_date = ticket.get("status", "")

        # Check if status at that date was NOT done
        return not self._is_done_status(status_at_date)

    def _is_done_status(self, status: str) -> bool:
        """
        Check if a status is considered "Done" category.

        Args:
            status: Status string

        Returns:
            True if status is in Done category
        """
        # Check exact matches
        if status in self.DONE_STATUSES:
            return True

        # Heuristic detection
        status_lower = status.lower()
        keywords = ["done", "closed", "resolved", "complete", "finish", "cancel", "reject"]
        return any(keyword in status_lower for keyword in keywords)

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
        Create chart showing issues not in Done status category each day.

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

        # Not Done line
        fig.add_trace(go.Scatter(
            x=dates,
            y=in_progress,
            name="Not Done (In Progress)",
            mode="lines+markers",
            line=dict(color="#f39c12", width=2),
            marker=dict(size=4),
            hovertemplate="<b>%{x|%Y-%m-%d}</b><br>Not Done: %{y}<extra></extra>",
        ))

        # Trend line
        fig.add_trace(go.Scatter(
            x=dates,
            y=trend,
            name="Trend",
            mode="lines",
            line=dict(color="#f39c12", width=2, dash="dash"),
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
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )

        return fig.to_html(full_html=False, include_plotlyjs="cdn")

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

        html = '<h3>In Progress Issues by Date</h3>'
        html += '<p style="font-size: 0.9rem; color: #666; margin-bottom: 15px;">Click on a date to see issues that were in progress</p>'

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
                    <span class="pattern-count" style="background: #f39c12;">{count} in progress</span>
                </div>
                <div id="progress-date-{idx}" class="pattern-details" style="display: none;">
            '''

            if ticket_keys:
                html += '<div class="ticket-list">'
                html += f'<h4 style="color: #f39c12;">Issues In Progress on {date_str} ({count})</h4>'
                html += '<table class="ticket-table">'
                html += '<tr><th>Key</th><th>Summary</th><th>Status</th><th>Assignee</th></tr>'

                for ticket_key in ticket_keys:
                    ticket = next((t for t in self.tickets if t["key"] == ticket_key), None)
                    if ticket:
                        ticket_link = f"{self.jira_url}/browse/{ticket_key}" if self.jira_url else "#"
                        summary = ticket["summary"][:80] + "..." if len(ticket["summary"]) > 80 else ticket["summary"]
                        html += f'''
                        <tr>
                            <td><a href="{ticket_link}" target="_blank" class="ticket-link">{ticket_key}</a></td>
                            <td>{summary}</td>
                            <td>{ticket["status"]}</td>
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
