#!/usr/bin/env python3
"""
GitHub Cloner Main Class Tests

Copyright (c) 2025 Michele Tavella <meeghele@proton.me>
Licensed under the MIT License.

Author: Michele Tavella <meeghele@proton.me>
"""

import os
import sys
from unittest.mock import patch, Mock, MagicMock
import pytest

# Add the parent directory to sys.path to import the module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the module under test
import importlib.util
spec = importlib.util.spec_from_file_location("github_cloner", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "github-cloner.py"))
gc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gc)


class TestGitHubCloner:
    """Test GitHubCloner main class."""
    
    def test_init(self):
        """Test GitHubCloner initialization."""
        config = gc.Config(
            url='https://api.github.com',
            token='test-token', 
            target_type='organization',
            target_name='test-org',
            path='/test/path',
            disable_root=False,
            dry_run=False,
            exclude=None
        )
        
        cloner = gc.GitHubCloner(config)
        
        assert cloner.config == config
        assert cloner.github_api is None
        assert cloner.repositories == []
    
    @patch('os.path.isdir')
    @patch.object(gc.GitOperations, 'validate_git_available')
    @patch('github.Github')
    def test_validate_environment_success(self, mock_github_class, mock_validate_git, mock_isdir):
        """Test successful environment validation."""
        mock_isdir.return_value = True
        
        config = gc.Config(
            url='https://api.github.com',
            token='test-token',
            target_type='organization',
            target_name='test-org', 
            path='/test/path',
            disable_root=False,
            dry_run=False,
            exclude=None
        )
        
        cloner = gc.GitHubCloner(config)
        
        # Should not raise exception
        cloner._validate_environment()
        
        mock_isdir.assert_called_once_with('/test/path')
        mock_validate_git.assert_called_once()
    
    @patch('os.path.isdir')
    @patch('sys.exit')
    def test_validate_environment_path_not_exists(self, mock_exit, mock_isdir):
        """Test environment validation with invalid path."""
        mock_isdir.return_value = False
        
        config = gc.Config(
            url='https://api.github.com',
            token='test-token',
            target_type='organization',
            target_name='test-org',
            path='/nonexistent/path',
            disable_root=False,
            dry_run=False,
            exclude=None
        )
        
        cloner = gc.GitHubCloner(config)
        cloner._validate_environment()
        
        mock_exit.assert_called_once_with(gc.EXIT_PATH_ERROR)
    
    @patch('github.Github')
    def test_initialize_github_api_success(self, mock_github_class):
        """Test successful GitHub API initialization."""
        mock_api = Mock()
        mock_github_class.return_value = mock_api
        
        config = gc.Config(
            url='https://api.github.com',
            token='test-token',
            target_type='organization',
            target_name='test-org',
            path='/test/path', 
            disable_root=False,
            dry_run=False,
            exclude=None
        )
        
        cloner = gc.GitHubCloner(config)
        cloner._initialize_github_api()
        
        mock_github_class.assert_called_once()
        mock_api.get_user.assert_called_once()
        assert cloner.github_api == mock_api
    
    @patch('github.Github')
    @patch('sys.exit')
    def test_initialize_github_api_failure(self, mock_exit, mock_github_class):
        """Test GitHub API initialization failure."""
        mock_api = Mock()
        mock_api.get_user.side_effect = Exception("Authentication failed")
        mock_github_class.return_value = mock_api
        
        config = gc.Config(
            url='https://api.github.com',
            token='invalid-token',
            target_type='organization',
            target_name='test-org',
            path='/test/path',
            disable_root=False,
            dry_run=False,
            exclude=None
        )
        
        cloner = gc.GitHubCloner(config)
        cloner._initialize_github_api()
        
        mock_exit.assert_called_once_with(gc.EXIT_GITHUB_ERROR)
    
    @patch.object(gc.GitHubCloner, '_process_repositories')
    @patch.object(gc.GitHubCloner, '_collect_repositories')
    @patch.object(gc.GitHubCloner, '_initialize_github_api')
    @patch.object(gc.GitHubCloner, '_validate_environment')
    def test_run_success(self, mock_validate, mock_init_api, mock_collect, mock_process):
        """Test successful run execution."""
        config = gc.Config(
            url='https://api.github.com',
            token='test-token',
            target_type='organization',
            target_name='test-org',
            path='/test/path',
            disable_root=False,
            dry_run=False,
            exclude=None
        )
        
        cloner = gc.GitHubCloner(config)
        result = cloner.run()
        
        assert result == gc.EXIT_SUCCESS
        mock_validate.assert_called_once()
        mock_init_api.assert_called_once()
        mock_collect.assert_called_once()
        mock_process.assert_called_once()
    
    @patch.object(gc.GitHubCloner, '_collect_repositories')
    @patch.object(gc.GitHubCloner, '_initialize_github_api')
    @patch.object(gc.GitHubCloner, '_validate_environment')
    def test_run_dry_run_mode(self, mock_validate, mock_init_api, mock_collect):
        """Test run execution in dry-run mode."""
        config = gc.Config(
            url='https://api.github.com',
            token='test-token',
            target_type='organization',
            target_name='test-org',
            path='/test/path',
            disable_root=False,
            dry_run=True,  # Dry run mode
            exclude=None
        )
        
        cloner = gc.GitHubCloner(config)
        result = cloner.run()
        
        assert result == gc.EXIT_SUCCESS
        mock_validate.assert_called_once()
        mock_init_api.assert_called_once()
        mock_collect.assert_called_once()
        # _process_repositories should not be called in dry-run mode
    
    @patch.object(gc.GitHubCloner, '_validate_environment')
    def test_run_exception_handling(self, mock_validate):
        """Test run exception handling."""
        mock_validate.side_effect = Exception("Test error")
        
        config = gc.Config(
            url='https://api.github.com',
            token='test-token',
            target_type='organization',
            target_name='test-org',
            path='/test/path',
            disable_root=False,
            dry_run=False,
            exclude=None
        )
        
        cloner = gc.GitHubCloner(config)
        result = cloner.run()
        
        assert result == gc.EXIT_EXECUTION_ERROR


