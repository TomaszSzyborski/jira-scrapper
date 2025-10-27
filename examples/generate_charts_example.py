"""
Example script demonstrating how to use the new chart generation features.

This script shows how to:
1. Generate daily issue trends charts (open/raised/closed with trend lines)
2. Generate Xray test execution progress charts
3. Integrate these charts into the main report
"""

import sys
from pathlib import Path

# Add parent directory to path to import jira_scraper
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from jira_scraper import (
    JiraScraper,
    JiraAnalyzer,
    ReportGenerator,
    IssueTrendsChart,
    XrayTestChart,
    ReportConfig,
)


def example_issue_trends_charts():
    """Example: Generate issue trends charts separately."""
    print("=== Example 1: Issue Trends Charts ===\n")

    # Sample ticket data (in practice, this comes from JiraScraper)
    sample_tickets = [
        {
            "key": "PROJ-1",
            "summary": "Test ticket 1",
            "status": "Done",
            "issue_type": "Story",
            "created": "2024-01-01T10:00:00Z",
            "updated": "2024-01-05T10:00:00Z",
            "resolved": "2024-01-05T10:00:00Z",
        },
        {
            "key": "PROJ-2",
            "summary": "Test ticket 2",
            "status": "In Progress",
            "issue_type": "Bug",
            "created": "2024-01-02T10:00:00Z",
            "updated": "2024-01-03T10:00:00Z",
            "resolved": None,
        },
        {
            "key": "PROJ-3",
            "summary": "Test ticket 3",
            "status": "Done",
            "issue_type": "Story",
            "created": "2024-01-03T10:00:00Z",
            "updated": "2024-01-07T10:00:00Z",
            "resolved": "2024-01-07T10:00:00Z",
        },
    ]

    # Create IssueTrendsChart instance
    trends_chart = IssueTrendsChart(sample_tickets)

    # Generate combined chart
    combined_html = trends_chart.create_combined_chart(
        start_date="2024-01-01",
        end_date="2024-01-10",
        title="Daily Issue Trends - Combined View"
    )

    # Save to file
    with open("issue_trends_combined.html", "w") as f:
        f.write(f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Issue Trends - Combined</title>
        </head>
        <body>
            {combined_html}
        </body>
        </html>
        """)
    print("✓ Combined chart saved to: issue_trends_combined.html")

    # Generate separate charts
    separate_charts = trends_chart.create_separate_charts(
        start_date="2024-01-01",
        end_date="2024-01-10"
    )

    # Save each chart
    for chart_type, html in separate_charts.items():
        filename = f"issue_trends_{chart_type}.html"
        with open(filename, "w") as f:
            f.write(f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Issue Trends - {chart_type.title()}</title>
            </head>
            <body>
                {html}
            </body>
            </html>
            """)
        print(f"✓ {chart_type.title()} chart saved to: {filename}")

    # Get summary statistics
    stats = trends_chart.get_summary_statistics(
        start_date="2024-01-01",
        end_date="2024-01-10"
    )
    print(f"\nSummary Statistics:")
    print(f"  Total Raised: {stats['total_raised']}")
    print(f"  Total Closed: {stats['total_closed']}")
    print(f"  Avg Raised/Day: {stats['avg_raised_per_day']:.2f}")
    print(f"  Avg Closed/Day: {stats['avg_closed_per_day']:.2f}")
    print(f"  Final Open Issues: {stats['final_open_issues']}")


