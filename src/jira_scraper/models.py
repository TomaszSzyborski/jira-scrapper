"""Data models and configuration structures."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ReportConfig:
    """Configuration for report generation."""

    granularity: str = "daily"  # "daily" or "weekly"
    include_changelog: bool = True
    track_custom_fields: List[str] = field(default_factory=lambda: ["Story Points", "Sprint"])
    status_categories: Dict[str, List[str]] = field(
        default_factory=lambda: {
            "in_progress": ["In Progress", "In Development"],
            "testing": ["To Test", "In Testing", "QA"],
            "blocked": ["Blocked", "On Hold"],
            "done": ["Done", "Closed", "Resolved"],
        }
    )
    max_retries: int = 3
    backoff_factor: int = 2
    requests_per_minute: int = 60
    batch_size: int = 100
    cache_enabled: bool = False
    cache_ttl: int = 3600  # seconds


@dataclass
class Ticket:
    """Represents a Jira ticket."""

    key: str
    summary: str
    status: str
    issue_type: str
    priority: Optional[str]
    created: str
    updated: str
    resolved: Optional[str]
    assignee: Optional[str]
    reporter: Optional[str]
    labels: List[str] = field(default_factory=list)
    components: List[str] = field(default_factory=list)
    changelog: List["StatusTransition"] = field(default_factory=list)
    story_points: Optional[float] = None


@dataclass
class StatusTransition:
    """Represents a status change in ticket history."""

    timestamp: str
    from_status: str
    to_status: str
    author: str


@dataclass
class FlowMetrics:
    """Flow analysis metrics."""

    total_transitions: int
    unique_patterns: int
    regression_count: int
    bounce_rate: float
    most_common_patterns: List[Dict[str, any]]
    time_in_status: Dict[str, float]


@dataclass
class CycleMetrics:
    """Cycle time and throughput metrics."""

    avg_lead_time: float
    median_lead_time: float
    avg_cycle_time: float
    median_cycle_time: float
    throughput: int
    lead_times: List[float] = field(default_factory=list)
    cycle_times: List[float] = field(default_factory=list)


@dataclass
class SummaryStatistics:
    """Overall summary statistics."""

    total_tickets: int
    resolved_tickets: int
    in_progress_tickets: int
    issue_type_distribution: Dict[str, int]
    priority_distribution: Dict[str, int]
    status_distribution: Dict[str, int]


@dataclass
class ProjectInfo:
    """Jira project information."""

    key: str
    name: str
    description: str
    lead: Optional[str]


@dataclass
class AnalysisResult:
    """Complete analysis result."""

    project_info: ProjectInfo
    summary_stats: SummaryStatistics
    flow_metrics: FlowMetrics
    cycle_metrics: CycleMetrics
    start_date: str
    end_date: str
    generated_at: str