class TestUserVsOrganization:
    """Test user vs organization functionality."""
    
    def test_init_with_user_config(self):
        """Test GitHubCloner initialization with user config."""
        config = gc.Config(
            url='https://api.github.com',
            token='test-token',
            target_type='user',
            target_name='test-user',
            path='/test/path',
            disable_root=False,
            dry_run=False,
            exclude=None
        )
        
        cloner = gc.GitHubCloner(config)
        
        assert cloner.config == config
        assert cloner.config.target_type == 'user'
        assert cloner.config.target_name == 'test-user'
        assert cloner.github_api is None
        assert cloner.repositories == []

    @patch('github.Github')
    def test_collect_repositories_user(self, mock_github_class):
        """Test repository collection for user."""
        # Setup mocks
        mock_api = Mock()
        mock_github_class.return_value = mock_api
        
        # Mock authenticated user (different from target user)
        mock_auth_user = Mock()
        mock_auth_user.login = 'authenticated-user'
        
        # Mock target user
        mock_target_user = Mock()
        mock_repo = Mock()
        mock_repo.name = 'test-repo'
        mock_repo.full_name = 'test-user/test-repo'
        mock_target_user.get_repos.return_value = [mock_repo]
        
        # Configure get_user to return different objects based on arguments
        def get_user_side_effect(login=None):
            if login == 'test-user':
                return mock_target_user
            return mock_auth_user
            
        mock_api.get_user.side_effect = get_user_side_effect
        
        config = gc.Config(
            url='https://api.github.com',
            token='test-token',
            target_type='user',
            target_name='test-user',
            path='/test/path',
            disable_root=False,
            dry_run=False,
            exclude=None
        )
        
        cloner = gc.GitHubCloner(config)
        cloner.github_api = mock_api
        cloner._collect_repositories()
        
        # Check that get_user was called twice (once for auth check, once for target)
        assert mock_api.get_user.call_count == 2
        mock_target_user.get_repos.assert_called_once_with(type='owner')
        assert len(cloner.repositories) == 1

    @patch('github.Github')
    def test_collect_repositories_authenticated_user(self, mock_github_class):
        """Test repository collection for authenticated user (own repos)."""
        # Setup mocks
        mock_api = Mock()
        mock_github_class.return_value = mock_api
        
        # Mock authenticated user (same as target user)
        mock_auth_user = Mock()
        mock_auth_user.login = 'test-user'
        
        mock_repo = Mock()
        mock_repo.name = 'private-repo'
        mock_repo.full_name = 'test-user/private-repo'
        mock_auth_user.get_repos.return_value = [mock_repo]
        
        mock_api.get_user.return_value = mock_auth_user
        
        config = gc.Config(
            url='https://api.github.com',
            token='test-token',
            target_type='user',
            target_name='test-user',
            path='/test/path',
            disable_root=False,
            dry_run=False,
            exclude=None
        )
        
        cloner = gc.GitHubCloner(config)
        cloner.github_api = mock_api
        cloner._collect_repositories()
        
        # Check that get_user was called once (for auth check)
        mock_api.get_user.assert_called_once()
        # Check that repos were fetched with affiliation='owner' for own repos
        mock_auth_user.get_repos.assert_called_once_with(affiliation='owner', sort='updated')
        assert len(cloner.repositories) == 1

    @patch('github.Github')
    def test_collect_repositories_organization(self, mock_github_class):
        """Test repository collection for organization."""
        # Setup mocks
        mock_api = Mock()
        mock_github_class.return_value = mock_api
        
        mock_org = Mock()
        mock_repo = Mock()
        mock_repo.name = 'test-repo'
        mock_repo.full_name = 'test-org/test-repo'
        mock_org.get_repos.return_value = [mock_repo]
        
        mock_api.get_organization.return_value = mock_org
        
        config = gc.Config(
            url='https://api.github.com',
            token='test-token',
            target_type='organization',
            target_name='test-org',
            path='/test/path',
            disable_root=False,
            dry_run=False,
            exclude=None
        )
        
        cloner = gc.GitHubCloner(config)
        cloner.github_api = mock_api
        cloner._collect_repositories()
        
        mock_api.get_organization.assert_called_once_with('test-org')
        mock_org.get_repos.assert_called_once()
        assert len(cloner.repositories) == 1


class TestMainFunction:
    """Test main function."""
    
    def test_main_function_exists(self):
        """Test that main function exists and is callable."""
        assert hasattr(gc, 'main')
        assert callable(gc.main)
    
    def test_parse_arguments_function_exists(self):
        """Test that parse_arguments function exists and is callable."""
        assert hasattr(gc, 'parse_arguments')
        assert callable(gc.parse_arguments)