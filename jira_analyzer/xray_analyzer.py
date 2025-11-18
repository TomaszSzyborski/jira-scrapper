"""
Xray Test Execution Analyzer Module.

This module analyzes test execution data from Xray for Jira and calculates
various test metrics and trends.

Classes:
    XrayAnalyzer: Main class for analyzing test execution data
"""

from collections import defaultdict
from datetime import datetime
from typing import Optional


class XrayAnalyzer:
    """
    Test execution analyzer for Xray data.

    This class processes test execution data and calculates metrics such as:
    - Pass/fail rates
    - Test execution trends over time
    - Test duration statistics
    - Defect density
    - Test coverage

    Attributes:
        executions (list): List of test execution dictionaries

    Example:
        >>> analyzer = XrayAnalyzer(executions)
        >>> metrics = analyzer.calculate_test_metrics()
        >>> print(f"Pass rate: {metrics['pass_rate']}%")
    """

    def __init__(self, executions: list, start_date: str = None, end_date: str = None):
        """
        Initialize analyzer with test execution data.

        Args:
            executions: List of test execution dictionaries from XrayFetcher
            start_date: Optional start date for filtering (YYYY-MM-DD)
            end_date: Optional end date for filtering (YYYY-MM-DD)
        """
        self.executions = executions
        self.start_date = start_date
        self.end_date = end_date

    def calculate_test_metrics(self) -> dict:
        """
        Calculate comprehensive test execution metrics.

        Returns:
            Dictionary containing all calculated metrics:
            - total_executions: Total number of test executions
            - total_test_runs: Total number of test runs across all executions
            - pass_count: Number of passed tests
            - fail_count: Number of failed tests
            - other_count: Number of tests with other statuses
            - pass_rate: Percentage of passed tests
            - fail_rate: Percentage of failed tests
            - timeline: Daily pass/fail trends
            - status_distribution: Count of each status
            - defects_found: List of defects found during testing
            - test_duration_stats: Statistics about test execution duration

        Example:
            >>> metrics = analyzer.calculate_test_metrics()
            >>> print(f"Pass rate: {metrics['pass_rate']:.1f}%")
        """
        if not self.executions:
            return {
                'total_executions': 0,
                'total_test_runs': 0,
                'pass_count': 0,
                'fail_count': 0,
                'other_count': 0,
                'pass_rate': 0.0,
                'fail_rate': 0.0,
                'timeline': {},
                'status_distribution': {},
                'defects_found': [],
                'test_duration_stats': {}
            }

        # Collect all test runs from all executions
        all_test_runs = []
        for execution in self.executions:
            for run in execution.get('test_runs', []):
                all_test_runs.append({
                    **run,
                    'execution_key': execution['key'],
                    'execution_created': execution['created']
                })

        # Calculate status counts
        status_counts = defaultdict(int)
        pass_count = 0
        fail_count = 0
        other_count = 0

        for run in all_test_runs:
            status = run.get('status', 'Unknown').upper()
            status_counts[status] += 1

            if status in ['PASS', 'PASSED', 'SUCCESS']:
                pass_count += 1
            elif status in ['FAIL', 'FAILED', 'FAILURE']:
                fail_count += 1
            else:
                other_count += 1

        total_runs = len(all_test_runs)
        pass_rate = (pass_count / total_runs * 100) if total_runs > 0 else 0.0
        fail_rate = (fail_count / total_runs * 100) if total_runs > 0 else 0.0

        # Build timeline data
        timeline = self._build_timeline(all_test_runs)

        # Collect defects
        defects_found = self._collect_defects(all_test_runs)

        # Calculate duration statistics
        duration_stats = self._calculate_duration_stats(all_test_runs)

        return {
            'total_executions': len(self.executions),
            'total_test_runs': total_runs,
            'pass_count': pass_count,
            'fail_count': fail_count,
            'other_count': other_count,
            'pass_rate': pass_rate,
            'fail_rate': fail_rate,
            'timeline': timeline,
            'status_distribution': dict(status_counts),
            'defects_found': defects_found,
            'test_duration_stats': duration_stats
        }

    def _build_timeline(self, test_runs: list) -> dict:
        """
        Build timeline of pass/fail trends by date.

        Args:
            test_runs: List of test run dictionaries

        Returns:
            Dictionary with daily data:
            {
                'daily_data': [
                    {
                        'date': '2024-01-01',
                        'passed': 10,
                        'failed': 2,
                        'other': 1,
                        'total': 13
                    },
                    ...
                ]
            }
        """
        daily_data = defaultdict(lambda: {'passed': 0, 'failed': 0, 'other': 0})

        for run in test_runs:
            # Get date from execution created field
            created = run.get('execution_created', '')
            if not created:
                continue

            date = created[:10]  # Extract YYYY-MM-DD

            status = run.get('status', 'Unknown').upper()

            if status in ['PASS', 'PASSED', 'SUCCESS']:
                daily_data[date]['passed'] += 1
            elif status in ['FAIL', 'FAILED', 'FAILURE']:
                daily_data[date]['failed'] += 1
            else:
                daily_data[date]['other'] += 1

        # Convert to sorted list
        sorted_data = []
        for date in sorted(daily_data.keys()):
            data = daily_data[date]
            sorted_data.append({
                'date': date,
                'passed': data['passed'],
                'failed': data['failed'],
                'other': data['other'],
                'total': data['passed'] + data['failed'] + data['other']
            })

        return {'daily_data': sorted_data}

    def _collect_defects(self, test_runs: list) -> list:
        """
        Collect all defects found during test runs.

        Args:
            test_runs: List of test run dictionaries

        Returns:
            List of defect dictionaries with metadata
        """
        defects = []
        seen_defects = set()

        for run in test_runs:
            run_defects = run.get('defects', [])
            for defect_key in run_defects:
                if defect_key not in seen_defects:
                    defects.append({
                        'key': defect_key,
                        'found_in_test': run.get('test_key', ''),
                        'execution': run.get('execution_key', '')
                    })
                    seen_defects.add(defect_key)

        return defects

    def _calculate_duration_stats(self, test_runs: list) -> dict:
        """
        Calculate test execution duration statistics.

        Args:
            test_runs: List of test run dictionaries

        Returns:
            Dictionary with duration statistics:
            - avg_duration_seconds: Average test duration
            - min_duration_seconds: Minimum test duration
            - max_duration_seconds: Maximum test duration
            - total_duration_hours: Total time spent on testing
        """
        durations = []

        for run in test_runs:
            started = run.get('started_on')
            finished = run.get('finished_on')

            if started and finished:
                try:
                    start_time = datetime.fromisoformat(started.replace('Z', '+00:00'))
                    end_time = datetime.fromisoformat(finished.replace('Z', '+00:00'))
                    duration = (end_time - start_time).total_seconds()
                    if duration > 0:
                        durations.append(duration)
                except Exception:
                    continue

        if not durations:
            return {
                'avg_duration_seconds': 0,
                'min_duration_seconds': 0,
                'max_duration_seconds': 0,
                'total_duration_hours': 0
            }

        return {
            'avg_duration_seconds': sum(durations) / len(durations),
            'min_duration_seconds': min(durations),
            'max_duration_seconds': max(durations),
            'total_duration_hours': sum(durations) / 3600
        }

    def get_failing_tests(self) -> list:
        """
        Get list of tests that are currently failing.

        Returns:
            List of dictionaries with failing test information
        """
        failing_tests = []
        seen_tests = set()

        for execution in self.executions:
            for run in execution.get('test_runs', []):
                status = run.get('status', 'Unknown').upper()

                if status in ['FAIL', 'FAILED', 'FAILURE']:
                    test_key = run.get('test_key', '')
                    if test_key not in seen_tests:
                        failing_tests.append({
                            'test_key': test_key,
                            'execution': execution['key'],
                            'status': run.get('status'),
                            'executed_by': run.get('executed_by', ''),
                            'defects': run.get('defects', []),
                            'comment': run.get('comment', '')
                        })
                        seen_tests.add(test_key)

        return failing_tests

    def get_test_coverage_by_plan(self) -> dict:
        """
        Calculate test coverage statistics by test plan.

        Returns:
            Dictionary mapping test plan keys to coverage statistics
        """
        coverage = defaultdict(lambda: {
            'total_tests': 0,
            'executed_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0
        })

        for execution in self.executions:
            plan_key = execution.get('test_plan', 'No Plan')
            test_runs = execution.get('test_runs', [])

            coverage[plan_key]['total_tests'] += len(test_runs)

            for run in test_runs:
                coverage[plan_key]['executed_tests'] += 1

                status = run.get('status', 'Unknown').upper()
                if status in ['PASS', 'PASSED', 'SUCCESS']:
                    coverage[plan_key]['passed_tests'] += 1
                elif status in ['FAIL', 'FAILED', 'FAILURE']:
                    coverage[plan_key]['failed_tests'] += 1

        return dict(coverage)
