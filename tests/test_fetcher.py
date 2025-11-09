"""
Tests for JiraFetcher module.

This module tests the Jira API integration using monkeypatching
to avoid actual API calls.
"""

import os
from unittest.mock import Mock, MagicMock

import pytest

from jira_analyzer.fetcher import JiraFetcher


class TestJiraFetcher:
    """Test cases for JiraFetcher class."""

    def test_init_with_cloud_credentials(self, monkeypatch):
        """Test initialization with Cloud credentials (email + token)."""
        monkeypatch.setenv('JIRA_URL', 'https://test.atlassian.net')
        monkeypatch.setenv('JIRA_EMAIL', 'test@example.com')
        monkeypatch.setenv('JIRA_API_TOKEN', 'test_token_123')

        # Mock JIRA client
        mock_jira = Mock()
        monkeypatch.setattr('jira_analyzer.fetcher.JIRA', lambda **kwargs: mock_jira)

        fetcher = JiraFetcher()

        assert fetcher.jira_url == 'https://test.atlassian.net'
        assert fetcher.jira is not None

    def test_init_with_onprem_credentials(self, monkeypatch):
        """Test initialization with On-Premise credentials (username + password)."""
        monkeypatch.setenv('JIRA_URL', 'https://jira.company.com')
        monkeypatch.setenv('JIRA_USERNAME', 'testuser')
        monkeypatch.setenv('JIRA_PASSWORD', 'testpass')
        monkeypatch.delenv('JIRA_EMAIL', raising=False)
        monkeypatch.delenv('JIRA_API_TOKEN', raising=False)

        # Mock JIRA client
        mock_jira = Mock()
        monkeypatch.setattr('jira_analyzer.fetcher.JIRA', lambda **kwargs: mock_jira)

        fetcher = JiraFetcher()

        assert fetcher.jira_url == 'https://jira.company.com'
        assert fetcher.jira is not None

    def test_init_missing_url(self, monkeypatch):
        """Test initialization fails without JIRA_URL."""
        monkeypatch.delenv('JIRA_URL', raising=False)

        with pytest.raises(ValueError, match="JIRA_URL not found"):
            JiraFetcher()

    def test_init_missing_credentials(self, monkeypatch):
        """Test initialization fails without credentials."""
        monkeypatch.setenv('JIRA_URL', 'https://test.atlassian.net')
        monkeypatch.delenv('JIRA_EMAIL', raising=False)
        monkeypatch.delenv('JIRA_API_TOKEN', raising=False)
        monkeypatch.delenv('JIRA_USERNAME', raising=False)
        monkeypatch.delenv('JIRA_PASSWORD', raising=False)

        with pytest.raises(ValueError, match="Missing credentials"):
            JiraFetcher()

    def test_build_jql_basic(self, monkeypatch):
        """Test JQL building with basic project only."""
        monkeypatch.setenv('JIRA_URL', 'https://test.atlassian.net')
        monkeypatch.setenv('JIRA_EMAIL', 'test@example.com')
        monkeypatch.setenv('JIRA_API_TOKEN', 'test_token')
        mock_jira = Mock()
        monkeypatch.setattr('jira_analyzer.fetcher.JIRA', lambda **kwargs: mock_jira)

        fetcher = JiraFetcher()
        jql = fetcher.build_jql('PROJ')

        assert 'project = "PROJ"' in jql
        assert 'type in (Bug, "Błąd w programie")' in jql
        assert 'ORDER BY created ASC' in jql

    def test_build_jql_ignores_label(self, monkeypatch):
        """Test that JQL building does NOT include label filter (label filtering is in analyzer)."""
        monkeypatch.setenv('JIRA_URL', 'https://test.atlassian.net')
        monkeypatch.setenv('JIRA_EMAIL', 'test@example.com')
        monkeypatch.setenv('JIRA_API_TOKEN', 'test_token')
        mock_jira = Mock()
        monkeypatch.setattr('jira_analyzer.fetcher.JIRA', lambda **kwargs: mock_jira)

        fetcher = JiraFetcher()
        jql = fetcher.build_jql('PROJ')

        assert 'project = "PROJ"' in jql
        assert 'labels' not in jql  # Label filtering should NOT be in JQL
        assert 'type in (Bug, "Błąd w programie")' in jql

    def test_fetch_issues(self, monkeypatch, fake_issues):
        """Test fetching issues with mocked Jira API."""
        monkeypatch.setenv('JIRA_URL', 'https://test.atlassian.net')
        monkeypatch.setenv('JIRA_EMAIL', 'test@example.com')
        monkeypatch.setenv('JIRA_API_TOKEN', 'test_token')

        # Create mock Jira issue objects
        mock_issues = []
        for issue_data in fake_issues:
            mock_issue = MagicMock()
            mock_issue.key = issue_data['key']
            mock_issue.id = issue_data['id']
            mock_issue.raw = {
                'fields': {
                    'summary': issue_data['summary'],
                    'status': {'name': issue_data['status']},
                    'issuetype': {'name': issue_data['issue_type']},
                    'priority': {'name': issue_data['priority']} if issue_data.get('priority') else None,
                    'assignee': {'displayName': issue_data['assignee']} if issue_data.get('assignee') else None,
                    'reporter': {'displayName': issue_data['reporter']} if issue_data.get('reporter') else None,
                    'created': issue_data['created'],
                    'updated': issue_data['updated'],
                    'resolutiondate': issue_data.get('resolved'),
                    'labels': issue_data.get('labels', []),
                    'components': [{'name': c} for c in issue_data.get('components', [])],
                    'description': issue_data.get('description', ''),
                }
            }

            # Mock changelog
            mock_changelog = MagicMock()
            mock_histories = []
            for change in issue_data.get('changelog', []):
                mock_history = MagicMock()
                mock_history.created = change['created']
                mock_history.author.displayName = change['author']

                mock_item = MagicMock()
                mock_item.field = 'status'
                mock_item.fromString = change['from_string']
                mock_item.toString = change['to_string']
                mock_history.items = [mock_item]

                mock_histories.append(mock_history)

            mock_changelog.histories = mock_histories
            mock_issue.changelog = mock_changelog

            mock_issues.append(mock_issue)

        # Mock JIRA client
        mock_jira = MagicMock()
        mock_jira.search_issues.return_value = mock_issues
        monkeypatch.setattr('jira_analyzer.fetcher.JIRA', lambda **kwargs: mock_jira)

        fetcher = JiraFetcher()
        issues = fetcher.fetch_issues('PROJ', batch_size=100)

        assert len(issues) == len(fake_issues)
        assert issues[0]['key'] == 'PROJ-101'
        assert issues[0]['summary'] == 'Login button not working on mobile'
        assert len(issues[0]['changelog']) > 0

    def test_fetch_issues_batch_processing(self, monkeypatch, fake_issues):
        """Test that batch processing works correctly."""
        monkeypatch.setenv('JIRA_URL', 'https://test.atlassian.net')
        monkeypatch.setenv('JIRA_EMAIL', 'test@example.com')
        monkeypatch.setenv('JIRA_API_TOKEN', 'test_token')

        # Create mock issues (simplified)
        mock_issue1 = MagicMock()
        mock_issue1.key = 'PROJ-101'
        mock_issue1.id = '10001'
        mock_issue1.raw = {'fields': {'summary': 'Test 1', 'status': {'name': 'Open'}}}
        mock_issue1.changelog = MagicMock()
        mock_issue1.changelog.histories = []

        mock_issue2 = MagicMock()
        mock_issue2.key = 'PROJ-102'
        mock_issue2.id = '10002'
        mock_issue2.raw = {'fields': {'summary': 'Test 2', 'status': {'name': 'Closed'}}}
        mock_issue2.changelog = MagicMock()
        mock_issue2.changelog.histories = []

        # Mock JIRA to return issues in batches
        mock_jira = MagicMock()
        call_count = [0]

        def search_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return [mock_issue1]
            else:
                return []

        mock_jira.search_issues.side_effect = search_side_effect
        monkeypatch.setattr('jira_analyzer.fetcher.JIRA', lambda **kwargs: mock_jira)

        fetcher = JiraFetcher()
        issues = fetcher.fetch_issues('PROJ', batch_size=1)

        assert len(issues) == 1
        assert mock_jira.search_issues.call_count == 2  # Second call returns empty

    def test_issue_to_dict_conversion(self, monkeypatch):
        """Test that _issue_to_dict properly converts Jira objects."""
        monkeypatch.setenv('JIRA_URL', 'https://test.atlassian.net')
        monkeypatch.setenv('JIRA_EMAIL', 'test@example.com')
        monkeypatch.setenv('JIRA_API_TOKEN', 'test_token')
        mock_jira = Mock()
        monkeypatch.setattr('jira_analyzer.fetcher.JIRA', lambda **kwargs: mock_jira)

        fetcher = JiraFetcher()

        # Create mock issue
        mock_issue = MagicMock()
        mock_issue.key = 'PROJ-123'
        mock_issue.id = '10123'
        mock_issue.raw = {
            'fields': {
                'summary': 'Test Summary',
                'status': {'name': 'In Progress'},
                'issuetype': {'name': 'Bug'},
                'priority': {'name': 'High'},
                'assignee': {'displayName': 'John Doe'},
                'reporter': {'displayName': 'Jane Smith'},
                'created': '2024-01-15T10:00:00.000+0000',
                'updated': '2024-01-16T12:00:00.000+0000',
                'resolutiondate': None,
                'labels': ['test', 'bug'],
                'components': [{'name': 'Frontend'}],
                'description': 'Test description',
            }
        }
        mock_issue.changelog = MagicMock()
        mock_issue.changelog.histories = []

        result = fetcher._issue_to_dict(mock_issue)

        assert result['key'] == 'PROJ-123'
        assert result['summary'] == 'Test Summary'
        assert result['status'] == 'In Progress'
        assert result['priority'] == 'High'
        assert result['assignee'] == 'John Doe'
        assert result['labels'] == ['test', 'bug']
        assert result['components'] == ['Frontend']
