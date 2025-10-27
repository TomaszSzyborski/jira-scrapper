"""Open issues tracking by status category (In Progress vs Open)."""

from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import polars as pl
import plotly.graph_objects as go
import numpy as np


class OpenIssuesStatusChart:
    """Generates charts for tracking open issues by status category."""

    # Status category mappings
    STATUS_CATEGORIES = {
        "in_progress": ["In Progress", "In Development", "In Review", "Testing", "QA"],
        "open": ["Open", "To Do", "Backlog", "New", "Reopened"],
        "blocked": ["Blocked", "On Hold", "Waiting"],
    }

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

    def _categorize_status(self, status: str) -> str:
        """
        Categorize a status into in_progress, open, or blocked.

        Args:
            status: Status string

        Returns:
            Category name
        """
        status_lower = status.lower()

        # Check exact matches first
        for category, statuses in self.STATUS_CATEGORIES.items():
            if status in statuses:
                return category

        # Heuristic detection
        if any(keyword in status_lower for keyword in ["progress", "development", "review", "testing"]):
            return "in_progress"
        elif any(keyword in status_lower for keyword in ["block", "hold", "wait"]):
            return "blocked"
        elif any(keyword in status_lower for keyword in ["open", "todo", "to do", "backlog", "new"]):
            return "open"

        # Default for done/closed statuses
        if any(keyword in status_lower for keyword in ["done", "closed", "resolved", "complete"]):
            return "done"

        return "open"  # Default fallback

    def build_dataframe(self) -> pl.DataFrame:
        """
        Convert raw ticket data into Polars DataFrame with categories.

        Returns:
            DataFrame with ticket data
        """
        ticket_records = []
        for ticket in self.tickets:
            # Exclude test executions
            if ticket.get("issue_type", "") not in ["Test Execution", "Test"]:
                ticket_records.append({
                    "key": ticket["key"],
                    "summary": ticket["summary"],
                    "created": datetime.fromisoformat(ticket["created"].replace("Z", "+00:00")),
                    "updated": datetime.fromisoformat(ticket["updated"].replace("Z", "+00:00")),
                    "resolved": datetime.fromisoformat(ticket["resolved"].replace("Z", "+00:00"))
                    if ticket.get("resolved") else None,
                    "status": ticket["status"],
                    "status_category": self._categorize_status(ticket["status"]),
                    "issue_type": ticket.get("issue_type", ""),
                    "priority": ticket.get("priority", ""),
                    "assignee": ticket.get("assignee", ""),
                })

        self.df = pl.DataFrame(ticket_records) if ticket_records else pl.DataFrame()
        return self.df

    def calculate_daily_open_metrics(
        self,
        start_date: str,
        end_date: str
    ) -> pl.DataFrame:
        """
        Calculate daily open issues by status category.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            DataFrame with daily open issue metrics
        """
        if self.df is None or self.df.is_empty():
            self.build_dataframe()

        if self.df.is_empty():
            return pl.DataFrame()

        start = datetime.fromisoformat(start_date).replace(tzinfo=timezone.utc)
        end = datetime.fromisoformat(end_date).replace(tzinfo=timezone.utc)

        date_range = pl.datetime_range(start, end, interval="1d", eager=True, time_zone="UTC")

        daily_metrics = []

        for current_date in date_range:
            # Get all issues that were open on this date
            # (created before/on this date AND not resolved OR resolved after this date)
            open_issues = self.df.filter(
                (pl.col("created") <= current_date) &
                ((pl.col("resolved").is_null()) | (pl.col("resolved") > current_date))
            )

            # Count by category
            in_progress_count = open_issues.filter(pl.col("status_category") == "in_progress").height
            open_count = open_issues.filter(pl.col("status_category") == "open").height
            blocked_count = open_issues.filter(pl.col("status_category") == "blocked").height
            total_open = open_issues.height

            daily_metrics.append({
                "date": current_date,
                "in_progress": in_progress_count,
                "open": open_count,
                "blocked": blocked_count,
                "total_open": total_open,
            })

        return pl.DataFrame(daily_metrics)

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

    def create_open_issues_chart(
        self,
        start_date: str,
        end_date: str,
        title: str = "Open Issues by Status Category"
    ) -> str:
        """
        Create stacked area chart showing open issues by category.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            title: Chart title

        Returns:
            HTML string of the chart
        """
        metrics_df = self.calculate_daily_open_metrics(start_date, end_date)

        if metrics_df.is_empty():
            return "<p>No issue data available for the specified date range.</p>"

        dates = metrics_df["date"].to_list()
        in_progress = metrics_df["in_progress"].to_list()
        open_status = metrics_df["open"].to_list()
        blocked = metrics_df["blocked"].to_list()
        total_open = metrics_df["total_open"].to_list()

        # Calculate trend line for total
        total_trend = self.calculate_trend_line(dates, total_open)

        # Create figure
        fig = go.Figure()

        # Stacked area chart
        fig.add_trace(go.Scatter(
            x=dates,
            y=in_progress,
            name="In Progress",
            mode="lines",
            stackgroup="one",
            fillcolor="#3498db",
            line=dict(width=0.5, color="#3498db"),
            hovertemplate="<b>%{x|%Y-%m-%d}</b><br>In Progress: %{y}<extra></extra>",
        ))

        fig.add_trace(go.Scatter(
            x=dates,
            y=open_status,
            name="Open",
            mode="lines",
            stackgroup="one",
            fillcolor="#95a5a6",
            line=dict(width=0.5, color="#95a5a6"),
            hovertemplate="<b>%{x|%Y-%m-%d}</b><br>Open: %{y}<extra></extra>",
        ))

        fig.add_trace(go.Scatter(
            x=dates,
            y=blocked,
            name="Blocked",
            mode="lines",
            stackgroup="one",
            fillcolor="#e67e22",
            line=dict(width=0.5, color="#e67e22"),
            hovertemplate="<b>%{x|%Y-%m-%d}</b><br>Blocked: %{y}<extra></extra>",
        ))

        # Total trend line
        fig.add_trace(go.Scatter(
            x=dates,
            y=total_trend,
            name="Total Trend",
            mode="lines",
            line=dict(color="#000000", width=2, dash="dash"),
            hovertemplate="<b>%{x|%Y-%m-%d}</b><br>Trend: %{y:.1f}<extra></extra>",
        ))

        # Update layout
        fig.update_layout(
            title=title,
            xaxis_title="Date",
            yaxis_title="Number of Open Issues",
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

    def get_summary_statistics(
        self,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """
        Get summary statistics for open issues.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            Dictionary with summary statistics
        """
        metrics_df = self.calculate_daily_open_metrics(start_date, end_date)

        if metrics_df.is_empty():
            return {
                "avg_open": 0,
                "max_open": 0,
                "final_open": 0,
                "avg_in_progress": 0,
                "avg_blocked": 0,
            }

        return {
            "avg_open": metrics_df["total_open"].mean(),
            "max_open": metrics_df["total_open"].max(),
            "final_open": metrics_df["total_open"][-1] if len(metrics_df) > 0 else 0,
            "avg_in_progress": metrics_df["in_progress"].mean(),
            "avg_blocked": metrics_df["blocked"].mean(),
        }
