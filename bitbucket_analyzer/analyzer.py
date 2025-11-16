"""
Commit Analysis Module.

This module analyzes commit and pull request data to generate
productivity statistics and rankings.

Classes:
    CommitAnalyzer: Main class for analyzing commit statistics
"""

from typing import List, Dict, Optional
from collections import defaultdict


class CommitAnalyzer:
    """
    Analyzer for commit and pull request statistics.

    This class processes commit and PR data to calculate per-user statistics
    and generate rankings (top/bottom performers).

    Attributes:
        commits: List of commit dictionaries
        prs: List of pull request dictionaries
        user_aliases: Optional mapping of usernames to group/alias names

    Example:
        >>> analyzer = CommitAnalyzer(commits, prs, user_aliases={'john.doe': 'Team A'})
        >>> stats = analyzer.calculate_statistics()
        >>> rankings = analyzer.get_rankings()
    """

    def __init__(
        self,
        commits: List[Dict],
        commit_diffs: Dict[str, Dict],
        prs: List[Dict],
        user_aliases: Optional[Dict[str, str]] = None
    ):
        """
        Initialize the analyzer with commit and PR data.

        Args:
            commits: List of commit dictionaries from BitbucketFetcher
            commit_diffs: Dictionary mapping commit IDs to diff statistics
            prs: List of pull request dictionaries from BitbucketFetcher
            user_aliases: Optional mapping of username to group/alias name
        """
        self.commits = commits
        self.commit_diffs = commit_diffs
        self.prs = prs
        self.user_aliases = user_aliases or {}

    def calculate_statistics(self) -> Dict[str, Dict]:
        """
        Calculate per-user statistics.

        Returns:
            Dictionary mapping usernames to their statistics:
            {
                'username': {
                    'alias': 'Team A',  # If aliased
                    'commits': 42,
                    'lines_added': 1234,
                    'lines_deleted': 567,
                    'lines_modified': 89,
                    'total_changes': 1890,  # Sum of added + deleted + modified
                    'pull_requests': 15,
                    'files_changed': 123
                }
            }

        Note:
            - Lines modified are counted separately (not as added + deleted)
            - Total changes = added + deleted + modified
        """
        user_stats = defaultdict(lambda: {
            'alias': '',
            'commits': 0,
            'lines_added': 0,
            'lines_deleted': 0,
            'lines_modified': 0,
            'total_changes': 0,
            'pull_requests': 0,
            'files_changed': 0
        })

        # Process commits
        for commit in self.commits:
            author = commit.get('author', {}).get('name', 'Unknown')
            commit_id = commit.get('id', '')

            # Set alias if available
            if author in self.user_aliases:
                user_stats[author]['alias'] = self.user_aliases[author]

            # Increment commit count
            user_stats[author]['commits'] += 1

            # Add diff statistics if available
            if commit_id in self.commit_diffs:
                diff = self.commit_diffs[commit_id]
                user_stats[author]['lines_added'] += diff.get('added', 0)
                user_stats[author]['lines_deleted'] += diff.get('deleted', 0)
                user_stats[author]['lines_modified'] += diff.get('modified', 0)
                user_stats[author]['files_changed'] += diff.get('files_changed', 0)

        # Process pull requests
        for pr in self.prs:
            author = pr.get('author', {}).get('user', {}).get('name', 'Unknown')

            # Set alias if available
            if author in self.user_aliases:
                user_stats[author]['alias'] = self.user_aliases[author]

            # Increment PR count
            user_stats[author]['pull_requests'] += 1

        # Calculate total changes
        for author, stats in user_stats.items():
            stats['total_changes'] = (
                stats['lines_added'] +
                stats['lines_deleted'] +
                stats['lines_modified']
            )

        return dict(user_stats)

    def get_rankings(self, stats: Optional[Dict[str, Dict]] = None) -> Dict:
        """
        Get rankings (top 3 and bottom 3) for each metric.

        Args:
            stats: User statistics dictionary (if None, will calculate)

        Returns:
            Dictionary with rankings:
            {
                'by_commits': {
                    'top': [('user1', 42), ('user2', 38), ('user3', 35)],
                    'bottom': [('user6', 5), ('user5', 8), ('user4', 12)]
                },
                'by_changes': {
                    'top': [...],
                    'bottom': [...]
                },
                'by_pull_requests': {
                    'top': [...],
                    'bottom': [...]
                }
            }

        Note:
            - Each ranking contains tuples of (username, value)
            - If fewer than 3 users, returns all available users
        """
        if stats is None:
            stats = self.calculate_statistics()

        rankings = {}

        # Ranking by commits
        commits_ranking = sorted(
            [(user, data['commits']) for user, data in stats.items()],
            key=lambda x: x[1],
            reverse=True
        )
        rankings['by_commits'] = {
            'top': commits_ranking[:3],
            'bottom': list(reversed(commits_ranking[-3:])) if len(commits_ranking) > 3 else []
        }

        # Ranking by total changes
        changes_ranking = sorted(
            [(user, data['total_changes']) for user, data in stats.items()],
            key=lambda x: x[1],
            reverse=True
        )
        rankings['by_changes'] = {
            'top': changes_ranking[:3],
            'bottom': list(reversed(changes_ranking[-3:])) if len(changes_ranking) > 3 else []
        }

        # Ranking by pull requests
        pr_ranking = sorted(
            [(user, data['pull_requests']) for user, data in stats.items()],
            key=lambda x: x[1],
            reverse=True
        )
        rankings['by_pull_requests'] = {
            'top': pr_ranking[:3],
            'bottom': list(reversed(pr_ranking[-3:])) if len(pr_ranking) > 3 else []
        }

        return rankings

    def get_summary(self, stats: Optional[Dict[str, Dict]] = None) -> Dict:
        """
        Get summary statistics across all users.

        Args:
            stats: User statistics dictionary (if None, will calculate)

        Returns:
            Summary dictionary:
            {
                'total_users': 10,
                'total_commits': 420,
                'total_lines_added': 12345,
                'total_lines_deleted': 6789,
                'total_lines_modified': 890,
                'total_changes': 20024,
                'total_pull_requests': 150,
                'average_commits_per_user': 42.0,
                'average_changes_per_user': 2002.4
            }
        """
        if stats is None:
            stats = self.calculate_statistics()

        total_commits = sum(data['commits'] for data in stats.values())
        total_added = sum(data['lines_added'] for data in stats.values())
        total_deleted = sum(data['lines_deleted'] for data in stats.values())
        total_modified = sum(data['lines_modified'] for data in stats.values())
        total_changes = sum(data['total_changes'] for data in stats.values())
        total_prs = sum(data['pull_requests'] for data in stats.values())
        total_users = len(stats)

        return {
            'total_users': total_users,
            'total_commits': total_commits,
            'total_lines_added': total_added,
            'total_lines_deleted': total_deleted,
            'total_lines_modified': total_modified,
            'total_changes': total_changes,
            'total_pull_requests': total_prs,
            'average_commits_per_user': total_commits / total_users if total_users > 0 else 0,
            'average_changes_per_user': total_changes / total_users if total_users > 0 else 0,
            'average_prs_per_user': total_prs / total_users if total_users > 0 else 0
        }

    def get_detailed_commit_list(
        self,
        username: str,
        stats: Optional[Dict[str, Dict]] = None
    ) -> List[Dict]:
        """
        Get detailed list of commits for a specific user.

        Args:
            username: Username to get commits for
            stats: User statistics dictionary (if None, will calculate)

        Returns:
            List of commit dictionaries with diff information:
            [
                {
                    'id': 'abc123...',
                    'message': 'Fix bug in login',
                    'date': '2024-01-15',
                    'added': 45,
                    'deleted': 12,
                    'modified': 3,
                    'files_changed': 2
                },
                ...
            ]
        """
        user_commits = []

        for commit in self.commits:
            author = commit.get('author', {}).get('name', '')
            if author == username:
                commit_id = commit.get('id', '')
                commit_timestamp = commit.get('authorTimestamp', 0) / 1000
                commit_date = None

                if commit_timestamp:
                    from datetime import datetime
                    commit_date = datetime.fromtimestamp(commit_timestamp).strftime('%Y-%m-%d %H:%M:%S')

                commit_info = {
                    'id': commit_id,
                    'short_id': commit_id[:8] if commit_id else '',
                    'message': commit.get('message', '').split('\n')[0],  # First line only
                    'date': commit_date,
                    'added': 0,
                    'deleted': 0,
                    'modified': 0,
                    'files_changed': 0
                }

                # Add diff stats if available
                if commit_id in self.commit_diffs:
                    diff = self.commit_diffs[commit_id]
                    commit_info.update({
                        'added': diff.get('added', 0),
                        'deleted': diff.get('deleted', 0),
                        'modified': diff.get('modified', 0),
                        'files_changed': diff.get('files_changed', 0)
                    })

                user_commits.append(commit_info)

        return user_commits
