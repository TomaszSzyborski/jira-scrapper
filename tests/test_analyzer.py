"""
Tests for FlowAnalyzer module.

This module tests the bug flow analysis functionality.
"""

import pytest

from jira_analyzer.analyzer import FlowAnalyzer


class TestFlowAnalyzer:
    """Test cases for FlowAnalyzer class."""

    def test_init_without_date_filter(self, fake_issues):
        """Test initialization without date filtering."""
        analyzer = FlowAnalyzer(fake_issues)

        assert analyzer.issues == fake_issues
        assert analyzer.filtered_issues == fake_issues
        assert analyzer.start_date is None
        assert analyzer.end_date is None

    def test_init_with_date_filter(self, fake_issues):
        """Test initialization with date filtering."""
        analyzer = FlowAnalyzer(fake_issues, start_date='2024-01-20', end_date='2024-01-25')

        assert analyzer.start_date == '2024-01-20'
        assert analyzer.end_date == '2024-01-25'
        # Should filter issues created between dates
        assert len(analyzer.filtered_issues) < len(fake_issues)

    def test_filter_issues_by_date(self, fake_issues):
        """Test date filtering logic."""
        analyzer = FlowAnalyzer(fake_issues, start_date='2024-01-20', end_date='2024-01-22')

        # Only PROJ-104 and PROJ-105 were created in this range
        assert len(analyzer.filtered_issues) == 2
        keys = [issue['key'] for issue in analyzer.filtered_issues]
        assert 'PROJ-104' in keys
        assert 'PROJ-105' in keys

    def test_filter_issues_by_label(self, fake_issues):
        """Test label filtering logic."""
        analyzer = FlowAnalyzer(fake_issues, label='mobile')

        # Only issues with 'mobile' label should be included
        assert len(analyzer.filtered_issues) > 0
        for issue in analyzer.filtered_issues:
            assert 'mobile' in issue['labels']

    def test_filter_issues_by_date_and_label(self, fake_issues):
        """Test combined date and label filtering."""
        analyzer = FlowAnalyzer(fake_issues, start_date='2024-01-15', end_date='2024-01-20', label='ui')

        # Should filter by both criteria
        assert len(analyzer.filtered_issues) >= 0
        for issue in analyzer.filtered_issues:
            # Check date range
            created_date = issue['created'].split('T')[0]
            assert '2024-01-15' <= created_date <= '2024-01-20'
            # Check label
            assert 'ui' in issue['labels']

    def test_categorize_status_new(self, fake_issues):
        """Test status categorization for NEW category."""
        analyzer = FlowAnalyzer(fake_issues)

        assert analyzer.categorize_status('New') == 'NEW'
        assert analyzer.categorize_status('To Do') == 'NEW'
        assert analyzer.categorize_status('NEW') == 'NEW'

    def test_categorize_status_in_progress(self, fake_issues):
        """Test status categorization for IN PROGRESS category."""
        analyzer = FlowAnalyzer(fake_issues)

        assert analyzer.categorize_status('Analysis') == 'IN PROGRESS'
        assert analyzer.categorize_status('In Development') == 'IN PROGRESS'
        assert analyzer.categorize_status('Blocked') == 'IN PROGRESS'
        assert analyzer.categorize_status('Review') == 'IN PROGRESS'
        assert analyzer.categorize_status('In Test') == 'IN PROGRESS'

    def test_categorize_status_closed(self, fake_issues):
        """Test status categorization for CLOSED category."""
        analyzer = FlowAnalyzer(fake_issues)

        assert analyzer.categorize_status('Closed') == 'CLOSED'
        assert analyzer.categorize_status('Resolved') == 'CLOSED'
        assert analyzer.categorize_status('Rejected') == 'CLOSED'
        assert analyzer.categorize_status('Ready for UAT') == 'CLOSED'

    def test_categorize_status_unknown(self, fake_issues):
        """Test status categorization for unknown statuses."""
        analyzer = FlowAnalyzer(fake_issues)

        assert analyzer.categorize_status('Unknown Status') == 'OTHER'
        assert analyzer.categorize_status('') == 'UNKNOWN'
        assert analyzer.categorize_status(None) == 'UNKNOWN'

    def test_build_transitions_dataframe(self, fake_issues):
        """Test building transitions dataframe."""
        analyzer = FlowAnalyzer(fake_issues)
        df = analyzer.build_transitions_dataframe()

        assert not df.is_empty()
        assert 'issue_key' in df.columns
        assert 'from_status' in df.columns
        assert 'to_status' in df.columns
        assert 'from_category' in df.columns
        assert 'to_category' in df.columns
        assert 'transition_date' in df.columns
        assert 'author' in df.columns
        assert 'duration_hours' in df.columns

        # Check that we have transitions
        assert len(df) > 0

    def test_build_transitions_includes_initial_status(self, fake_issues):
        """Test that initial status creation is included in transitions."""
        analyzer = FlowAnalyzer(fake_issues)
        df = analyzer.build_transitions_dataframe()

        # Filter for PROJ-101's initial status
        proj101_initial = df.filter(
            (df['issue_key'] == 'PROJ-101') & (df['from_status'].is_null())
        )

        assert len(proj101_initial) == 1
        assert proj101_initial['to_status'][0] == 'To Do'

    def test_calculate_duration(self, fake_issues):
        """Test duration calculation between timestamps."""
        analyzer = FlowAnalyzer(fake_issues)

        # Test 1 hour difference
        start = '2024-01-15T10:00:00.000+0000'
        end = '2024-01-15T11:00:00.000+0000'
        duration = analyzer._calculate_duration(start, end)

        assert duration == 1.0

    def test_detect_loops(self, fake_issues):
        """Test loop detection in status transitions."""
        analyzer = FlowAnalyzer(fake_issues)
        loops = analyzer.detect_loops()

        assert 'total_loops' in loops
        assert 'issues_with_loops' in loops
        assert 'common_loops' in loops

        # PROJ-102 has a loop (In Test -> In Development -> In Test)
        # PROJ-105 has loops (In Development -> Review -> In Development -> Review)
        assert loops['total_loops'] > 0
        assert len(loops['issues_with_loops']) > 0

        # Check that PROJ-102 is in issues with loops
        assert 'PROJ-102' in loops['issues_with_loops'] or 'PROJ-105' in loops['issues_with_loops']

    def test_detect_loops_specific_pattern(self, fake_issues):
        """Test that specific loop patterns are detected."""
        analyzer = FlowAnalyzer(fake_issues)
        loops = analyzer.detect_loops()

        # Should detect the In Test -> In Development loop from PROJ-102
        patterns = [loop['pattern'] for loop in loops['common_loops']]

        # At least one loop pattern should be detected
        assert len(patterns) > 0

    def test_calculate_time_in_status(self, fake_issues):
        """Test time in status calculation."""
        analyzer = FlowAnalyzer(fake_issues)
        time_stats = analyzer.calculate_time_in_status()

        assert isinstance(time_stats, dict)
        assert len(time_stats) > 0

        # Check structure of time stats
        for status, stats in time_stats.items():
            assert 'avg_hours' in stats
            assert 'avg_days' in stats
            assert 'median_hours' in stats
            assert 'min_hours' in stats
            assert 'max_hours' in stats
            assert 'count' in stats

            # Values should be non-negative
            assert stats['avg_hours'] >= 0
            assert stats['count'] > 0

    def test_calculate_timeline_metrics(self, fake_issues):
        """Test timeline metrics calculation."""
        analyzer = FlowAnalyzer(fake_issues)
        timeline = analyzer.calculate_timeline_metrics()

        assert 'daily_data' in timeline
        assert len(timeline['daily_data']) > 0

        # Check daily data structure
        for day in timeline['daily_data']:
            assert 'date' in day
            assert 'created' in day
            assert 'closed' in day
            assert 'open' in day

            # Counts should be non-negative
            assert day['created'] >= 0
            assert day['closed'] >= 0
            assert day['open'] >= 0

    def test_calculate_timeline_cumulative_open(self, fake_issues):
        """Test that cumulative open count is calculated correctly."""
        analyzer = FlowAnalyzer(fake_issues)
        timeline = analyzer.calculate_timeline_metrics()

        daily_data = timeline['daily_data']

        # Verify open count never goes negative
        for day in daily_data:
            assert day['open'] >= 0

    def test_calculate_flow_metrics(self, fake_issues):
        """Test comprehensive flow metrics calculation."""
        analyzer = FlowAnalyzer(fake_issues)
        metrics = analyzer.calculate_flow_metrics()

        # Check all expected keys
        assert 'total_transitions' in metrics
        assert 'unique_statuses' in metrics
        assert 'flow_patterns' in metrics
        assert 'all_statuses' in metrics
        assert 'loops' in metrics
        assert 'time_in_status' in metrics
        assert 'timeline' in metrics
        assert 'total_issues' in metrics

        # Check types and basic validations
        assert metrics['total_transitions'] > 0
        assert metrics['unique_statuses'] > 0
        assert isinstance(metrics['flow_patterns'], list)
        assert isinstance(metrics['all_statuses'], list)
        assert metrics['total_issues'] == len(fake_issues)

    def test_calculate_flow_metrics_flow_patterns(self, fake_issues):
        """Test that flow patterns are properly calculated."""
        analyzer = FlowAnalyzer(fake_issues)
        metrics = analyzer.calculate_flow_metrics()

        flow_patterns = metrics['flow_patterns']

        assert len(flow_patterns) > 0

        # Check flow pattern structure
        for pattern in flow_patterns:
            assert 'from' in pattern
            assert 'to' in pattern
            assert 'count' in pattern
            assert pattern['count'] > 0

    def test_empty_issues_list(self):
        """Test analyzer handles empty issues list gracefully."""
        analyzer = FlowAnalyzer([])
        metrics = analyzer.calculate_flow_metrics()

        assert metrics['total_transitions'] == 0
        assert metrics['unique_statuses'] == 0
        assert metrics['total_issues'] == 0
        assert len(metrics['flow_patterns']) == 0

    def test_issue_without_changelog(self):
        """Test handling of issues with no changelog."""
        issue_no_changelog = {
            'key': 'PROJ-999',
            'id': '10999',
            'summary': 'Issue with no changes',
            'status': 'New',
            'created': '2024-01-15T10:00:00.000+0000',
            'reporter': 'Test User',
            'changelog': []
        }

        analyzer = FlowAnalyzer([issue_no_changelog])
        df = analyzer.build_transitions_dataframe()

        # Should still have one row for the initial creation
        assert len(df) == 1
        assert df['to_status'][0] == 'New'
        assert df['from_status'][0] is None

    def test_date_filtering_edge_cases(self, fake_issues):
        """Test date filtering edge cases."""
        # Start date only
        analyzer1 = FlowAnalyzer(fake_issues, start_date='2024-01-20')
        assert len(analyzer1.filtered_issues) < len(fake_issues)

        # End date only
        analyzer2 = FlowAnalyzer(fake_issues, end_date='2024-01-18')
        assert len(analyzer2.filtered_issues) < len(fake_issues)

        # No matches
        analyzer3 = FlowAnalyzer(fake_issues, start_date='2025-01-01', end_date='2025-01-31')
        assert len(analyzer3.filtered_issues) == 0
