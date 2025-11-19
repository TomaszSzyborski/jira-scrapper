"""
Bitbucket Repository Analyzer.

This package provides comprehensive tools for fetching and analyzing repository data
from Bitbucket Server/Data Center (On-Premise), including:

- Commit analysis with diff statistics (lines added/removed)
- Pull request analysis with review metrics
- Code churn tracking
- Contributor productivity metrics
- Review engagement analysis

Classes:
    BitbucketFetcher: Fetch commits, PRs, and diff data from Bitbucket API
    BitbucketAnalyzer: Analyze repository data and calculate metrics
    BitbucketReportGenerator: Generate HTML reports with visualizations

Example:
    >>> from bitbucket_analyzer import BitbucketFetcher, BitbucketAnalyzer
    >>>
    >>> # Fetch data
    >>> fetcher = BitbucketFetcher()
    >>> commits = fetcher.fetch_commits('PROJ', 'myrepo')
    >>> prs = fetcher.fetch_pull_requests('PROJ', 'myrepo')
    >>>
    >>> # Analyze
    >>> analyzer = BitbucketAnalyzer(commits, prs)
    >>> metrics = analyzer.calculate_metrics()
    >>>
    >>> # View metrics
    >>> print(f"Total lines added: {metrics['code_churn_metrics']['total_lines_added']:,}")
    >>> print(f"Review engagement: {metrics['pr_code_review_metrics']['review_engagement_rate']:.1f}%")
"""

from .fetcher import BitbucketFetcher
from .analyzer import BitbucketAnalyzer
from .reporter import BitbucketReportGenerator

__version__ = '2.0.0'
__all__ = [
    'BitbucketFetcher',
    'BitbucketAnalyzer',
    'BitbucketReportGenerator'
]
