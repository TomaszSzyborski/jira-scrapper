"""Test execution tracking - list of executions and cumulative test case statuses."""

from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import plotly.graph_objects as go
from collections import defaultdict


class TestExecutionChart:
    """Generates test execution list and cumulative test case status chart."""

    # Test case status mapping (what's inside test executions)
    STATUS_MAP = {
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
            test_executions: List of test execution issues (Test Execution type tickets)
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
        """Filter test executions by target label if specified."""
        if not self.target_label:
            return self.test_executions

        filtered = []
        for execution in self.test_executions:
            labels = execution.get("labels", [])
            if self.target_label in labels:
                filtered.append(execution)

        return filtered

    def _normalize_status(self, status: str) -> str:
        """
        Normalize test case status.

        Args:
            status: Raw status string

        Returns:
            Normalized status (Passed, Failed, Executing, To Do, Aborted)
        """
        # Normalize using mapping
        normalized = self.STATUS_MAP.get(status, "To Do")

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

    def get_current_test_executions_list(self) -> str:
        """
        Generate HTML table listing current test executions.

        Returns:
            HTML string with test execution list
        """
        if not self.filtered_executions:
            return "<p>No test executions found.</p>"

        html = '<h3 data-i18n="current_test_executions">Current Test Executions</h3>'
        html += '<table class="ticket-table">'
        html += '<tr>'
        html += '<th data-i18n="key">Key</th>'
        html += '<th data-i18n="summary">Summary</th>'
        html += '<th data-i18n="status">Status</th>'
        html += '<th>Test Cases</th>'
        html += '<th data-i18n="created">Created</th>'
        html += '<th data-i18n="updated">Updated</th>'
        html += '</tr>'

        for execution in sorted(self.filtered_executions, key=lambda x: x.get("created", ""), reverse=True):
            key = execution["key"]
            link = f"{self.jira_url}/browse/{key}" if self.jira_url else "#"
            summary = execution["summary"][:60] + "..." if len(execution["summary"]) > 60 else execution["summary"]
            status = execution.get("status", "Unknown")
            created = datetime.fromisoformat(execution["created"].replace("Z", "+00:00")).strftime("%Y-%m-%d")
            updated = datetime.fromisoformat(execution["updated"].replace("Z", "+00:00")).strftime("%Y-%m-%d")

            # Count test cases (this would need to be extracted from xray_data or linked tests)
            # For now, show a placeholder
            test_count = "N/A"
            xray_data = execution.get("xray_data", {})
            if xray_data.get("test_count"):
                test_count = str(xray_data["test_count"])

            html += f'''
            <tr>
                <td><a href="{link}" target="_blank" class="ticket-link">{key}</a></td>
                <td>{summary}</td>
                <td>{status}</td>
                <td>{test_count}</td>
                <td>{created}</td>
                <td>{updated}</td>
            </tr>'''

        html += '</table>'
        return html

    def get_cumulative_test_case_statuses(self) -> Dict[str, int]:
        """
        Calculate cumulative test case statuses across all test executions.

        This counts the test cases inside test executions, not the test executions themselves.

        Returns:
            Dictionary with status counts
        """
        status_counts = defaultdict(int)

        for execution in self.filtered_executions:
            # Get status from test execution
            # In Xray, test executions contain multiple test cases with different statuses
            # For now, we'll count each test execution's status as one test case
            # TODO: This should be enhanced to extract actual test case statuses from Xray data

            status = execution.get("status", "To Do")
            xray_data = execution.get("xray_data", {})

            # If xray_data has test_execution_status, use it
            if xray_data and xray_data.get("is_test_execution"):
                status = xray_data.get("test_execution_status") or status

            normalized = self._normalize_status(status)
            status_counts[normalized] += 1

        return dict(status_counts)

    def create_cumulative_status_chart(self) -> str:
        """
        Create bar chart showing cumulative test case statuses.

        Returns:
            HTML string of the chart
        """
        status_counts = self.get_cumulative_test_case_statuses()

        if not status_counts:
            return "<p>No test case data available.</p>"

        # Prepare data
        statuses = ["Passed", "Failed", "Executing", "To Do", "Aborted"]
        counts = [status_counts.get(status, 0) for status in statuses]
        colors = [self.STATUS_COLORS[status] for status in statuses]

        # Create bar chart
        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=statuses,
            y=counts,
            marker_color=colors,
            text=counts,
            textposition='auto',
            hovertemplate="<b>%{x}</b><br>Count: %{y}<extra></extra>",
        ))

        # Update layout
        fig.update_layout(
            title="Cumulative Test Case Statuses (All Test Executions)",
            xaxis_title="Status",
            yaxis_title="Number of Test Cases",
            template="plotly_white",
            height=400,
            showlegend=False,
        )

        return fig.to_html(full_html=False, include_plotlyjs="cdn")

    def get_summary_statistics(self) -> Dict[str, Any]:
        """
        Get summary statistics for test executions.

        Returns:
            Dictionary with summary statistics
        """
        status_counts = self.get_cumulative_test_case_statuses()

        total = sum(status_counts.values())
        passed = status_counts.get("Passed", 0)
        failed = status_counts.get("Failed", 0)
        executing = status_counts.get("Executing", 0)
        todo = status_counts.get("To Do", 0)
        aborted = status_counts.get("Aborted", 0)

        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "executing": executing,
            "todo": todo,
            "aborted": aborted,
            "remaining": todo + executing,
            "completed": passed + failed,
            "test_executions_count": len(self.filtered_executions),
        }
