"""
Jira Bug Flow Analyzer Package.

A comprehensive tool for analyzing Jira bug workflows, detecting rework loops,
and generating detailed HTML reports with interactive visualizations.

Modules:
    fetcher: Jira API connection and data fetching
    analyzer: Bug flow analysis and metrics calculation
    reporter: HTML report generation with Plotly.js visualizations
    models: Pydantic data models for validation and type safety
"""

from .fetcher import JiraFetcher
from .analyzer import FlowAnalyzer
from .reporter import ReportGenerator
from .models import (
    JiraIssue,
    ChangelogEntry,
    IssueSnapshot,
    StatusCategory,
    StatusMetrics,
    FlowPattern,
    DailyMetrics,
    ProjectMetrics,
    is_correct_flow,
    CORRECT_WORKFLOW,
)

__version__ = "2.0.0"
__all__ = [
    "JiraFetcher",
    "FlowAnalyzer",
    "ReportGenerator",
    "JiraIssue",
    "ChangelogEntry",
    "IssueSnapshot",
    "StatusCategory",
    "StatusMetrics",
    "FlowPattern",
    "DailyMetrics",
    "ProjectMetrics",
    "is_correct_flow",
    "CORRECT_WORKFLOW",
]
