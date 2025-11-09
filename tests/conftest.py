"""
Pytest configuration and shared fixtures.

This module contains shared fixtures used across all test modules.
"""

import json
from pathlib import Path

import pytest


@pytest.fixture
def fake_jira_data():
    """
    Load fake Jira data from fixtures.

    Returns:
        dict: Fake Jira data with issues and changelogs
    """
    fixture_path = Path(__file__).parent / 'fixtures' / 'fake_jira_data.json'
    with open(fixture_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data


@pytest.fixture
def fake_issues(fake_jira_data):
    """
    Get fake issues list.

    Returns:
        list: List of fake issue dictionaries
    """
    return fake_jira_data['issues']


@pytest.fixture
def sample_metadata():
    """
    Sample metadata for testing.

    Returns:
        dict: Sample project metadata
    """
    return {
        'project': 'PROJ',
        'start_date': '2024-01-15',
        'end_date': '2024-01-26',
        'label': None,
        'fetched_at': '2024-01-26T12:00:00',
        'total_issues': 5,
    }


@pytest.fixture
def temp_output_dir(tmp_path):
    """
    Create temporary directory for test output files.

    Args:
        tmp_path: pytest's built-in temporary directory fixture

    Returns:
        Path: Path to temporary directory
    """
    output_dir = tmp_path / 'output'
    output_dir.mkdir()
    return output_dir
