"""Jira Scraper - A tool for extracting data from Jira instances."""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .scraper import JiraScraper
from .analyzer import JiraAnalyzer
from .report_generator import ReportGenerator
from .issue_trends_chart import IssueTrendsChart
from .xray_test_chart import XrayTestChart
from .bug_tracking_chart import BugTrackingChart
from .test_execution_cumulative_chart import TestExecutionCumulativeChart
from .in_progress_tracking_chart import InProgressTrackingChart
from .models import ReportConfig, Ticket, StatusTransition, FlowMetrics, CycleMetrics
from .jql_queries import JQLQueries

__all__ = [
    "JiraScraper",
    "JiraAnalyzer",
    "ReportGenerator",
    "IssueTrendsChart",
    "XrayTestChart",
    "BugTrackingChart",
    "TestExecutionCumulativeChart",
    "InProgressTrackingChart",
    "JQLQueries",
    "ReportConfig",
    "Ticket",
    "StatusTransition",
    "FlowMetrics",
    "CycleMetrics",
]