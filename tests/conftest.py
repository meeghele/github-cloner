#!/usr/bin/env python3
"""
GitHub Cloner Test Configuration and Fixtures

Copyright (c) 2025 Michele Tavella <meeghele@proton.me>
Licensed under the MIT License.

Author: Michele Tavella <meeghele@proton.me>
"""

import os
import tempfile
from unittest.mock import MagicMock, Mock
from typing import Dict, List, Any

import pytest
import github


@pytest.fixture
def temp_dir():
    """Provide a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def mock_config():
    """Provide a mock configuration for testing."""
    return {
        'url': 'https://github.com',
        'token': 'test-token-123',
        'organization': 'test-org',
        'path': '/tmp/test-path',
        'exclude': ['excluded-repo'],
        'dry_run': False,
        'verbose': False
    }


@pytest.fixture
def mock_github_client():
    """Provide a mock GitHub client."""
    client = Mock(spec=github.Github)
    return client


@pytest.fixture
def mock_repository():
    """Provide a mock GitHub repository."""
    repo = Mock()
    repo.id = 1
    repo.name = 'test-repo'
    repo.full_name = 'test-org/test-repo'
    repo.ssh_url = 'git@github.com:test-org/test-repo.git'
    repo.clone_url = 'https://github.com/test-org/test-repo.git'
    repo.archived = False
    repo.disabled = False
    return repo


@pytest.fixture
def mock_organization():
    """Provide a mock GitHub organization."""
    org = Mock()
    org.login = 'test-org'
    org.name = 'Test Organization'
    return org


@pytest.fixture
def mock_subprocess(monkeypatch):
    """Mock subprocess calls."""
    mock_run = Mock()
    mock_run.returncode = 0
    mock_run.stdout = ''
    mock_run.stderr = ''
    
    def mock_subprocess_run(*args, **kwargs):
        return mock_run
    
    monkeypatch.setattr('subprocess.run', mock_subprocess_run)
    return mock_run


@pytest.fixture
def sample_repositories():
    """Provide sample repository data for testing."""
    return [
        {
            'id': 1,
            'name': 'repo1',
            'full_name': 'test-org/repo1',
            'ssh_url': 'git@github.com:test-org/repo1.git',
            'archived': False,
            'disabled': False
        },
        {
            'id': 2,
            'name': 'repo2',
            'full_name': 'test-org/repo2',
            'ssh_url': 'git@github.com:test-org/repo2.git',
            'archived': False,
            'disabled': False
        }
    ]