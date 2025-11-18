"""
Bitbucket Repository Data Analyzer Module.

This module analyzes repository data fetched from Bitbucket, calculating
metrics such as commit frequency, contributor statistics, and PR analysis.

Classes:
    BitbucketAnalyzer: Main class for analyzing Bitbucket repository data
"""

from typing import List, Dict
from datetime import datetime, timedelta
from collections import defaultdict


class BitbucketAnalyzer:
    """
    Analyzer for Bitbucket repository data.

    Calculates various metrics from commits and pull requests including
    contributor statistics, commit frequency, and PR metrics.

    Attributes:
        commits (list): List of commit dictionaries
        pull_requests (list): List of pull request dictionaries
        start_date (str): Analysis start date
        end_date (str): Analysis end date

    Example:
        >>> analyzer = BitbucketAnalyzer(commits, pull_requests)
        >>> metrics = analyzer.calculate_metrics()
    """

    def __init__(
        self,
        commits: List[dict],
        pull_requests: List[dict] = None,
        start_date: str = None,
        end_date: str = None
    ):
        """
        Initialize the analyzer with repository data.

        Args:
            commits: List of commit dictionaries
            pull_requests: List of pull request dictionaries
            start_date: Analysis start date (YYYY-MM-DD)
            end_date: Analysis end date (YYYY-MM-DD)
        """
        self.commits = commits
        self.pull_requests = pull_requests or []
        self.start_date = start_date
        self.end_date = end_date

    def calculate_metrics(self) -> dict:
        """
        Calculate comprehensive repository metrics.

        Returns:
            Dictionary containing all calculated metrics including:
            - total_commits: Total number of commits
            - total_contributors: Number of unique contributors
            - commit_timeline: Daily commit counts
            - contributor_stats: Statistics per contributor
            - pr_metrics: Pull request metrics
            - activity_summary: Summary of repository activity
        """
        metrics = {
            'total_commits': len(self.commits),
            'total_pull_requests': len(self.pull_requests),
            'total_contributors': len(self._get_unique_contributors()),
            'commit_timeline': self._build_commit_timeline(),
            'contributor_stats': self._calculate_contributor_stats(),
            'pr_metrics': self._calculate_pr_metrics(),
            'activity_summary': self._calculate_activity_summary(),
            'date_range': {
                'start': self.start_date,
                'end': self.end_date
            }
        }

        return metrics

    def _get_unique_contributors(self) -> set:
        """
        Get unique contributors from commits.

        Returns:
            Set of unique contributor emails
        """
        contributors = set()
        for commit in self.commits:
            email = commit.get('author_email', '')
            if email:
                contributors.add(email.lower())

        return contributors

    def _build_commit_timeline(self) -> dict:
        """
        Build daily commit timeline.

        Returns:
            Dictionary with dates as keys and commit counts as values
        """
        timeline = defaultdict(int)

        for commit in self.commits:
            timestamp = commit.get('author_timestamp', 0)
            if timestamp:
                date = datetime.fromtimestamp(timestamp / 1000).strftime('%Y-%m-%d')
                timeline[date] += 1

        # Sort by date
        sorted_timeline = dict(sorted(timeline.items()))

        return sorted_timeline

    def _calculate_contributor_stats(self) -> List[dict]:
        """
        Calculate statistics for each contributor.

        Returns:
            List of contributor statistic dictionaries
        """
        contributor_data = defaultdict(lambda: {
            'commits': 0,
            'additions': 0,
            'deletions': 0,
            'name': '',
            'email': '',
            'first_commit': None,
            'last_commit': None
        })

        for commit in self.commits:
            email = commit.get('author_email', '').lower()
            name = commit.get('author_name', '')
            timestamp = commit.get('author_timestamp', 0)

            if email:
                contributor_data[email]['commits'] += 1
                contributor_data[email]['email'] = email
                if not contributor_data[email]['name']:
                    contributor_data[email]['name'] = name

                # Track first and last commit timestamps
                if not contributor_data[email]['first_commit']:
                    contributor_data[email]['first_commit'] = timestamp
                else:
                    contributor_data[email]['first_commit'] = min(
                        contributor_data[email]['first_commit'],
                        timestamp
                    )

                if not contributor_data[email]['last_commit']:
                    contributor_data[email]['last_commit'] = timestamp
                else:
                    contributor_data[email]['last_commit'] = max(
                        contributor_data[email]['last_commit'],
                        timestamp
                    )

        # Convert to list and sort by commit count
        contributor_stats = []
        for email, stats in contributor_data.items():
            # Convert timestamps to dates
            if stats['first_commit']:
                stats['first_commit_date'] = datetime.fromtimestamp(
                    stats['first_commit'] / 1000
                ).strftime('%Y-%m-%d')
            if stats['last_commit']:
                stats['last_commit_date'] = datetime.fromtimestamp(
                    stats['last_commit'] / 1000
                ).strftime('%Y-%m-%d')

            contributor_stats.append(stats)

        # Sort by commits (descending)
        contributor_stats.sort(key=lambda x: x['commits'], reverse=True)

        return contributor_stats

    def _calculate_pr_metrics(self) -> dict:
        """
        Calculate pull request metrics.

        Returns:
            Dictionary containing PR metrics
        """
        if not self.pull_requests:
            return {
                'total': 0,
                'merged': 0,
                'declined': 0,
                'open': 0,
                'avg_time_to_merge': None,
                'pr_timeline': {},
                'pr_by_author': []
            }

        merged_count = 0
        declined_count = 0
        open_count = 0
        merge_times = []
        pr_timeline = defaultdict(int)
        pr_by_author = defaultdict(int)

        for pr in self.pull_requests:
            state = pr.get('state', '').upper()
            created_ts = pr.get('created_timestamp', 0)
            closed_ts = pr.get('closed_timestamp')
            author_email = pr.get('author_email', '').lower()

            # Count by state
            if state == 'MERGED':
                merged_count += 1
                # Calculate time to merge
                if created_ts and closed_ts:
                    merge_time_hours = (closed_ts - created_ts) / (1000 * 3600)
                    merge_times.append(merge_time_hours)
            elif state == 'DECLINED':
                declined_count += 1
            elif state == 'OPEN':
                open_count += 1

            # Timeline
            if created_ts:
                date = datetime.fromtimestamp(created_ts / 1000).strftime('%Y-%m-%d')
                pr_timeline[date] += 1

            # By author
            if author_email:
                pr_by_author[author_email] += 1

        # Calculate average time to merge
        avg_merge_time = None
        if merge_times:
            avg_merge_time = sum(merge_times) / len(merge_times)

        # Convert pr_by_author to sorted list
        pr_by_author_list = [
            {'email': email, 'count': count}
            for email, count in pr_by_author.items()
        ]
        pr_by_author_list.sort(key=lambda x: x['count'], reverse=True)

        return {
            'total': len(self.pull_requests),
            'merged': merged_count,
            'declined': declined_count,
            'open': open_count,
            'avg_time_to_merge_hours': avg_merge_time,
            'pr_timeline': dict(sorted(pr_timeline.items())),
            'pr_by_author': pr_by_author_list[:10]  # Top 10 authors
        }

    def _calculate_activity_summary(self) -> dict:
        """
        Calculate overall activity summary.

        Returns:
            Dictionary with activity summary metrics
        """
        if not self.commits:
            return {
                'busiest_day': None,
                'total_days_with_commits': 0,
                'avg_commits_per_day': 0,
                'busiest_contributor': None
            }

        # Get commit timeline
        timeline = self._build_commit_timeline()

        # Find busiest day
        busiest_day = max(timeline.items(), key=lambda x: x[1]) if timeline else (None, 0)

        # Calculate average commits per day
        total_days = len(timeline)
        avg_commits_per_day = len(self.commits) / total_days if total_days > 0 else 0

        # Find busiest contributor
        contributor_stats = self._calculate_contributor_stats()
        busiest_contributor = contributor_stats[0] if contributor_stats else None

        return {
            'busiest_day': busiest_day[0] if busiest_day[0] else None,
            'busiest_day_commits': busiest_day[1] if busiest_day[0] else 0,
            'total_days_with_commits': total_days,
            'avg_commits_per_day': round(avg_commits_per_day, 2),
            'busiest_contributor': {
                'name': busiest_contributor['name'],
                'email': busiest_contributor['email'],
                'commits': busiest_contributor['commits']
            } if busiest_contributor else None
        }

    def get_commit_frequency(self, period: str = 'daily') -> dict:
        """
        Get commit frequency for a specific period.

        Args:
            period: Aggregation period ('daily', 'weekly', 'monthly')

        Returns:
            Dictionary with period as keys and commit counts as values
        """
        frequency = defaultdict(int)

        for commit in self.commits:
            timestamp = commit.get('author_timestamp', 0)
            if timestamp:
                date = datetime.fromtimestamp(timestamp / 1000)

                if period == 'daily':
                    key = date.strftime('%Y-%m-%d')
                elif period == 'weekly':
                    # ISO week number
                    key = date.strftime('%Y-W%W')
                elif period == 'monthly':
                    key = date.strftime('%Y-%m')
                else:
                    key = date.strftime('%Y-%m-%d')

                frequency[key] += 1

        return dict(sorted(frequency.items()))

    def get_top_contributors(self, limit: int = 10) -> List[dict]:
        """
        Get top contributors by commit count.

        Args:
            limit: Maximum number of contributors to return

        Returns:
            List of top contributor dictionaries
        """
        contributor_stats = self._calculate_contributor_stats()
        return contributor_stats[:limit]
