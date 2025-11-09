"""
Tests for ReportGenerator module.

This module tests the HTML report generation functionality.
"""

import re
from pathlib import Path

import pytest

from jira_analyzer.analyzer import FlowAnalyzer
from jira_analyzer.reporter import ReportGenerator


class TestReportGenerator:
    """Test cases for ReportGenerator class."""

    @pytest.fixture
    def flow_metrics(self, fake_issues):
        """Generate flow metrics from fake issues."""
        analyzer = FlowAnalyzer(fake_issues)
        return analyzer.calculate_flow_metrics()

    def test_init(self, sample_metadata, flow_metrics):
        """Test ReportGenerator initialization."""
        generator = ReportGenerator(sample_metadata, flow_metrics)

        assert generator.metadata == sample_metadata
        assert generator.flow_metrics == flow_metrics

    def test_calculate_trend_basic(self, sample_metadata, flow_metrics):
        """Test trend line calculation with basic data."""
        generator = ReportGenerator(sample_metadata, flow_metrics)

        x = [1, 2, 3, 4, 5]
        y = [2, 4, 6, 8, 10]

        trend = generator._calculate_trend(x, y)

        assert len(trend) == len(y)
        # Should be approximately linear
        assert abs(trend[0] - 2) < 0.1
        assert abs(trend[-1] - 10) < 0.1

    def test_calculate_trend_single_point(self, sample_metadata, flow_metrics):
        """Test trend line with single data point."""
        generator = ReportGenerator(sample_metadata, flow_metrics)

        x = [1]
        y = [5]

        trend = generator._calculate_trend(x, y)

        assert len(trend) == 1
        assert trend[0] == 5

    def test_calculate_trend_empty(self, sample_metadata, flow_metrics):
        """Test trend line with empty data."""
        generator = ReportGenerator(sample_metadata, flow_metrics)

        x = []
        y = []

        trend = generator._calculate_trend(x, y)

        assert trend == []

    def test_generate_html_creates_file(self, sample_metadata, flow_metrics, temp_output_dir):
        """Test that HTML report file is created."""
        generator = ReportGenerator(sample_metadata, flow_metrics)

        output_path = temp_output_dir / 'test_report.html'
        result_path = generator.generate_html(str(output_path))

        assert Path(result_path).exists()
        assert Path(result_path).is_file()

    def test_generate_html_content_structure(self, sample_metadata, flow_metrics, temp_output_dir):
        """Test that HTML report has proper structure."""
        generator = ReportGenerator(sample_metadata, flow_metrics)

        output_path = temp_output_dir / 'test_report.html'
        generator.generate_html(str(output_path))

        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check basic HTML structure
        assert '<!DOCTYPE html>' in content
        assert '<html lang="pl">' in content
        assert '</html>' in content
        assert '<head>' in content
        assert '<body>' in content

        # Check title
        assert f'<title>Raport Przepływu Błędów Jira - {sample_metadata["project"]}</title>' in content

    def test_generate_html_includes_plotly(self, sample_metadata, flow_metrics, temp_output_dir):
        """Test that Plotly.js is included."""
        generator = ReportGenerator(sample_metadata, flow_metrics)

        output_path = temp_output_dir / 'test_report.html'
        generator.generate_html(str(output_path))

        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check for Plotly CDN
        assert 'plotly' in content.lower()
        assert 'cdn.plot.ly' in content or 'plotly-2' in content

    def test_generate_html_includes_metadata(self, sample_metadata, flow_metrics, temp_output_dir):
        """Test that metadata is included in report."""
        generator = ReportGenerator(sample_metadata, flow_metrics)

        output_path = temp_output_dir / 'test_report.html'
        generator.generate_html(str(output_path))

        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check metadata presence
        assert sample_metadata['project'] in content
        assert str(sample_metadata['total_issues']) in content

    def test_generate_html_includes_statistics(self, sample_metadata, flow_metrics, temp_output_dir):
        """Test that statistics cards are included."""
        generator = ReportGenerator(sample_metadata, flow_metrics)

        output_path = temp_output_dir / 'test_report.html'
        generator.generate_html(str(output_path))

        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check for stat cards (Polish) - simplified to only open bugs
        assert 'Obecnie Otwarte Błędy' in content or 'Currently Open Bugs' in content

    def test_generate_html_includes_charts(self, sample_metadata, flow_metrics, temp_output_dir):
        """Test that chart containers are included."""
        generator = ReportGenerator(sample_metadata, flow_metrics)

        output_path = temp_output_dir / 'test_report.html'
        generator.generate_html(str(output_path))

        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check for chart containers
        assert 'timeline-chart' in content
        assert 'open-chart' in content
        assert 'sankey-chart' in content

    def test_generate_html_includes_javascript(self, sample_metadata, flow_metrics, temp_output_dir):
        """Test that JavaScript for charts is included."""
        generator = ReportGenerator(sample_metadata, flow_metrics)

        output_path = temp_output_dir / 'test_report.html'
        generator.generate_html(str(output_path))

        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check for Plotly.newPlot calls
        assert 'Plotly.newPlot' in content
        assert "type: 'scatter'" in content or "type: \"scatter\"" in content
        assert "type: 'sankey'" in content or "type: \"sankey\"" in content

    def test_generate_html_includes_time_table(self, sample_metadata, flow_metrics, temp_output_dir):
        """Test that time in status table is included."""
        generator = ReportGenerator(sample_metadata, flow_metrics)

        output_path = temp_output_dir / 'test_report.html'
        generator.generate_html(str(output_path))

        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check for time table (Polish)
        assert 'Średni Czas w Każdym Statusie' in content or 'Average Time in Each Status' in content
        assert 'Śr. Dni' in content or 'Avg Days' in content
        assert 'Mediana Dni' in content or 'Median Days' in content

    def test_generate_html_loop_table_removed(self, sample_metadata, flow_metrics, temp_output_dir):
        """Test that rework patterns table is NOT included (removed in refactoring)."""
        generator = ReportGenerator(sample_metadata, flow_metrics)

        output_path = temp_output_dir / 'test_report.html'
        generator.generate_html(str(output_path))

        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Loop table removed - verify it's not present
        assert 'Wzorce Przeróbek' not in content
        assert 'Wzorzec Pętli' not in content

    def test_generate_html_all_flows_gray(self, sample_metadata, flow_metrics, temp_output_dir):
        """Test that all flows are gray in Sankey diagram."""
        generator = ReportGenerator(sample_metadata, flow_metrics)

        output_path = temp_output_dir / 'test_report.html'
        generator.generate_html(str(output_path))

        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check that all flows are gray (no color coding)
        assert 'rgba(128, 128, 128, 0.4)' in content  # All flows gray
        # Verify no green or red colors
        assert 'rgba(34, 197, 94, 0.4)' not in content  # No green
        assert 'rgba(220, 38, 38, 0.4)' not in content  # No red

    def test_generate_html_styling(self, sample_metadata, flow_metrics, temp_output_dir):
        """Test that CSS styling is included."""
        generator = ReportGenerator(sample_metadata, flow_metrics)

        output_path = temp_output_dir / 'test_report.html'
        generator.generate_html(str(output_path))

        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check for CSS
        assert '<style>' in content
        assert '</style>' in content
        assert 'background:' in content or 'background-color:' in content

    def test_generate_html_footer(self, sample_metadata, flow_metrics, temp_output_dir):
        """Test that footer is included."""
        generator = ReportGenerator(sample_metadata, flow_metrics)

        output_path = temp_output_dir / 'test_report.html'
        generator.generate_html(str(output_path))

        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check for footer (Polish)
        assert 'Wygenerowano' in content or 'Generated on' in content
        assert 'Analizator Przepływu Błędów Jira' in content or 'Jira Bug Flow Analyzer' in content

    def test_generate_html_returns_path(self, sample_metadata, flow_metrics, temp_output_dir):
        """Test that generate_html returns the output path."""
        generator = ReportGenerator(sample_metadata, flow_metrics)

        output_path = temp_output_dir / 'test_report.html'
        result = generator.generate_html(str(output_path))

        assert result == str(output_path)

    def test_generate_html_default_filename(self, sample_metadata, flow_metrics):
        """Test that default filename is used when not specified."""
        generator = ReportGenerator(sample_metadata, flow_metrics)

        result = generator.generate_html()

        assert Path(result).exists()
        assert 'jira_flow_report.html' in result

        # Clean up
        Path(result).unlink()

    def test_generate_html_with_empty_metrics(self, sample_metadata):
        """Test report generation with empty metrics."""
        empty_metrics = {
            'total_transitions': 0,
            'unique_statuses': 0,
            'flow_patterns': [],
            'all_statuses': [],
            'loops': {'total_loops': 0, 'issues_with_loops': [], 'common_loops': []},
            'time_in_status': {},
            'timeline': {'daily_data': []},
            'total_issues': 0,
        }

        generator = ReportGenerator(sample_metadata, empty_metrics)

        # Should not raise an error
        result = generator.generate_html()

        assert Path(result).exists()

        # Clean up
        Path(result).unlink()

    def test_generate_html_utf8_encoding(self, sample_metadata, flow_metrics, temp_output_dir):
        """Test that HTML is saved with UTF-8 encoding."""
        # Add Polish characters to metadata
        sample_metadata['project'] = 'PROJ-Błąd'

        generator = ReportGenerator(sample_metadata, flow_metrics)

        output_path = temp_output_dir / 'test_report.html'
        generator.generate_html(str(output_path))

        # Read with UTF-8 and verify Polish characters
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()

        assert 'PROJ-Błąd' in content
        assert '<meta charset="UTF-8">' in content
