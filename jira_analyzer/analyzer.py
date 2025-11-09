"""
Bug Flow Analysis Module.

This module analyzes bug status transitions, detects rework loops, calculates
time metrics, and generates timeline data for reporting.

Classes:
    FlowAnalyzer: Main class for analyzing bug flows and detecting patterns
"""

from datetime import datetime
from typing import Optional

import polars as pl


class FlowAnalyzer:
    """
    Analyzer for bug status flows and workflow patterns.

    This class processes bug data to identify status transitions, detect rework
    loops, calculate time spent in each status, and generate timeline metrics
    for visualization.

    Attributes:
        STATUS_CATEGORIES: Mapping of statuses to workflow categories
        issues: All issues from Jira
        filtered_issues: Issues filtered by date range
        start_date: Optional start date for filtering
        end_date: Optional end date for filtering

    Example:
        >>> analyzer = FlowAnalyzer(issues, start_date='2024-01-01')
        >>> metrics = analyzer.calculate_flow_metrics()
        >>> print(f"Detected {metrics['loops']['total_loops']} rework loops")
    """

    # Status category mappings for workflow analysis
    STATUS_CATEGORIES = {
        'NEW': ['new', 'to do'],
        'IN PROGRESS': ['analysis', 'blocked', 'development', 'in development', 'review',
                        'development done', 'to test', 'in test'],
        'CLOSED': ['rejected', 'closed', 'resolved', 'ready for uat'],
    }

    def __init__(self, issues: list, start_date: Optional[str] = None, end_date: Optional[str] = None):
        """
        Initialize flow analyzer with issues.

        Args:
            issues: List of issue dictionaries from Jira
            start_date: Optional start date for filtering (YYYY-MM-DD)
            end_date: Optional end date for filtering (YYYY-MM-DD)
        """
        self.issues = issues
        self.start_date = start_date
        self.end_date = end_date

        # Filter issues by date if provided
        if start_date or end_date:
            self.filtered_issues = self._filter_issues_by_date()
        else:
            self.filtered_issues = issues

    def _filter_issues_by_date(self) -> list:
        """
        Filter issues by creation date.

        Filters the issue list based on start_date and end_date parameters.

        Returns:
            Filtered list of issues

        Note:
            Only the creation date is used for filtering, not resolution date.
        """
        filtered = []
        for issue in self.issues:
            created = issue.get('created', '')
            if not created:
                continue

            created_date = created.split('T')[0]  # Extract YYYY-MM-DD

            if self.start_date and created_date < self.start_date:
                continue
            if self.end_date and created_date > self.end_date:
                continue

            filtered.append(issue)

        return filtered

    def categorize_status(self, status: str) -> str:
        """
        Categorize a status into NEW, IN PROGRESS, or CLOSED.

        Maps individual Jira statuses to high-level workflow categories.

        Args:
            status: Status name from Jira

        Returns:
            Category name ('NEW', 'IN PROGRESS', 'CLOSED', 'OTHER', or 'UNKNOWN')

        Example:
            >>> analyzer = FlowAnalyzer([])
            >>> analyzer.categorize_status('In Development')
            'IN PROGRESS'
        """
        if not status:
            return 'UNKNOWN'

        status_lower = status.lower()
        for category, statuses in self.STATUS_CATEGORIES.items():
            if status_lower in statuses:
                return category

        return 'OTHER'

    def build_transitions_dataframe(self) -> pl.DataFrame:
        """
        Build a Polars DataFrame of all status transitions.

        Creates a detailed transition history for each issue, including:
        - Initial status (when created)
        - All status changes from changelog
        - Time duration in each status
        - Status categories

        Returns:
            DataFrame with columns: issue_key, from_status, to_status,
            from_category, to_category, transition_date, author, duration_hours

        Example:
            >>> df = analyzer.build_transitions_dataframe()
            >>> print(df.shape)
            (150, 8)  # 150 transitions across 8 columns
        """
        transitions = []

        for issue in self.filtered_issues:
            issue_key = issue['key']
            current_status = issue['status']
            changelog = issue.get('changelog', [])
            created = issue['created']

            # Build full transition history
            if not changelog:
                # Issue created and never changed status
                transitions.append({
                    'issue_key': issue_key,
                    'from_status': None,
                    'to_status': current_status,
                    'from_category': None,
                    'to_category': self.categorize_status(current_status),
                    'transition_date': created,
                    'author': issue['reporter'],
                    'duration_hours': None,
                })
            else:
                # Add initial creation
                first_change = changelog[0]
                first_status = first_change['from_string']

                transitions.append({
                    'issue_key': issue_key,
                    'from_status': None,
                    'to_status': first_status,
                    'from_category': None,
                    'to_category': self.categorize_status(first_status),
                    'transition_date': created,
                    'author': issue['reporter'],
                    'duration_hours': None,
                })

                # Process all status transitions
                for i, change in enumerate(changelog):
                    from_status = change['from_string']
                    to_status = change['to_string']
                    transition_date = change['created']

                    # Calculate duration in previous status
                    duration_hours = None
                    if i == 0:
                        # Duration from creation to first transition
                        duration_hours = self._calculate_duration(created, transition_date)
                    else:
                        # Duration from previous transition
                        prev_transition = changelog[i-1]['created']
                        duration_hours = self._calculate_duration(prev_transition, transition_date)

                    transitions.append({
                        'issue_key': issue_key,
                        'from_status': from_status,
                        'to_status': to_status,
                        'from_category': self.categorize_status(from_status),
                        'to_category': self.categorize_status(to_status),
                        'transition_date': transition_date,
                        'author': change['author'],
                        'duration_hours': duration_hours,
                    })

        if not transitions:
            return pl.DataFrame()

        df = pl.DataFrame(transitions)
        return df

    def _calculate_duration(self, start: str, end: str) -> float:
        """
        Calculate duration in hours between two datetime strings.

        Args:
            start: Start datetime in ISO format
            end: End datetime in ISO format

        Returns:
            Duration in hours, or None if calculation fails

        Note:
            Handles both 'Z' and '+00:00' timezone formats.
        """
        try:
            start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))
            delta = end_dt - start_dt
            return delta.total_seconds() / 3600  # Convert to hours
        except:
            return None

    def detect_loops(self) -> dict:
        """
        Detect status loops and rework in ticket flows.

        Identifies when bugs return to a previous status, indicating rework.
        For example: "In Test" → "Development" → "In Test" contains a loop.

        Returns:
            Dictionary with:
                - total_loops: Total number of loop instances
                - issues_with_loops: List of issue keys with loops
                - common_loops: Top 10 most common loop patterns

        Example:
            >>> loops = analyzer.detect_loops()
            >>> print(f"{loops['total_loops']} loops in {len(loops['issues_with_loops'])} bugs")
            6 loops in 2 bugs
        """
        loops_data = {
            'total_loops': 0,
            'issues_with_loops': [],
            'common_loops': [],
        }

        issues_with_loops = set()
        loop_patterns = {}

        for issue in self.filtered_issues:
            changelog = issue.get('changelog', [])
            if len(changelog) < 2:
                continue

            # Track status history
            status_history = []
            for change in changelog:
                to_status = change['to_string']
                status_history.append(to_status)

                # Check if this status appeared before (loop detected)
                if to_status in status_history[:-1]:
                    loops_data['total_loops'] += 1
                    issues_with_loops.add(issue['key'])

                    # Find what status it came from
                    from_status = change['from_string']
                    loop_key = f"{to_status} ← {from_status}"
                    loop_patterns[loop_key] = loop_patterns.get(loop_key, 0) + 1

        loops_data['issues_with_loops'] = sorted(list(issues_with_loops))
        loops_data['common_loops'] = [
            {'pattern': k, 'count': v}
            for k, v in sorted(loop_patterns.items(), key=lambda x: x[1], reverse=True)
        ][:10]  # Top 10

        return loops_data

    def calculate_time_in_status(self) -> dict:
        """
        Calculate average time spent in each status.

        Computes statistics for how long bugs remain in each status before
        transitioning to the next state.

        Returns:
            Dictionary mapping status names to time statistics:
                - avg_hours: Average time in hours
                - avg_days: Average time in days
                - median_hours: Median time in hours
                - min_hours: Minimum time in hours
                - max_hours: Maximum time in hours
                - count: Number of transitions from this status

        Example:
            >>> time_stats = analyzer.calculate_time_in_status()
            >>> for status, stats in time_stats.items():
            ...     print(f"{status}: {stats['avg_days']:.1f} days average")
        """
        df = self.build_transitions_dataframe()

        if df.is_empty() or 'duration_hours' not in df.columns:
            return {}

        # Group by from_status and calculate average duration
        time_stats = (
            df.filter(
                (pl.col('from_status').is_not_null()) &
                (pl.col('duration_hours').is_not_null())
            )
            .group_by('from_status')
            .agg([
                pl.col('duration_hours').mean().alias('avg_hours'),
                pl.col('duration_hours').median().alias('median_hours'),
                pl.col('duration_hours').min().alias('min_hours'),
                pl.col('duration_hours').max().alias('max_hours'),
                pl.len().alias('count')
            ])
            .sort('avg_hours', descending=True)
        )

        results = {}
        for row in time_stats.iter_rows(named=True):
            status = row['from_status']
            results[status] = {
                'avg_hours': round(row['avg_hours'], 2),
                'avg_days': round(row['avg_hours'] / 24, 2),
                'median_hours': round(row['median_hours'], 2) if row['median_hours'] else 0,
                'min_hours': round(row['min_hours'], 2) if row['min_hours'] else 0,
                'max_hours': round(row['max_hours'], 2) if row['max_hours'] else 0,
                'count': row['count'],
            }

        return results

    def _get_status_on_date(self, issue: dict, target_date: str) -> str:
        """
        Determine the status of an issue on a specific date.

        Args:
            issue: Issue dictionary with changelog
            target_date: Date in YYYY-MM-DD format

        Returns:
            Status name on the target date, or None if issue didn't exist yet
        """
        from datetime import datetime

        created_date = issue.get('created', '').split('T')[0]
        if not created_date or target_date < created_date:
            return None  # Issue didn't exist yet

        # Start with the first status (from first changelog entry or current status)
        changelog = issue.get('changelog', [])

        if not changelog:
            # No changelog means issue was created and never changed
            return issue.get('status', '')

        # Find the status on the target date by going through changelog
        current_status = changelog[0]['from_string']  # Initial status

        for change in changelog:
            change_date = change['created'].split('T')[0]
            if change_date <= target_date:
                current_status = change['to_string']
            else:
                break  # Changes after target date don't apply

        return current_status

    def calculate_timeline_metrics(self, future_days: int = 30) -> dict:
        """
        Calculate created/closed/open tickets over time with daily status checking.

        IMPORTANT: Uses ALL issues (not just filtered), then allows filtering at
        display level. Includes future dates for trend projection.

        For each day in the date range, determines which bugs were open (NEW or
        IN PROGRESS status) by examining their status history. Includes drilldown
        data showing which specific bugs were open on each day.

        Args:
            future_days: Number of days to project into the future for trend analysis (default: 30)

        Returns:
            Dictionary with 'daily_data' list containing:
                - date: Date in YYYY-MM-DD format
                - created: Number of bugs created on this date
                - closed: Number of bugs closed on this date
                - open: Number of bugs in NEW or IN PROGRESS status on this date
                - open_issues: List of dicts with bug details (key, summary, status)

        Example:
            >>> timeline = analyzer.calculate_timeline_metrics()
            >>> for day in timeline['daily_data'][:3]:
            ...     print(f"{day['date']}: {day['open']} bugs open")
            ...     for bug in day['open_issues'][:2]:
            ...         print(f"  - {bug['key']}: {bug['summary']}")

        Note:
            Timeline is calculated for ALL issues in the project, regardless of
            start_date/end_date filters. This allows proper trend analysis and
            future projections. Filtering should be applied at the display level.
        """
        from datetime import datetime, timedelta

        # Use ALL issues for timeline calculation, not filtered_issues
        all_issues = self.issues

        if not all_issues:
            return {'daily_data': []}

        # Determine date range from ALL issues (not filtered)
        all_dates = []
        for issue in all_issues:
            created_date = issue.get('created', '').split('T')[0]
            if created_date:
                all_dates.append(created_date)
            # Include all changelog dates
            for change in issue.get('changelog', []):
                change_date = change['created'].split('T')[0]
                all_dates.append(change_date)

        if not all_dates:
            return {'daily_data': []}

        min_date = min(all_dates)
        max_date = max(all_dates)

        # Extend range into the future for trend projection
        start = datetime.strptime(min_date, '%Y-%m-%d')
        end = datetime.strptime(max_date, '%Y-%m-%d')

        # Add future days for trend reference
        end = end + timedelta(days=future_days)

        # Generate all dates in range (including future)
        date_range = []
        current = start
        while current <= end:
            date_range.append(current.strftime('%Y-%m-%d'))
            current += timedelta(days=1)

        # Calculate stats for each day
        timeline_data = []
        for date in date_range:
            created_count = 0
            closed_count = 0
            open_count = 0
            open_issues = []

            # Use ALL issues for calculation
            for issue in all_issues:
                # Check if created on this date
                created_date = issue.get('created', '').split('T')[0]
                if created_date == date:
                    created_count += 1

                # Check if closed on this date
                resolved_date = issue.get('resolved', '')
                if resolved_date:
                    resolved_date = resolved_date.split('T')[0]
                    if resolved_date == date:
                        closed_count += 1

                # Check status on this date
                status_on_date = self._get_status_on_date(issue, date)
                if status_on_date:
                    category = self.categorize_status(status_on_date)
                    if category in ['NEW', 'IN PROGRESS']:
                        open_count += 1
                        open_issues.append({
                            'key': issue['key'],
                            'summary': issue['summary'],
                            'status': status_on_date,
                        })

            timeline_data.append({
                'date': date,
                'created': created_count,
                'closed': closed_count,
                'open': open_count,
                'open_issues': open_issues,
            })

        return {'daily_data': timeline_data}

    def calculate_flow_metrics(self) -> dict:
        """
        Calculate comprehensive flow metrics.

        Performs complete analysis of bug flows including transitions,
        loops, time metrics, and timeline data.

        Returns:
            Dictionary containing:
                - total_transitions: Total number of status changes
                - unique_statuses: Number of distinct statuses
                - flow_patterns: List of status transition patterns with counts
                - all_statuses: Sorted list of all status names
                - loops: Rework loop detection results
                - time_in_status: Time statistics per status
                - timeline: Daily created/closed/open metrics
                - total_issues: Number of issues analyzed

        Example:
            >>> metrics = analyzer.calculate_flow_metrics()
            >>> print(f"Analyzed {metrics['total_issues']} bugs")
            >>> print(f"Found {metrics['total_transitions']} transitions")
            >>> print(f"Detected {metrics['loops']['total_loops']} rework loops")
        """
        df = self.build_transitions_dataframe()

        if df.is_empty():
            return {
                'total_transitions': 0,
                'unique_statuses': 0,
                'flow_patterns': [],
                'all_statuses': [],
                'loops': {},
                'time_in_status': {},
                'timeline': {},
                'total_issues': len(self.filtered_issues),
            }

        # Count transitions between statuses
        flow_counts = (
            df.filter(pl.col('from_status').is_not_null())
            .group_by(['from_status', 'to_status'])
            .agg(pl.len().alias('count'))
            .sort('count', descending=True)
        )

        # Get unique statuses
        all_statuses = set()
        for status in df['from_status'].drop_nulls():
            all_statuses.add(status)
        for status in df['to_status']:
            all_statuses.add(status)

        # Convert to list of flow patterns
        flow_patterns = []
        for row in flow_counts.iter_rows(named=True):
            flow_patterns.append({
                'from': row['from_status'],
                'to': row['to_status'],
                'count': row['count'],
            })

        # Detect loops
        loops = self.detect_loops()

        # Calculate time in status
        time_in_status = self.calculate_time_in_status()

        # Calculate timeline metrics
        timeline = self.calculate_timeline_metrics()

        return {
            'total_transitions': len(df),
            'unique_statuses': len(all_statuses),
            'flow_patterns': flow_patterns,
            'all_statuses': sorted(all_statuses),
            'loops': loops,
            'time_in_status': time_in_status,
            'timeline': timeline,
            'total_issues': len(self.filtered_issues),
        }
