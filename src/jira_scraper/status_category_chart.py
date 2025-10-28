"""Status category distribution chart - bar chart showing To Do, In Progress, Done each day."""

from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import polars as pl
import plotly.graph_objects as go
import numpy as np


class StatusCategoryChart:
    """Generates bar charts for status category distribution day by day."""

    # Status category mappings
    STATUS_CATEGORY_MAP = {
        "To Do": ["To Do", "Open", "New", "Backlog", "Reopened", "TODO"],
        "In Progress": ["In Progress", "In Development", "In Review", "Testing", "QA", "Code Review", "Developing"],
        "Done": ["Done", "Closed", "Resolved", "Complete", "Completed", "Finished", "Cancelled", "Canceled", "Rejected"],
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

    def _get_status_category(self, status: str, status_category: Optional[str] = None) -> str:
        """
        Map a status to a category (To Do, In Progress, Done).

        Args:
            status: Status string
            status_category: Optional statusCategory field from Jira

        Returns:
            Category name
        """
        # Use Jira's statusCategory if available
        if status_category:
            cat_lower = status_category.lower()
            if cat_lower in ["todo", "to do", "new"]:
                return "To Do"
            elif cat_lower in ["indeterminate", "in progress", "inprogress"]:
                return "In Progress"
            elif cat_lower in ["done", "complete"]:
                return "Done"

        # Fallback to status name mapping
        for category, statuses in self.STATUS_CATEGORY_MAP.items():
            if status in statuses:
                return category

        # Heuristic detection
        status_lower = status.lower()
        if any(kw in status_lower for kw in ["done", "closed", "resolved", "complete", "finish", "cancel", "reject"]):
            return "Done"
        elif any(kw in status_lower for kw in ["progress", "development", "review", "testing", "qa", "developing"]):
            return "In Progress"
        else:
            return "To Do"

    def _get_status_category_on_date(self, ticket: Dict[str, Any], target_date: datetime) -> Optional[str]:
        """
        Get the status category of a ticket on a specific date.

        Args:
            ticket: Ticket dictionary
            target_date: Date to check (timezone-aware)

        Returns:
            Status category or None if ticket didn't exist
        """
        # Check if ticket existed on target date
        created = datetime.fromisoformat(ticket["created"].replace("Z", "+00:00"))
        if created.date() > target_date.date():
            return None  # Ticket didn't exist yet

        # Get status history from changelog
        status_history = ticket.get("status_history", [])

        if not status_history:
            # No history, use current status
            current_status = ticket.get("status", "")
            status_category = ticket.get("status_category", "")
            return self._get_status_category(current_status, status_category)

        # Find status at target date
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

        return self._get_status_category(status_at_date, ticket.get("status_category"))

    def calculate_daily_status_categories(
        self,
        start_date: str,
        end_date: str
    ) -> pl.DataFrame:
        """
        Calculate daily status category distribution.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            DataFrame with daily category counts
        """
        start = datetime.fromisoformat(start_date).replace(tzinfo=timezone.utc)
        end = datetime.fromisoformat(end_date).replace(tzinfo=timezone.utc)

        date_range = pl.datetime_range(start, end, interval="1d", eager=True, time_zone="UTC")

        daily_metrics = []

        for current_date in date_range:
            # Count tickets in each category
            todo_count = 0
            in_progress_count = 0
            done_count = 0

            for ticket in self.tickets:
                # Skip test executions
                if ticket.get("issue_type") in ["Test Execution", "Test"]:
                    continue

                category = self._get_status_category_on_date(ticket, current_date)
                if category == "To Do":
                    todo_count += 1
                elif category == "In Progress":
                    in_progress_count += 1
                elif category == "Done":
                    done_count += 1

            daily_metrics.append({
                "date": current_date,
                "todo": todo_count,
                "in_progress": in_progress_count,
                "done": done_count,
                "total": todo_count + in_progress_count + done_count,
            })

        return pl.DataFrame(daily_metrics)

    def create_status_category_chart(
        self,
        start_date: str,
        end_date: str,
        title: str = "Status Category Distribution Day by Day"
    ) -> str:
        """
        Create stacked bar chart showing status category distribution.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            title: Chart title

        Returns:
            HTML string of the chart
        """
        metrics_df = self.calculate_daily_status_categories(start_date, end_date)

        if metrics_df.is_empty():
            return "<p>No data available for the specified date range.</p>"

        dates = metrics_df["date"].to_list()
        todo = metrics_df["todo"].to_list()
        in_progress = metrics_df["in_progress"].to_list()
        done = metrics_df["done"].to_list()

        # Create figure
        fig = go.Figure()

        # To Do bar
        fig.add_trace(go.Bar(
            x=dates,
            y=todo,
            name="To Do",
            marker_color="#95a5a6",
            hovertemplate="<b>%{x|%Y-%m-%d}</b><br>To Do: %{y}<extra></extra>",
        ))

        # In Progress bar
        fig.add_trace(go.Bar(
            x=dates,
            y=in_progress,
            name="In Progress",
            marker_color="#f39c12",
            hovertemplate="<b>%{x|%Y-%m-%d}</b><br>In Progress: %{y}<extra></extra>",
        ))

        # Done bar
        fig.add_trace(go.Bar(
            x=dates,
            y=done,
            name="Done",
            marker_color="#2ecc71",
            hovertemplate="<b>%{x|%Y-%m-%d}</b><br>Done: %{y}<extra></extra>",
        ))

        # Update layout for stacked bar chart
        fig.update_layout(
            title=title,
            xaxis_title="Date",
            yaxis_title="Number of Issues",
            barmode='stack',
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
        Get summary statistics for status categories.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            Dictionary with summary statistics
        """
        metrics_df = self.calculate_daily_status_categories(start_date, end_date)

        if metrics_df.is_empty():
            return {
                "avg_todo": 0,
                "avg_in_progress": 0,
                "avg_done": 0,
                "final_todo": 0,
                "final_in_progress": 0,
                "final_done": 0,
            }

        return {
            "avg_todo": metrics_df["todo"].mean(),
            "avg_in_progress": metrics_df["in_progress"].mean(),
            "avg_done": metrics_df["done"].mean(),
            "final_todo": metrics_df["todo"][-1] if len(metrics_df) > 0 else 0,
            "final_in_progress": metrics_df["in_progress"][-1] if len(metrics_df) > 0 else 0,
            "final_done": metrics_df["done"][-1] if len(metrics_df) > 0 else 0,
        }
