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
        # Calculate enhanced commit and PR metrics
        commit_activity = self.calculate_commit_activity_metrics()
        pr_detailed = self.calculate_detailed_pr_metrics()

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
            },
            'commit_activity': commit_activity,
            'pr_detailed_metrics': pr_detailed,
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

    def calculate_commit_activity_metrics(self) -> dict:
        """
        Calculate detailed commit activity metrics.

        Calculates:
        - Commits per day/week
        - Distribution of commits among team members
        - Average commit size (lines changed) - Note: requires diff data
        - Commit message analysis

        Returns:
            Dictionary containing commit activity metrics
        """
        # Commits per day and week
        commits_per_day = self.get_commit_frequency('daily')
        commits_per_week = self.get_commit_frequency('weekly')

        # Distribution among team members
        contributor_distribution = {}
        total_commits = len(self.commits)

        for commit in self.commits:
            email = commit.get('author_email', 'Unknown').lower()
            contributor_distribution[email] = contributor_distribution.get(email, 0) + 1

        # Calculate percentages
        contributor_percentages = {}
        for email, count in contributor_distribution.items():
            percentage = (count / total_commits * 100) if total_commits > 0 else 0
            contributor_percentages[email] = {
                'commits': count,
                'percentage': round(percentage, 2)
            }

        # Sort by commit count
        sorted_contributors = sorted(
            contributor_percentages.items(),
            key=lambda x: x[1]['commits'],
            reverse=True
        )

        # Analyze commit messages for keywords
        commit_types = defaultdict(int)
        for commit in self.commits:
            message = commit.get('message', '').lower()

            # Simple categorization based on common prefixes
            if message.startswith('fix') or 'fix:' in message:
                commit_types['fix'] += 1
            elif message.startswith('feat') or 'feature:' in message:
                commit_types['feature'] += 1
            elif message.startswith('refactor') or 'refactor:' in message:
                commit_types['refactor'] += 1
            elif message.startswith('docs') or 'docs:' in message:
                commit_types['docs'] += 1
            elif message.startswith('test') or 'test:' in message:
                commit_types['test'] += 1
            elif message.startswith('chore') or 'chore:' in message:
                commit_types['chore'] += 1
            else:
                commit_types['other'] += 1

        return {
            'commits_per_day': commits_per_day,
            'commits_per_week': commits_per_week,
            'contributor_distribution': dict(sorted_contributors),
            'commit_types': dict(commit_types),
            'avg_commits_per_contributor': round(total_commits / len(contributor_distribution), 2) if contributor_distribution else 0,
        }

    def calculate_detailed_pr_metrics(self) -> dict:
        """
        Calculate detailed pull request metrics.

        Calculates:
        - Average review time
        - Comments per PR (if available)
        - Accept/reject ratio
        - Bottleneck analysis (reviewers with longest review times)

        Returns:
            Dictionary containing detailed PR metrics
        """
        if not self.pull_requests:
            return {
                'avg_review_time_hours': 0,
                'avg_comments_per_pr': 0,
                'accept_reject_ratio': 0,
                'reviewer_bottlenecks': [],
                'pr_size_distribution': {},
            }

        review_times = []
        total_comments = 0
        accepted_count = 0
        rejected_count = 0
        reviewer_times = defaultdict(list)

        for pr in self.pull_requests:
            created_ts = pr.get('created_timestamp', 0)
            closed_ts = pr.get('closed_timestamp')
            state = pr.get('state', '').upper()

            # Calculate review time
            if created_ts and closed_ts:
                review_time_hours = (closed_ts - created_ts) / (1000 * 3600)
                review_times.append(review_time_hours)

                # Track review times by reviewer
                reviewers = pr.get('reviewers', [])
                for reviewer in reviewers:
                    reviewer_email = reviewer.get('email', 'Unknown')
                    reviewer_times[reviewer_email].append(review_time_hours)

            # Count accepted/rejected
            if state == 'MERGED':
                accepted_count += 1
            elif state == 'DECLINED':
                rejected_count += 1

            # Comments per PR (placeholder - would need additional API call)
            # For now, count reviewers as proxy for engagement
            total_comments += len(pr.get('reviewers', []))

        # Calculate averages
        avg_review_time = sum(review_times) / len(review_times) if review_times else 0
        avg_comments = total_comments / len(self.pull_requests) if self.pull_requests else 0

        # Accept/reject ratio
        accept_reject_ratio = (accepted_count / rejected_count) if rejected_count > 0 else accepted_count

        # Find bottlenecks (reviewers with longest average review times)
        reviewer_avg_times = []
        for reviewer, times in reviewer_times.items():
            avg_time = sum(times) / len(times)
            reviewer_avg_times.append({
                'reviewer': reviewer,
                'avg_review_time_hours': round(avg_time, 2),
                'total_reviews': len(times)
            })

        # Sort by longest review time
        reviewer_bottlenecks = sorted(
            reviewer_avg_times,
            key=lambda x: x['avg_review_time_hours'],
            reverse=True
        )[:5]  # Top 5 slowest reviewers

        return {
            'avg_review_time_hours': round(avg_review_time, 2),
            'median_review_time_hours': round(sorted(review_times)[len(review_times)//2], 2) if review_times else 0,
            'avg_comments_per_pr': round(avg_comments, 2),
            'accepted_count': accepted_count,
            'rejected_count': rejected_count,
            'accept_reject_ratio': round(accept_reject_ratio, 2),
            'reviewer_bottlenecks': reviewer_bottlenecks,
            'total_review_hours': round(sum(review_times), 2),
        }
