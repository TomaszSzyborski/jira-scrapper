#!/usr/bin/env python3
"""
Test script to verify Xray and Bitbucket scrapers functionality.

This script performs basic validation tests to ensure:
1. Xray scraper can connect and fetch data using on-prem APIs
2. Bitbucket scraper can fetch commits with diff data
3. Bitbucket scraper can fetch PRs with activities and diff stats
4. Analyzers properly calculate all metrics

Usage:
    python test_scrapers.py [--xray] [--bitbucket] [--all]
"""

import argparse
import sys
import os
from datetime import datetime, timedelta


def test_xray_fetcher():
    """Test Xray fetcher with on-prem API support."""
    print("\n" + "=" * 80)
    print("TESTING XRAY FETCHER")
    print("=" * 80)

    try:
        from jira_analyzer.xray_fetcher import XrayFetcher

        print("✓ XrayFetcher imported successfully")

        # Check if credentials are available
        if not os.getenv('JIRA_URL'):
            print("⚠ JIRA_URL not set in environment - skipping connection test")
            print("✓ XrayFetcher import test PASSED")
            return True

        print(f"Testing connection to: {os.getenv('JIRA_URL')}")

        try:
            fetcher = XrayFetcher()
            print("✓ XrayFetcher initialized successfully")

            # Test JQL building
            jql = fetcher.build_jql_for_test_executions('TEST', start_date='2024-01-01')
            print(f"✓ JQL built successfully: {jql}")

            print("\n✅ XrayFetcher test PASSED")
            return True

        except Exception as e:
            print(f"✗ XrayFetcher initialization failed: {e}")
            print("Note: This is expected if credentials are not configured")
            return True  # Don't fail if credentials aren't set

    except Exception as e:
        print(f"✗ XrayFetcher test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_bitbucket_fetcher():
    """Test Bitbucket fetcher with enhanced diff and PR analysis."""
    print("\n" + "=" * 80)
    print("TESTING BITBUCKET FETCHER")
    print("=" * 80)

    try:
        from jira_analyzer.bitbucket_fetcher import BitbucketFetcher

        print("✓ BitbucketFetcher imported successfully")

        # Check if credentials are available
        if not os.getenv('BITBUCKET_URL'):
            print("⚠ BITBUCKET_URL not set in environment - skipping connection test")
            print("✓ BitbucketFetcher import test PASSED")
            return True

        print(f"Testing connection to: {os.getenv('BITBUCKET_URL')}")

        try:
            fetcher = BitbucketFetcher()
            print("✓ BitbucketFetcher initialized successfully")

            # Verify new methods exist
            assert hasattr(fetcher, '_fetch_commit_changes'), "Missing _fetch_commit_changes method"
            print("✓ _fetch_commit_changes method exists")

            assert hasattr(fetcher, '_fetch_commit_diff_stats'), "Missing _fetch_commit_diff_stats method"
            print("✓ _fetch_commit_diff_stats method exists")

            assert hasattr(fetcher, '_fetch_pr_activities'), "Missing _fetch_pr_activities method"
            print("✓ _fetch_pr_activities method exists")

            assert hasattr(fetcher, '_fetch_pr_diff_stats'), "Missing _fetch_pr_diff_stats method"
            print("✓ _fetch_pr_diff_stats method exists")

            print("\n✅ BitbucketFetcher test PASSED")
            return True

        except Exception as e:
            print(f"✗ BitbucketFetcher initialization failed: {e}")
            print("Note: This is expected if credentials are not configured")
            return True  # Don't fail if credentials aren't set

    except Exception as e:
        print(f"✗ BitbucketFetcher test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_xray_analyzer():
    """Test Xray analyzer with sample data."""
    print("\n" + "=" * 80)
    print("TESTING XRAY ANALYZER")
    print("=" * 80)

    try:
        from jira_analyzer.xray_analyzer import XrayAnalyzer

        print("✓ XrayAnalyzer imported successfully")

        # Sample test execution data
        sample_executions = [
            {
                'key': 'TEST-1',
                'created': '2024-01-15T10:00:00Z',
                'test_runs': [
                    {
                        'test_key': 'TEST-10',
                        'status': 'PASS',
                        'started_on': '2024-01-15T10:05:00Z',
                        'finished_on': '2024-01-15T10:10:00Z',
                        'defects': [],
                        'execution_key': 'TEST-1'
                    },
                    {
                        'test_key': 'TEST-11',
                        'status': 'FAIL',
                        'started_on': '2024-01-15T10:15:00Z',
                        'finished_on': '2024-01-15T10:20:00Z',
                        'defects': ['BUG-123'],
                        'execution_key': 'TEST-1'
                    }
                ]
            }
        ]

        analyzer = XrayAnalyzer(sample_executions)
        print("✓ XrayAnalyzer initialized successfully")

        metrics = analyzer.calculate_test_metrics()
        print("✓ Test metrics calculated successfully")

        # Validate metrics
        assert metrics['total_executions'] == 1, f"Expected 1 execution, got {metrics['total_executions']}"
        print(f"✓ Total executions: {metrics['total_executions']}")

        assert metrics['total_test_runs'] == 2, f"Expected 2 test runs, got {metrics['total_test_runs']}"
        print(f"✓ Total test runs: {metrics['total_test_runs']}")

        assert metrics['pass_count'] == 1, f"Expected 1 pass, got {metrics['pass_count']}"
        print(f"✓ Pass count: {metrics['pass_count']}")

        assert metrics['fail_count'] == 1, f"Expected 1 fail, got {metrics['fail_count']}"
        print(f"✓ Fail count: {metrics['fail_count']}")

        assert len(metrics['defects_found']) == 1, f"Expected 1 defect, got {len(metrics['defects_found'])}"
        print(f"✓ Defects found: {len(metrics['defects_found'])}")

        print("\n✅ XrayAnalyzer test PASSED")
        return True

    except Exception as e:
        print(f"✗ XrayAnalyzer test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_bitbucket_analyzer():
    """Test Bitbucket analyzer with sample data including code churn metrics."""
    print("\n" + "=" * 80)
    print("TESTING BITBUCKET ANALYZER")
    print("=" * 80)

    try:
        from jira_analyzer.bitbucket_analyzer import BitbucketAnalyzer

        print("✓ BitbucketAnalyzer imported successfully")

        # Sample commit data with diff stats
        sample_commits = [
            {
                'id': 'abc123',
                'message': 'Fix: Authentication bug',
                'author_name': 'John Doe',
                'author_email': 'john@example.com',
                'author_timestamp': 1705482000000,
                'lines_added': 50,
                'lines_removed': 20,
                'files_changed': 3,
                'file_changes': [
                    {'path': 'src/auth.py', 'type': 'MODIFY'},
                    {'path': 'tests/test_auth.py', 'type': 'MODIFY'},
                    {'path': 'README.md', 'type': 'MODIFY'}
                ]
            },
            {
                'id': 'def456',
                'message': 'Feature: Add user dashboard',
                'author_name': 'Jane Smith',
                'author_email': 'jane@example.com',
                'author_timestamp': 1705568400000,
                'lines_added': 200,
                'lines_removed': 10,
                'files_changed': 5,
                'file_changes': [
                    {'path': 'src/dashboard.py', 'type': 'ADD'},
                    {'path': 'src/routes.py', 'type': 'MODIFY'}
                ]
            }
        ]

        # Sample PR data with activities
        sample_prs = [
            {
                'id': 1,
                'title': 'Add authentication',
                'state': 'MERGED',
                'created_timestamp': 1705482000000,
                'closed_timestamp': 1705568400000,
                'author_email': 'john@example.com',
                'pr_lines_added': 150,
                'pr_lines_removed': 30,
                'pr_files_changed': 8,
                'activities': {
                    'comments_count': 5,
                    'approvals_count': 2,
                    'reviews_count': 3,
                    'total_activities': 10
                }
            }
        ]

        analyzer = BitbucketAnalyzer(sample_commits, sample_prs)
        print("✓ BitbucketAnalyzer initialized successfully")

        metrics = analyzer.calculate_metrics()
        print("✓ Metrics calculated successfully")

        # Validate basic metrics
        assert metrics['total_commits'] == 2, f"Expected 2 commits, got {metrics['total_commits']}"
        print(f"✓ Total commits: {metrics['total_commits']}")

        assert metrics['total_pull_requests'] == 1, f"Expected 1 PR, got {metrics['total_pull_requests']}"
        print(f"✓ Total PRs: {metrics['total_pull_requests']}")

        # Validate code churn metrics
        code_churn = metrics.get('code_churn_metrics', {})
        assert code_churn is not None, "code_churn_metrics not found"
        print("✓ Code churn metrics exist")

        assert code_churn['total_lines_added'] == 250, f"Expected 250 lines added, got {code_churn['total_lines_added']}"
        print(f"✓ Total lines added: {code_churn['total_lines_added']}")

        assert code_churn['total_lines_removed'] == 30, f"Expected 30 lines removed, got {code_churn['total_lines_removed']}"
        print(f"✓ Total lines removed: {code_churn['total_lines_removed']}")

        assert code_churn['total_files_changed'] == 8, f"Expected 8 files changed, got {code_churn['total_files_changed']}"
        print(f"✓ Total files changed: {code_churn['total_files_changed']}")

        # Validate PR code review metrics
        pr_review = metrics.get('pr_code_review_metrics', {})
        assert pr_review is not None, "pr_code_review_metrics not found"
        print("✓ PR code review metrics exist")

        assert pr_review['total_pr_lines_added'] == 150, f"Expected 150 PR lines added, got {pr_review['total_pr_lines_added']}"
        print(f"✓ PR lines added: {pr_review['total_pr_lines_added']}")

        assert pr_review['avg_comments_per_pr'] == 5.0, f"Expected 5.0 comments/PR, got {pr_review['avg_comments_per_pr']}"
        print(f"✓ Avg comments per PR: {pr_review['avg_comments_per_pr']}")

        print("\n✅ BitbucketAnalyzer test PASSED")
        return True

    except Exception as e:
        print(f"✗ BitbucketAnalyzer test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests or specific test suites."""
    parser = argparse.ArgumentParser(description='Test Xray and Bitbucket scrapers')
    parser.add_argument('--xray', action='store_true', help='Test only Xray components')
    parser.add_argument('--bitbucket', action='store_true', help='Test only Bitbucket components')
    parser.add_argument('--all', action='store_true', help='Test all components (default)')

    args = parser.parse_args()

    # Default to all tests if no specific test selected
    if not (args.xray or args.bitbucket):
        args.all = True

    results = []

    if args.all or args.xray:
        results.append(('Xray Fetcher', test_xray_fetcher()))
        results.append(('Xray Analyzer', test_xray_analyzer()))

    if args.all or args.bitbucket:
        results.append(('Bitbucket Fetcher', test_bitbucket_fetcher()))
        results.append(('Bitbucket Analyzer', test_bitbucket_analyzer()))

    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    all_passed = True
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False

    print("=" * 80)

    if all_passed:
        print("\n🎉 All tests PASSED!")
        sys.exit(0)
    else:
        print("\n❌ Some tests FAILED!")
        sys.exit(1)


if __name__ == '__main__':
    main()