def example_xray_test_charts():
    """Example: Generate Xray test execution progress charts."""
    print("\n\n=== Example 2: Xray Test Execution Charts ===\n")

    # Sample Xray test execution data
    test_executions = [
        {
            "key": "PROJ-10",
            "issue_type": "Test Execution",
            "status": "PASS",
            "labels": ["release-1.0", "regression"],
        },
        {
            "key": "PROJ-11",
            "issue_type": "Test Execution",
            "status": "PASS",
            "labels": ["release-1.0"],
        },
        {
            "key": "PROJ-12",
            "issue_type": "Test Execution",
            "status": "FAIL",
            "labels": ["release-1.0", "regression"],
        },
        {
            "key": "PROJ-13",
            "issue_type": "Test Execution",
            "status": "EXECUTING",
            "labels": ["release-1.0"],
        },
        {
            "key": "PROJ-14",
            "issue_type": "Test Execution",
            "status": "TODO",
            "labels": ["release-1.0", "regression"],
        },
        {
            "key": "PROJ-15",
            "issue_type": "Test Execution",
            "status": "TODO",
            "labels": ["release-1.0"],
        },
        {
            "key": "PROJ-16",
            "issue_type": "Test Execution",
            "status": "ABORTED",
            "labels": ["release-1.0"],
        },
    ]

    # Create XrayTestChart instance (filter by label "release-1.0")
    xray_chart = XrayTestChart(test_executions, target_label="release-1.0")

    # Get metrics
    metrics = xray_chart.calculate_test_metrics()
    print(f"Test Execution Metrics:")
    print(f"  Total Tests: {metrics['total_tests']}")
    print(f"  Passed: {metrics['passed']}")
    print(f"  Failed: {metrics['failed']}")
    print(f"  Executing: {metrics['executing']}")
    print(f"  To Do: {metrics['todo']}")
    print(f"  Aborted: {metrics['aborted']}")
    print(f"  Coverage: {metrics['coverage_percent']}%")
    print(f"  Remaining for 100%: {metrics['remaining_for_100_percent']}")

    # Generate complete report
    complete_report = xray_chart.generate_complete_report()

    # Save to file
    with open("xray_test_report.html", "w") as f:
        f.write(f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Xray Test Execution Report</title>
        </head>
        <body>
            {complete_report}
        </body>
        </html>
        """)
    print(f"\n✓ Complete Xray report saved to: xray_test_report.html")

    # Generate individual charts
    pie_chart = xray_chart.create_progress_pie_chart()
    bar_chart = xray_chart.create_progress_bar_chart()
    gauge = xray_chart.create_coverage_gauge()
    readiness = xray_chart.create_release_readiness_chart()

    print("✓ All individual charts generated")


def example_integrated_report():
    """Example: Generate integrated report with all new charts."""
    print("\n\n=== Example 3: Integrated Report with All Charts ===\n")

    # Sample mixed ticket data (regular tickets + test executions)
    all_tickets = [
        {
            "key": "PROJ-1",
            "summary": "Feature A",
            "status": "Done",
            "issue_type": "Story",
            "priority": "High",
            "created": "2024-01-01T10:00:00Z",
            "updated": "2024-01-05T10:00:00Z",
            "resolved": "2024-01-05T10:00:00Z",
            "assignee": "john.doe",
            "reporter": "jane.doe",
            "labels": [],
            "components": [],
            "changelog": [],
        },
        {
            "key": "PROJ-2",
            "summary": "Bug fix B",
            "status": "In Progress",
            "issue_type": "Bug",
            "priority": "Medium",
            "created": "2024-01-02T10:00:00Z",
            "updated": "2024-01-03T10:00:00Z",
            "resolved": None,
            "assignee": "jane.doe",
            "reporter": "john.doe",
            "labels": [],
            "components": [],
            "changelog": [],
        },
        {
            "key": "PROJ-10",
            "summary": "Test execution 1",
            "status": "PASS",
            "issue_type": "Test Execution",
            "priority": "Medium",
            "created": "2024-01-03T10:00:00Z",
            "updated": "2024-01-04T10:00:00Z",
            "resolved": "2024-01-04T10:00:00Z",
            "assignee": "tester",
            "reporter": "qa.lead",
            "labels": ["release-1.0"],
            "components": [],
            "changelog": [],
        },
        {
            "key": "PROJ-11",
            "summary": "Test execution 2",
            "status": "TODO",
            "issue_type": "Test Execution",
            "priority": "Medium",
            "created": "2024-01-04T10:00:00Z",
            "updated": "2024-01-04T10:00:00Z",
            "resolved": None,
            "assignee": "tester",
            "reporter": "qa.lead",
            "labels": ["release-1.0"],
            "components": [],
            "changelog": [],
        },
    ]

    # Analyze data
    analyzer = JiraAnalyzer(all_tickets)
    analyzer.build_dataframes()

    summary_stats = analyzer.get_summary_statistics()
    flow_metrics = analyzer.calculate_flow_metrics()
    cycle_metrics = analyzer.calculate_cycle_metrics()
    temporal_trends = analyzer.calculate_temporal_trends(
        start_date="2024-01-01",
        end_date="2024-01-10",
        granularity="daily"
    )

    # Generate report with new charts
    report_gen = ReportGenerator(
        project_name="PROJ",
        start_date="2024-01-01",
        end_date="2024-01-10"
    )

    output_file = report_gen.generate_html_report(
        summary_stats=summary_stats,
        flow_metrics=flow_metrics,
        cycle_metrics=cycle_metrics,
        temporal_trends=temporal_trends,
        tickets=all_tickets,  # Pass raw tickets for new charts
        xray_label="release-1.0",  # Filter Xray tests by this label
        output_file="integrated_report_with_new_charts.html"
    )

    print(f"✓ Integrated report with all new charts saved to: {output_file}")
    print("\nThe report includes:")
    print("  - Executive Summary")
    print("  - Daily Issue Trends (Raised/Closed/Open with trend lines)")
    print("  - Xray Test Execution Progress (if test executions exist)")
    print("  - Flow Analysis")
    print("  - Temporal Trends")
    print("  - Cycle Metrics")
    print("  - Status Distribution")


if __name__ == "__main__":
    print("Jira Scraper - New Chart Generation Examples")
    print("=" * 60)

    # Run examples
    example_issue_trends_charts()
    example_xray_test_charts()
    example_integrated_report()

    print("\n" + "=" * 60)
    print("All examples completed successfully!")
    print("\nGenerated files:")
    print("  - issue_trends_combined.html")
    print("  - issue_trends_raised.html")
    print("  - issue_trends_closed.html")
    print("  - issue_trends_open.html")
    print("  - xray_test_report.html")
    print("  - integrated_report_with_new_charts.html")
