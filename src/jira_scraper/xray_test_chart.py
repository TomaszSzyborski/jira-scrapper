"""Xray test execution progress visualization module."""

from datetime import datetime
from typing import List, Dict, Any, Optional
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from collections import defaultdict, Counter


class XrayTestChart:
    """Generates charts for Xray test execution progress (On-Premise and Cloud compatible)."""

    # Xray test execution statuses (On-Premise)
    # On-Premise Xray uses workflow statuses, which can be customized
    # These are the most common default statuses
    XRAY_STATUSES = {
        # Cloud/API statuses
        "PASS": "Passed",
        "FAIL": "Failed",
        "EXECUTING": "Executing",
        "TODO": "To Do",
        "ABORTED": "Aborted",
        # On-Premise workflow statuses (common defaults)
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
        # Additional common statuses
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

    def __init__(self, test_executions: List[Dict[str, Any]], target_label: Optional[str] = None):
        """
        Initialize with test execution data.

        Args:
            test_executions: List of Xray test execution issues
            target_label: Optional label to filter test executions
        """
        self.test_executions = test_executions
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

    def calculate_test_metrics(self) -> Dict[str, Any]:
        """
        Calculate test execution metrics (compatible with On-Premise and Cloud).

        For On-Premise Xray, we check both the main status field and xray_data.

        Returns:
            Dictionary with test metrics
        """
        status_counts = defaultdict(int)
        total_tests = len(self.filtered_executions)

        for execution in self.filtered_executions:
            # Try multiple sources for status (On-Premise compatibility)
            status = None

            # First, check if there's Xray-specific data from On-Premise
            xray_data = execution.get("xray_data", {})
            if xray_data and xray_data.get("is_test_execution"):
                status = xray_data.get("test_execution_status")

            # Fallback to main status field
            if not status:
                status = execution.get("status", "To Do")

            # Normalize status using our mapping
            normalized_status = self.XRAY_STATUSES.get(status, "To Do")

            # If still not recognized, try to infer from status name
            if normalized_status == "To Do" and status not in ["To Do", "TODO", "Open", "Unexecuted"]:
                status_lower = status.lower()
                if "pass" in status_lower or "success" in status_lower or "done" in status_lower:
                    normalized_status = "Passed"
                elif "fail" in status_lower or "error" in status_lower:
                    normalized_status = "Failed"
                elif "progress" in status_lower or "executing" in status_lower or "running" in status_lower:
                    normalized_status = "Executing"
                elif "abort" in status_lower or "block" in status_lower or "cancel" in status_lower:
                    normalized_status = "Aborted"

            status_counts[normalized_status] += 1

        # Calculate coverage and progress
        completed = status_counts.get("Passed", 0) + status_counts.get("Failed", 0)
        in_progress = status_counts.get("Executing", 0)
        aborted = status_counts.get("Aborted", 0)
        todo = status_counts.get("To Do", 0)

        coverage_percent = (completed / total_tests * 100) if total_tests > 0 else 0
        progress_percent = ((completed + in_progress) / total_tests * 100) if total_tests > 0 else 0

        return {
            "total_tests": total_tests,
            "passed": status_counts.get("Passed", 0),
            "failed": status_counts.get("Failed", 0),
            "executing": in_progress,
            "todo": todo,
            "aborted": aborted,
            "completed": completed,
            "coverage_percent": round(coverage_percent, 2),
            "progress_percent": round(progress_percent, 2),
            "remaining_for_100_percent": todo,
        }

    def create_progress_pie_chart(self, title: str = "Test Execution Progress") -> str:
        """
        Create pie chart showing test execution status distribution.

        Args:
            title: Chart title

        Returns:
            HTML string of the chart
        """
        metrics = self.calculate_test_metrics()

        labels = []
        values = []
        colors = []

        for status in ["Passed", "Failed", "Executing", "To Do", "Aborted"]:
            key = status.lower().replace(" ", "_")
            value = metrics.get(key, 0)
            if value > 0:
                labels.append(status)
                values.append(value)
                colors.append(self.STATUS_COLORS[status])

        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            marker=dict(colors=colors),
            hole=0.3,
            textinfo="label+percent+value",
            hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>",
        )])

        fig.update_layout(
            title=title,
            showlegend=True,
            height=500,
            template="plotly_white",
        )

        return fig.to_html(full_html=False, include_plotlyjs="cdn")

    def create_progress_bar_chart(self, title: str = "Test Execution Status") -> str:
        """
        Create horizontal bar chart showing test execution counts.

        Args:
            title: Chart title

        Returns:
            HTML string of the chart
        """
        metrics = self.calculate_test_metrics()

        statuses = ["Passed", "Failed", "Executing", "To Do", "Aborted"]
        counts = [
            metrics.get("passed", 0),
            metrics.get("failed", 0),
            metrics.get("executing", 0),
            metrics.get("todo", 0),
            metrics.get("aborted", 0),
        ]
        colors = [self.STATUS_COLORS[status] for status in statuses]

        fig = go.Figure(data=[go.Bar(
            y=statuses,
            x=counts,
            orientation="h",
            marker=dict(color=colors),
            text=counts,
            textposition="auto",
            hovertemplate="<b>%{y}</b><br>Count: %{x}<extra></extra>",
        )])

        fig.update_layout(
            title=title,
            xaxis_title="Number of Tests",
            yaxis_title="Status",
            height=400,
            template="plotly_white",
        )

        return fig.to_html(full_html=False, include_plotlyjs="cdn")

    def create_coverage_gauge(self) -> str:
        """
        Create gauge chart showing test coverage percentage.

        Returns:
            HTML string of the chart
        """
        metrics = self.calculate_test_metrics()
        coverage = metrics["coverage_percent"]

        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=coverage,
            domain={"x": [0, 1], "y": [0, 1]},
            title={"text": "Test Coverage (Completed Tests)"},
            delta={"reference": 100},
            gauge={
                "axis": {"range": [None, 100]},
                "bar": {"color": "#3498db"},
                "steps": [
                    {"range": [0, 50], "color": "#e74c3c"},
                    {"range": [50, 80], "color": "#f39c12"},
                    {"range": [80, 100], "color": "#2ecc71"},
                ],
                "threshold": {
                    "line": {"color": "red", "width": 4},
                    "thickness": 0.75,
                    "value": 100,
                },
            },
        ))

        fig.update_layout(
            height=400,
            template="plotly_white",
        )

        return fig.to_html(full_html=False, include_plotlyjs="cdn")

    def create_release_readiness_chart(self) -> str:
        """
        Create stacked bar chart showing release readiness.

        Returns:
            HTML string of the chart
        """
        metrics = self.calculate_test_metrics()

        categories = ["Test Execution Progress"]
        completed = metrics["completed"]
        in_progress = metrics["executing"]
        remaining = metrics["remaining_for_100_percent"]
        aborted = metrics["aborted"]

        fig = go.Figure()

        fig.add_trace(go.Bar(
            name="Completed",
            x=categories,
            y=[completed],
            marker_color="#2ecc71",
            text=[f"{completed} ({metrics['coverage_percent']}%)"],
            textposition="inside",
        ))

        fig.add_trace(go.Bar(
            name="In Progress",
            x=categories,
            y=[in_progress],
            marker_color="#3498db",
            text=[in_progress],
            textposition="inside",
        ))

        fig.add_trace(go.Bar(
            name="Remaining",
            x=categories,
            y=[remaining],
            marker_color="#95a5a6",
            text=[remaining],
            textposition="inside",
        ))

        fig.add_trace(go.Bar(
            name="Aborted",
            x=categories,
            y=[aborted],
            marker_color="#e67e22",
            text=[aborted],
            textposition="inside",
        ))

        fig.update_layout(
            title="Release Readiness - Test Execution Overview",
            barmode="stack",
            yaxis_title="Number of Tests",
            height=400,
            template="plotly_white",
            showlegend=True,
        )

        return fig.to_html(full_html=False, include_plotlyjs="cdn")

    def create_summary_table_html(self) -> str:
        """
        Create HTML table with summary statistics.

        Returns:
            HTML string of the summary table
        """
        metrics = self.calculate_test_metrics()

        html = """
        <div style="margin: 20px 0;">
            <h3>Test Execution Summary</h3>
            <table style="border-collapse: collapse; width: 100%; max-width: 600px;">
                <tr style="background-color: #f8f9fa;">
                    <th style="border: 1px solid #dee2e6; padding: 12px; text-align: left;">Metric</th>
                    <th style="border: 1px solid #dee2e6; padding: 12px; text-align: right;">Value</th>
                </tr>
                <tr>
                    <td style="border: 1px solid #dee2e6; padding: 10px;">Total Tests</td>
                    <td style="border: 1px solid #dee2e6; padding: 10px; text-align: right; font-weight: bold;">{total_tests}</td>
                </tr>
                <tr style="background-color: #d4edda;">
                    <td style="border: 1px solid #dee2e6; padding: 10px;">Tests Passed</td>
                    <td style="border: 1px solid #dee2e6; padding: 10px; text-align: right; font-weight: bold; color: #2ecc71;">{passed}</td>
                </tr>
                <tr style="background-color: #f8d7da;">
                    <td style="border: 1px solid #dee2e6; padding: 10px;">Tests Failed</td>
                    <td style="border: 1px solid #dee2e6; padding: 10px; text-align: right; font-weight: bold; color: #e74c3c;">{failed}</td>
                </tr>
                <tr style="background-color: #d1ecf1;">
                    <td style="border: 1px solid #dee2e6; padding: 10px;">Tests Executing</td>
                    <td style="border: 1px solid #dee2e6; padding: 10px; text-align: right; font-weight: bold; color: #3498db;">{executing}</td>
                </tr>
                <tr>
                    <td style="border: 1px solid #dee2e6; padding: 10px;">Tests To Do</td>
                    <td style="border: 1px solid #dee2e6; padding: 10px; text-align: right; font-weight: bold;">{todo}</td>
                </tr>
                <tr style="background-color: #fff3cd;">
                    <td style="border: 1px solid #dee2e6; padding: 10px;">Tests Aborted</td>
                    <td style="border: 1px solid #dee2e6; padding: 10px; text-align: right; font-weight: bold; color: #e67e22;">{aborted}</td>
                </tr>
                <tr style="background-color: #e7f3ff;">
                    <td style="border: 1px solid #dee2e6; padding: 10px; font-weight: bold;">Coverage (Completed)</td>
                    <td style="border: 1px solid #dee2e6; padding: 10px; text-align: right; font-weight: bold; color: #3498db;">{coverage_percent}%</td>
                </tr>
                <tr style="background-color: #fff9e6;">
                    <td style="border: 1px solid #dee2e6; padding: 10px; font-weight: bold;">Remaining for 100%</td>
                    <td style="border: 1px solid #dee2e6; padding: 10px; text-align: right; font-weight: bold; color: #f39c12;">{remaining_for_100_percent}</td>
                </tr>
            </table>
        </div>
        """.format(**metrics)

        return html

    def generate_complete_report(self) -> str:
        """
        Generate complete HTML report with all charts and summary.

        Returns:
            Complete HTML string with all visualizations
        """
        summary_table = self.create_summary_table_html()
        pie_chart = self.create_progress_pie_chart()
        bar_chart = self.create_progress_bar_chart()
        gauge_chart = self.create_coverage_gauge()
        readiness_chart = self.create_release_readiness_chart()

        label_info = f"<p><strong>Filtered by label:</strong> {self.target_label}</p>" if self.target_label else ""

        html = f"""
        <div style="font-family: Arial, sans-serif;">
            <h2>Xray Test Execution Progress Report</h2>
            {label_info}
            {summary_table}
            <div style="margin: 30px 0;">
                {readiness_chart}
            </div>
            <div style="margin: 30px 0;">
                {gauge_chart}
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 30px 0;">
                <div>{pie_chart}</div>
                <div>{bar_chart}</div>
            </div>
        </div>
        """

        return html
