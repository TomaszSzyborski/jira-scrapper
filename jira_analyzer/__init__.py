"""
Jira Bug Flow Analyzer Package.

A comprehensive tool for analyzing Jira bug workflows, detecting rework loops,
and generating detailed HTML reports with interactive visualizations.

Modules:
    fetcher: Jira API connection and data fetching
    analyzer: Bug flow analysis and metrics calculation
    reporter: HTML report generation with Plotly.js visualizations
"""

from .fetcher import JiraFetcher
from .analyzer import FlowAnalyzer
from .reporter import ReportGenerator

__version__ = "2.0.0"
__all__ = ["JiraFetcher", "FlowAnalyzer", "ReportGenerator"]
