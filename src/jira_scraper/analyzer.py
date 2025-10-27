"""Data analysis and metrics calculation module."""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple, Optional
import polars as pl
from collections import defaultdict, Counter


class JiraAnalyzer:
    """Analyzes Jira ticket data and calculates metrics."""

    def __init__(self, tickets: List[Dict[str, Any]], jira_url: Optional[str] = None):
        """
        Initialize analyzer with ticket data.

        Args:
            tickets: List of ticket dictionaries from JiraScraper
            jira_url: Base URL of Jira instance for generating ticket links
        """
        self.tickets = tickets
        self.df: Optional[pl.DataFrame] = None
        self.transitions_df: Optional[pl.DataFrame] = None
        self.jira_url = jira_url or ""
        # Clean up URL (remove trailing slash)
        if self.jira_url.endswith("/"):
            self.jira_url = self.jira_url[:-1]

    def build_dataframes(self) -> Tuple[pl.DataFrame, pl.DataFrame]:
        """
        Convert raw ticket data into Polars DataFrames.

        Returns:
            Tuple of (tickets_df, transitions_df)
        """
        # Build tickets DataFrame
        ticket_records = []
        for ticket in self.tickets:
            ticket_records.append({
                "key": ticket["key"],
                "summary": ticket["summary"],
                "status": ticket["status"],
                "issue_type": ticket["issue_type"],
                "priority": ticket["priority"],
                "created": datetime.fromisoformat(ticket["created"].replace("Z", "+00:00")),
                "updated": datetime.fromisoformat(ticket["updated"].replace("Z", "+00:00")),
                "resolved": datetime.fromisoformat(ticket["resolved"].replace("Z", "+00:00"))
                if ticket["resolved"] else None,
                "assignee": ticket["assignee"],
                "reporter": ticket["reporter"],
                "story_points": ticket.get("story_points"),
            })

        self.df = pl.DataFrame(ticket_records)

        # Build transitions DataFrame
        transition_records = []
        for ticket in self.tickets:
            for transition in ticket["changelog"]:
                transition_records.append({
                    "ticket_key": ticket["key"],
                    "timestamp": datetime.fromisoformat(transition["timestamp"].replace("Z", "+00:00")),
                    "from_status": transition["from_status"],
                    "to_status": transition["to_status"],
                    "author": transition["author"],
                })

        self.transitions_df = pl.DataFrame(transition_records) if transition_records else pl.DataFrame()

        return self.df, self.transitions_df

    def calculate_flow_metrics(self) -> Dict[str, Any]:
        """
        Calculate ticket flow metrics and patterns.

        Returns:
            Dictionary with flow analysis results
        """
        if self.transitions_df.is_empty():
            return {"error": "No transitions available"}

        # Count status transitions
        transitions = (
            self.transitions_df
            .group_by(["from_status", "to_status"])
            .agg(pl.count().alias("count"))
            .sort("count", descending=True)
        )

        # Identify regression patterns (backward movements)
        regressions = self._identify_regressions()

        # Calculate average time in each status
        time_in_status = self._calculate_time_in_status()

        # Find most common flow patterns
        flow_patterns = self._find_flow_patterns()

        return {
            "transitions": transitions.to_dicts(),
            "regressions": regressions,
            "time_in_status": time_in_status,
            "flow_patterns": flow_patterns,
            "total_transitions": len(self.transitions_df),
        }

    def _identify_regressions(self) -> Dict[str, Any]:
        """
        Identify tickets that moved backward in the workflow.

        Returns:
            Dictionary with regression analysis
        """
        # Define typical workflow order (can be customized)
        workflow_order = {
            "To Do": 1,
            "In Progress": 2,
            "In Development": 2,
            "To Test": 3,
            "In Testing": 3,
            "QA": 3,
            "Done": 4,
            "Closed": 4,
            "Resolved": 4,
        }

        regressions = []
        for ticket_key in self.transitions_df["ticket_key"].unique():
            ticket_transitions = (
                self.transitions_df
                .filter(pl.col("ticket_key") == ticket_key)
                .sort("timestamp")
            )

            for i in range(len(ticket_transitions)):
                row = ticket_transitions.row(i, named=True)
                from_order = workflow_order.get(row["from_status"], 0)
                to_order = workflow_order.get(row["to_status"], 0)

                if to_order < from_order:
                    regressions.append({
                        "ticket_key": ticket_key,
                        "from_status": row["from_status"],
                        "to_status": row["to_status"],
                        "timestamp": row["timestamp"],
                    })

        return {
            "count": len(regressions),
            "examples": regressions[:10],  # Top 10 examples
            "bounce_rate": len(regressions) / len(self.df) if len(self.df) > 0 else 0,
        }

    def _calculate_time_in_status(self) -> Dict[str, float]:
        """
        Calculate average time spent in each status.

        Returns:
            Dictionary mapping status to average days
        """
        time_in_status = defaultdict(list)

        for ticket_key in self.transitions_df["ticket_key"].unique():
            ticket_transitions = (
                self.transitions_df
                .filter(pl.col("ticket_key") == ticket_key)
                .sort("timestamp")
            )

            for i in range(len(ticket_transitions) - 1):
                current = ticket_transitions.row(i, named=True)
                next_trans = ticket_transitions.row(i + 1, named=True)

                duration = (next_trans["timestamp"] - current["timestamp"]).total_seconds() / 86400
                time_in_status[current["to_status"]].append(duration)

        # Calculate averages
        avg_time = {}
        for status, durations in time_in_status.items():
            avg_time[status] = sum(durations) / len(durations) if durations else 0

        return avg_time

    def _find_flow_patterns(self, top_n: int = 10) -> List[Dict[str, Any]]:
        """
        Find most common flow patterns (sequences of status transitions) with ticket details.

        Args:
            top_n: Number of top patterns to return

        Returns:
            List of common flow patterns with counts and ticket details
        """
        patterns = []
        pattern_to_tickets = defaultdict(list)

        for ticket_key in self.transitions_df["ticket_key"].unique():
            ticket_transitions = (
                self.transitions_df
                .filter(pl.col("ticket_key") == ticket_key)
                .sort("timestamp")
            )

            # Create pattern string
            if len(ticket_transitions) >= 2:
                pattern_list = []
                for i in range(len(ticket_transitions)):
                    row = ticket_transitions.row(i, named=True)
                    if i == 0:
                        pattern_list.append(row["from_status"])
                    pattern_list.append(row["to_status"])

                pattern = " → ".join(pattern_list)
                patterns.append(pattern)

                # Find ticket details
                ticket_info = next((t for t in self.tickets if t["key"] == ticket_key), None)
                if ticket_info:
                    pattern_to_tickets[pattern].append({
                        "key": ticket_key,
                        "summary": ticket_info.get("summary", ""),
                        "status": ticket_info.get("status", ""),
                        "priority": ticket_info.get("priority", ""),
                        "assignee": ticket_info.get("assignee", ""),
                    })

        # Count patterns
        pattern_counts = Counter(patterns)

        return [
            {
                "pattern": pattern,
                "count": count,
                "tickets": pattern_to_tickets[pattern]
            }
            for pattern, count in pattern_counts.most_common(top_n)
        ]

    def calculate_temporal_trends(
        self,
        start_date: str,
        end_date: str,
        granularity: str = "daily"
    ) -> pl.DataFrame:
        """
        Calculate temporal trends over a date range.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            granularity: "daily" or "weekly"

        Returns:
            DataFrame with temporal metrics
        """
        from datetime import timezone

        # Create timezone-aware datetimes to match DataFrame columns
        start = datetime.fromisoformat(start_date).replace(tzinfo=timezone.utc)
        end = datetime.fromisoformat(end_date).replace(tzinfo=timezone.utc)

        # Generate date range
        if granularity == "daily":
            date_range = pl.datetime_range(
                start, end, interval="1d", eager=True, time_zone="UTC"
            )
        else:  # weekly
            date_range = pl.datetime_range(
                start, end, interval="1w", eager=True, time_zone="UTC"
            )

        trends = []
        for current_date in date_range:
            # Tickets created by this date
            created = self.df.filter(pl.col("created") <= current_date).height

            # Tickets resolved by this date
            resolved = self.df.filter(
                (pl.col("resolved").is_not_null()) &
                (pl.col("resolved") <= current_date)
            ).height

            # Tickets in progress at this date
            in_progress = created - resolved

            trends.append({
                "date": current_date,
                "tickets_created": created,
                "tickets_resolved": resolved,
                "tickets_in_progress": in_progress,
            })

        return pl.DataFrame(trends)

    def calculate_cycle_metrics(self) -> Dict[str, Any]:
        """
        Calculate cycle time, lead time, and throughput metrics.

        Returns:
            Dictionary with cycle metrics
        """
        metrics = {
            "lead_times": [],
            "cycle_times": [],
            "throughput": 0,
        }

        for ticket in self.tickets:
            created = datetime.fromisoformat(ticket["created"].replace("Z", "+00:00"))

            # Lead time: from creation to resolution
            if ticket["resolved"]:
                resolved = datetime.fromisoformat(ticket["resolved"].replace("Z", "+00:00"))
                lead_time = (resolved - created).total_seconds() / 86400
                metrics["lead_times"].append(lead_time)
                metrics["throughput"] += 1

            # Cycle time: from first "In Progress" to resolution
            if ticket["changelog"] and ticket["resolved"]:
                first_in_progress = None
                for change in ticket["changelog"]:
                    if change["to_status"] in ["In Progress", "In Development"]:
                        first_in_progress = datetime.fromisoformat(
                            change["timestamp"].replace("Z", "+00:00")
                        )
                        break

                if first_in_progress:
                    resolved = datetime.fromisoformat(ticket["resolved"].replace("Z", "+00:00"))
                    cycle_time = (resolved - first_in_progress).total_seconds() / 86400
                    metrics["cycle_times"].append(cycle_time)

        # Calculate statistics
        if metrics["lead_times"]:
            metrics["avg_lead_time"] = sum(metrics["lead_times"]) / len(metrics["lead_times"])
            metrics["median_lead_time"] = sorted(metrics["lead_times"])[len(metrics["lead_times"]) // 2]
        else:
            metrics["avg_lead_time"] = 0
            metrics["median_lead_time"] = 0

        if metrics["cycle_times"]:
            metrics["avg_cycle_time"] = sum(metrics["cycle_times"]) / len(metrics["cycle_times"])
            metrics["median_cycle_time"] = sorted(metrics["cycle_times"])[len(metrics["cycle_times"]) // 2]
        else:
            metrics["avg_cycle_time"] = 0
            metrics["median_cycle_time"] = 0

        return metrics

    def get_status_distribution(self) -> Dict[str, int]:
        """
        Get current status distribution of tickets.

        Returns:
            Dictionary mapping status to ticket count
        """
        status_counts = (
            self.df
            .group_by("status")
            .agg(pl.count().alias("count"))
            .sort("count", descending=True)
        )

        return {row["status"]: row["count"] for row in status_counts.iter_rows(named=True)}

    def get_summary_statistics(self) -> Dict[str, Any]:
        """
        Get overall summary statistics.

        Returns:
            Dictionary with summary metrics
        """
        return {
            "total_tickets": len(self.df),
            "resolved_tickets": self.df.filter(pl.col("resolved").is_not_null()).height,
            "in_progress_tickets": self.df.filter(pl.col("status").str.contains("(?i)progress")).height,
            "issue_type_distribution": self._get_distribution("issue_type"),
            "priority_distribution": self._get_distribution("priority"),
            "status_distribution": self.get_status_distribution(),
        }

    def _get_distribution(self, column: str) -> Dict[str, int]:
        """
        Get distribution of values for a column.

        Args:
            column: Column name to analyze

        Returns:
            Dictionary mapping values to counts
        """
        distribution = (
            self.df
            .group_by(column)
            .agg(pl.count().alias("count"))
            .sort("count", descending=True)
        )

        return {row[column]: row["count"] for row in distribution.iter_rows(named=True)}

    def calculate_daily_issue_metrics(
        self,
        start_date: str,
        end_date: str
    ) -> pl.DataFrame:
        """
        Calculate daily metrics for issues raised, closed, and open.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            DataFrame with daily issue metrics
        """
        from datetime import timezone

        # Create timezone-aware datetimes to match DataFrame columns
        start = datetime.fromisoformat(start_date).replace(tzinfo=timezone.utc)
        end = datetime.fromisoformat(end_date).replace(tzinfo=timezone.utc)

        # Generate date range with timezone
        date_range = pl.datetime_range(start, end, interval="1d", eager=True, time_zone="UTC")

        daily_metrics = []
        for current_date in date_range:
            # Get current date (timezone-aware)
            current_date_tz = current_date

            # Issues raised on this day
            raised = self.df.filter(
                pl.col("created").dt.date() == current_date_tz.date()
            ).height

            # Issues closed on this day
            closed = self.df.filter(
                (pl.col("resolved").is_not_null()) &
                (pl.col("resolved").dt.date() == current_date_tz.date())
            ).height

            # Total issues created up to this day
            total_created = self.df.filter(
                pl.col("created") <= current_date_tz
            ).height

            # Total issues resolved up to this day
            total_resolved = self.df.filter(
                (pl.col("resolved").is_not_null()) &
                (pl.col("resolved") <= current_date_tz)
            ).height

            # Open issues at end of this day
            open_issues = total_created - total_resolved

            daily_metrics.append({
                "date": current_date_tz,
                "issues_raised": raised,
                "issues_closed": closed,
                "open_issues": open_issues,
            })

        return pl.DataFrame(daily_metrics)

    def get_xray_test_executions(self, label_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Extract Xray test execution issues from tickets.

        Args:
            label_filter: Optional label to filter test executions

        Returns:
            List of test execution issues
        """
        test_executions = []

        for ticket in self.tickets:
            # Filter for Xray Test Execution issue type
            if ticket.get("issue_type") in ["Test Execution", "Test"]:
                if label_filter:
                    if label_filter in ticket.get("labels", []):
                        test_executions.append(ticket)
                else:
                    test_executions.append(ticket)

        return test_executions
