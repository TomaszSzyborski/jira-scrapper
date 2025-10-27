"""Cumulative test execution tracking with status breakdown and drilldown."""

from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import polars as pl
import plotly.graph_objects as go
from collections import defaultdict


class TestExecutionCumulativeChart:
    """Generates cumulative test execution charts with status tracking."""

    # Xray test execution statuses mapping
    XRAY_STATUSES = {
        "PASS": "Passed",
        "FAIL": "Failed",
        "EXECUTING": "Executing",
        "TODO": "To Do",
        "ABORTED": "Aborted",
        "Passed": "Passed",
        "Failed": "Failed",
        "PASSED": "Passed",
        "FAILED": "Failed",
        "Executing": "Executing",
        "In Progress": "Executing",
        "To Do": "To Do",
        "TODO": "To Do",
        "Open": "To Do",
        "Aborted": "Aborted",
        "ABORTED": "Aborted",
        "Blocked": "Aborted",
        "Done": "Passed",
        "Closed": "Passed",
        "Unexecuted": "To Do",
    }

    STATUS_COLORS = {
        "Passed": "#2ecc71",
        "Failed": "#e74c3c",
        "Executing": "#3498db",
        "To Do": "#95a5a6",
        "Aborted": "#e67e22",
    }

    def __init__(self, test_executions: List[Dict[str, Any]], jira_url: str = "", target_label: Optional[str] = None):
        """
        Initialize with test execution data.

        Args:
            test_executions: List of test execution issues
            jira_url: Base URL of Jira instance for generating links
            target_label: Optional label to filter test executions
        """
        self.test_executions = test_executions
        self.jira_url = jira_url
        if self.jira_url and self.jira_url.endswith("/"):
            self.jira_url = self.jira_url[:-1]
        self.target_label = target_label
        self.filtered_executions = self._filter_by_label()

    def _filter_by_label(self) -> List[Dict[str, Any]]:
        """
        Filter test executions by target label if specified.

        Returns:
            Filtered list of test executions
        """
        if not self.target_label:
            return self.test_executions

        filtered = []
        for execution in self.test_executions:
            labels = execution.get("labels", [])
            if self.target_label in labels:
                filtered.append(execution)

        return filtered

    def _normalize_status(self, status: str, xray_data: Dict[str, Any]) -> str:
        """
        Normalize test execution status.

        Args:
            status: Raw status string
            xray_data: Xray-specific data

        Returns:
            Normalized status
        """
        # Check xray_data first
        if xray_data and xray_data.get("is_test_execution"):
            status = xray_data.get("test_execution_status") or status

        # Normalize using mapping
        normalized = self.XRAY_STATUSES.get(status, "To Do")

        # Heuristic detection for custom statuses
        if normalized == "To Do" and status not in ["To Do", "TODO", "Open", "Unexecuted"]:
            status_lower = status.lower()
            if "pass" in status_lower or "success" in status_lower or "done" in status_lower:
                normalized = "Passed"
            elif "fail" in status_lower or "error" in status_lower:
                normalized = "Failed"
            elif "progress" in status_lower or "executing" in status_lower or "running" in status_lower:
                normalized = "Executing"
            elif "abort" in status_lower or "block" in status_lower or "cancel" in status_lower:
                normalized = "Aborted"

        return normalized

    def calculate_cumulative_metrics(
        self,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """
        Calculate cumulative test execution metrics over time.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            Dictionary with cumulative metrics by date and status
        """
        if not self.filtered_executions:
            return {}

        start = datetime.fromisoformat(start_date).replace(tzinfo=timezone.utc)
        end = datetime.fromisoformat(end_date).replace(tzinfo=timezone.utc)

        # Generate date range
        date_range = pl.datetime_range(start, end, interval="1d", eager=True, time_zone="UTC")

        cumulative_data = []
        status_by_date = defaultdict(lambda: defaultdict(list))

        for current_date in date_range:
            date_str = current_date.strftime("%Y-%m-%d")

            # Count tests by status that were updated by this date
            status_counts = defaultdict(int)
            status_tests = defaultdict(list)

            for test in self.filtered_executions:
                updated = datetime.fromisoformat(test["updated"].replace("Z", "+00:00"))

                # Only include tests updated before or on this date
                if updated.date() <= current_date.date():
                    xray_data = test.get("xray_data", {})
                    status = self._normalize_status(test.get("status", "To Do"), xray_data)

                    status_counts[status] += 1
                    status_tests[status].append(test["key"])

            # Store for drilldown
            for status, keys in status_tests.items():
                status_by_date[date_str][status] = keys

            cumulative_data.append({
                "date": current_date,
                "passed": status_counts["Passed"],
                "failed": status_counts["Failed"],
                "executing": status_counts["Executing"],
                "todo": status_counts["To Do"],
                "aborted": status_counts["Aborted"],
                "total": sum(status_counts.values()),
            })

        return {
            "cumulative_data": cumulative_data,
            "status_by_date": dict(status_by_date),
        }

    def create_cumulative_chart(
        self,
        start_date: str,
        end_date: str,
        title: Optional[str] = None
    ) -> str:
        """
        Create stacked area chart showing cumulative test execution status.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            title: Chart title

        Returns:
            HTML string of the chart
        """
        metrics = self.calculate_cumulative_metrics(start_date, end_date)

        if not metrics:
            return "<p>No test execution data available for the specified date range.</p>"

        cumulative_data = metrics["cumulative_data"]
        dates = [d["date"] for d in cumulative_data]

        # Create stacked area chart
        fig = go.Figure()

        # Add traces in order (bottom to top of stack)
        fig.add_trace(go.Scatter(
            x=dates,
            y=[d["passed"] for d in cumulative_data],
            name="Passed",
            mode="lines",
            stackgroup="one",
            fillcolor=self.STATUS_COLORS["Passed"],
            line=dict(width=0.5, color=self.STATUS_COLORS["Passed"]),
            hovertemplate="<b>%{x|%Y-%m-%d}</b><br>Passed: %{y}<extra></extra>",
        ))

        fig.add_trace(go.Scatter(
            x=dates,
            y=[d["failed"] for d in cumulative_data],
            name="Failed",
            mode="lines",
            stackgroup="one",
            fillcolor=self.STATUS_COLORS["Failed"],
            line=dict(width=0.5, color=self.STATUS_COLORS["Failed"]),
            hovertemplate="<b>%{x|%Y-%m-%d}</b><br>Failed: %{y}<extra></extra>",
        ))

        fig.add_trace(go.Scatter(
            x=dates,
            y=[d["executing"] for d in cumulative_data],
            name="Executing",
            mode="lines",
            stackgroup="one",
            fillcolor=self.STATUS_COLORS["Executing"],
            line=dict(width=0.5, color=self.STATUS_COLORS["Executing"]),
            hovertemplate="<b>%{x|%Y-%m-%d}</b><br>Executing: %{y}<extra></extra>",
        ))

        fig.add_trace(go.Scatter(
            x=dates,
            y=[d["todo"] for d in cumulative_data],
            name="To Do",
            mode="lines",
            stackgroup="one",
            fillcolor=self.STATUS_COLORS["To Do"],
            line=dict(width=0.5, color=self.STATUS_COLORS["To Do"]),
            hovertemplate="<b>%{x|%Y-%m-%d}</b><br>To Do: %{y}<extra></extra>",
        ))

        fig.add_trace(go.Scatter(
            x=dates,
            y=[d["aborted"] for d in cumulative_data],
            name="Aborted",
            mode="lines",
            stackgroup="one",
            fillcolor=self.STATUS_COLORS["Aborted"],
            line=dict(width=0.5, color=self.STATUS_COLORS["Aborted"]),
            hovertemplate="<b>%{x|%Y-%m-%d}</b><br>Aborted: %{y}<extra></extra>",
        ))

        # Update layout
        if not title:
            title = f"Cumulative Test Execution Progress"
            if self.target_label:
                title += f" (Label: {self.target_label})"

        fig.update_layout(
            title=title,
            xaxis_title="Date",
            yaxis_title="Number of Tests",
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

    def get_test_execution_drilldown(
        self,
        start_date: str,
        end_date: str
    ) -> str:
        """
        Generate HTML with test execution drilldown by date.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            HTML string with test execution details
        """
        metrics = self.calculate_cumulative_metrics(start_date, end_date)

        if not metrics:
            return ""

        cumulative_data = metrics["cumulative_data"]
        status_by_date = metrics["status_by_date"]

        html = '<h3>Test Execution Details</h3>'
        html += '<p style="font-size: 0.9rem; color: #666; margin-bottom: 15px;">Click on a date to see test execution details</p>'

        # Show only dates with changes (skip first date or dates with no activity)
        prev_totals = {}
        for idx, data in enumerate(cumulative_data):
            date = data["date"]
            date_str = date.strftime("%Y-%m-%d")

            current_totals = {
                "Passed": data["passed"],
                "Failed": data["failed"],
                "Executing": data["executing"],
                "To Do": data["todo"],
                "Aborted": data["aborted"],
            }

            # Skip if no change from previous date (except first date)
            if idx > 0 and current_totals == prev_totals:
                continue

            prev_totals = current_totals

            if data["total"] == 0:
                continue

            html += f'''
            <div class="pattern-row">
                <div class="pattern-header" onclick="togglePattern('test-date-{idx}')">
                    <span class="pattern-arrow">▶</span>
                    <span class="pattern-text">{date_str}</span>
                    <span class="pattern-count" style="background: {self.STATUS_COLORS["Passed"]};">✓ {data["passed"]}</span>
                    <span class="pattern-count" style="background: {self.STATUS_COLORS["Failed"]};">✗ {data["failed"]}</span>
                    <span class="pattern-count" style="background: {self.STATUS_COLORS["Executing"]};">⟳ {data["executing"]}</span>
                    <span class="pattern-count" style="background: {self.STATUS_COLORS["To Do"]};">◯ {data["todo"]}</span>
                    <span class="pattern-count" style="background: {self.STATUS_COLORS["Aborted"]};">⊗ {data["aborted"]}</span>
                </div>
                <div id="test-date-{idx}" class="pattern-details" style="display: none;">
            '''

            # Show tests for each status
            for status in ["Passed", "Failed", "Executing", "To Do", "Aborted"]:
                test_keys = status_by_date.get(date_str, {}).get(status, [])
                count = len(test_keys)

                if count == 0:
                    continue

                html += f'<div class="ticket-list" style="margin-bottom: 20px;">'
                html += f'<h4 style="color: {self.STATUS_COLORS[status]};">{status} Tests ({count})</h4>'
                html += '<table class="ticket-table">'
                html += '<tr><th>Key</th><th>Summary</th><th>Status</th><th>Updated</th></tr>'

                for test_key in test_keys:
                    test = next((t for t in self.filtered_executions if t["key"] == test_key), None)
                    if test:
                        test_link = f"{self.jira_url}/browse/{test_key}" if self.jira_url else "#"
                        summary = test["summary"][:60] + "..." if len(test["summary"]) > 60 else test["summary"]
                        updated_date = datetime.fromisoformat(test["updated"].replace("Z", "+00:00")).strftime("%Y-%m-%d")

                        html += f'''
                        <tr>
                            <td><a href="{test_link}" target="_blank" class="ticket-link">{test_key}</a></td>
                            <td>{summary}</td>
                            <td>{test["status"]}</td>
                            <td>{updated_date}</td>
                        </tr>'''

                html += '</table></div>'

            html += '</div></div>'

        return html

    def get_current_status_summary(self, end_date: str) -> Dict[str, Any]:
        """
        Get current status summary at end date.

        Args:
            end_date: End date in YYYY-MM-DD format

        Returns:
            Dictionary with current status counts
        """
        end = datetime.fromisoformat(end_date).replace(tzinfo=timezone.utc)

        status_counts = defaultdict(int)
        for test in self.filtered_executions:
            updated = datetime.fromisoformat(test["updated"].replace("Z", "+00:00"))
            if updated.date() <= end.date():
                xray_data = test.get("xray_data", {})
                status = self._normalize_status(test.get("status", "To Do"), xray_data)
                status_counts[status] += 1

        total = sum(status_counts.values())
        completed = status_counts["Passed"] + status_counts["Failed"]
        coverage = (completed / total * 100) if total > 0 else 0

        return {
            "total": total,
            "passed": status_counts["Passed"],
            "failed": status_counts["Failed"],
            "executing": status_counts["Executing"],
            "todo": status_counts["To Do"],
            "aborted": status_counts["Aborted"],
            "completed": completed,
            "coverage_percent": round(coverage, 2),
            "remaining": status_counts["To Do"],
        }
