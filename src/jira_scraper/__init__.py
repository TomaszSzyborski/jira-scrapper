"""Jira Scraper - A tool for extracting data from Jira instances."""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .scraper import JiraScraper
from .analyzer import JiraAnalyzer
from .report_generator import ReportGenerator
from .issue_trends_chart import IssueTrendsChart
from .xray_test_chart import XrayTestChart
from .models import ReportConfig, Ticket, StatusTransition, FlowMetrics, CycleMetrics

__all__ = [
    "JiraScraper",
    "JiraAnalyzer",
    "ReportGenerator",
    "IssueTrendsChart",
    "XrayTestChart",
    "ReportConfig",
    "Ticket",
    "StatusTransition",
    "FlowMetrics",
    "CycleMetrics",
]