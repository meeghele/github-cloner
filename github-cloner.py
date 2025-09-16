#!/usr/bin/env python3
"""
GitHub Cloner - Clone and manage all repositories from a GitHub user or organization.

This tool automates the process of cloning or fetching all repositories from
a GitHub user or organization. It provides intelligent sync capabilities, exclusion
patterns, dry-run functionality, and supports both GitHub.com and GitHub
Enterprise instances.

Copyright (c) 2025 Michele Tavella <meeghele@proton.me>
Licensed under the MIT License. See LICENSE file for details.

Author: Michele Tavella <meeghele@proton.me>
Version: 1.0.0
License: MIT
"""

import argparse
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, List, NoReturn, Optional, Union

if TYPE_CHECKING:
    import github.Repository
    import github.NamedUser
    import github.AuthenticatedUser
    import github.Organization

import colorama
import github

# Initialize colorama for cross-platform colored output
colorama.init(autoreset=True)

# Exit codes
EXIT_SUCCESS = 0
EXIT_EXECUTION_ERROR = 1
EXIT_MISSING_ARGUMENTS = 2
EXIT_PATH_ERROR = 10
EXIT_GIT_NOT_FOUND = 20
EXIT_GIT_CLONE_ERROR = 21
EXIT_GIT_FETCH_ERROR = 22
EXIT_GITHUB_ERROR = 30
EXIT_AUTH_ERROR = 40


class CloneMethod(Enum):
    """Enumeration for git clone methods."""

    HTTPS = "https"
    SSH = "ssh"


class TargetType(Enum):
    """Enumeration for GitHub target types."""

    ORGANIZATION = "organization"
    USER = "user"


@dataclass
class Config:
    """Configuration for GitHub cloner."""

    url: str
    token: str
    target_type: TargetType
    target_name: str
    path: str
    disable_root: bool
    dry_run: bool
    exclude: Optional[str]
    clone_method: CloneMethod = CloneMethod.HTTPS


class GitOperations:
    """Handles Git operations like clone and fetch."""

    @staticmethod
    def validate_git_available() -> None:
        """Validate that git executable is available."""
        git_executable = shutil.which("git")
        if git_executable is None:
            Logger.error("error: git executable not installed or not in $PATH")
            sys.exit(EXIT_GIT_NOT_FOUND)
        Logger.debug(f"git: {git_executable}")

    @staticmethod
    def clone_repository(remote_url: str, local_path: str) -> None:
        """Clone a repository."""
        Logger.debug(f"cloning: {remote_url}")
        try:
            result = subprocess.run(
                ["git", "clone", remote_url, local_path],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                Logger.error(f"git clone failed: {result.stderr}")
                if "Permission denied" in result.stderr:
                    Logger.error(
                        "hint: make sure you have SSH keys configured for GitHub"
                    )
                sys.exit(EXIT_GIT_CLONE_ERROR)
        except Exception as e:
            Logger.error(f"unexpected error while cloning: {e}")
            sys.exit(EXIT_GIT_CLONE_ERROR)

    @staticmethod
    def fetch_repository(local_path: str) -> None:
        """Fetch updates for existing repository."""
        Logger.debug(f"fetching: {local_path}")
        try:
            result = subprocess.run(
                ["git", "-C", local_path, "fetch", "--all"],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                Logger.error(f"git fetch failed: {result.stderr}")
                sys.exit(EXIT_GIT_FETCH_ERROR)
        except Exception as e:
            Logger.error(f"unexpected error while fetching: {e}")
            sys.exit(EXIT_GIT_FETCH_ERROR)


class PathManager:
    """Handles path operations and calculations."""

    @staticmethod
    def ensure_parent_directories(path: str) -> None:
        """Create parent directories if they don't exist."""
        parent_dir = os.path.dirname(path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)

    @staticmethod
    def calculate_local_path(
        repo_full_name: str, base_path: str, target_name: str, disable_root: bool
    ) -> str:
        """Calculate local path for repository."""
        folders = [f.strip().lower() for f in repo_full_name.split("/")]

        if disable_root:
            target_lower = target_name.lower()
            if target_lower in folders:
                folders.remove(target_lower)

        local_path = os.path.join(base_path, *folders)
        return os.path.normpath(local_path)


class Logger:
    """Handles formatted console output with colors."""

    PROCESS_NAME = "github-cloner"

    @classmethod
    def debug(cls, *messages: str) -> None:
        """Print debug message in gray."""
        cls._write_stdout(colorama.Fore.LIGHTBLACK_EX, *messages)

    @classmethod
    def info(cls, *messages: str) -> None:
        """Print info message in magenta."""
        cls._write_stdout(colorama.Fore.MAGENTA, *messages)

    @classmethod
    def warn(cls, *messages: str) -> None:
        """Print warning message in yellow."""
        cls._write_stdout(colorama.Fore.YELLOW, *messages)

    @classmethod
    def error(cls, *messages: str) -> None:
        """Print error message in red to stderr."""
        cls._write_stderr(colorama.Fore.RED, *messages)

    @classmethod
    def _write_stdout(cls, color: str, *messages: str) -> None:
        """Write formatted message to stdout."""
        sys.stdout.write(cls._format_line(color, *messages) + "\n")

    @classmethod
    def _write_stderr(cls, color: str, *messages: str) -> None:
        """Write formatted message to stderr."""
        sys.stderr.write(cls._format_line(color, *messages) + "\n")

    @classmethod
    def _get_header(cls) -> str:
        """Get process header with PID."""
        return f"[{cls.PROCESS_NAME}:{os.getpid()}]"

    @classmethod
    def _format_line(cls, color: str, *messages: str) -> str:
        """Format a colored line with header."""
        header = cls._get_header()
        message = " ".join(str(msg) for msg in messages)
        return f"{color}{header}{colorama.Style.RESET_ALL} {message}"


class GitHubCloner:
    """Main class for cloning GitHub repositories."""

    def __init__(self, config: Config):
        """Initialize GitHub cloner with configuration."""
        self.config = config
        self.github_api: Optional[github.Github] = None
        self.repositories: List["github.Repository.Repository"] = []

    def run(self) -> int:
        """Execute the cloning process."""
        try:
            self._validate_environment()
            self._initialize_github_api()
            self._collect_repositories()

            if self.config.dry_run:
                Logger.info("dry-run completed")
                return EXIT_SUCCESS

            self._process_repositories()
            Logger.info("mission accomplished")
            return EXIT_SUCCESS

        except SystemExit as e:
            return int(e.code) if isinstance(e.code, int) else EXIT_EXECUTION_ERROR
        except Exception as e:
            Logger.error(f"unexpected error: {e}")
            return EXIT_EXECUTION_ERROR
        finally:
            self._cleanup()

    def _validate_environment(self) -> None:
        """Validate environment and requirements."""
        # Check destination path
        if not os.path.isdir(self.config.path):
            Logger.error(f"error: destination path does not exist: {self.config.path}")
            sys.exit(EXIT_PATH_ERROR)
        Logger.debug(f"path: {self.config.path}")

        # Check git executable
        GitOperations.validate_git_available()

    def _initialize_github_api(self) -> None:
        """Initialize GitHub API connection."""
        Logger.info("init github auth")
        try:
            auth = github.Auth.Token(self.config.token)

            Logger.info(f"init github api: {self.config.url}")
            if self.config.url != "https://api.github.com":
                # Custom GitHub Enterprise URL
                self.github_api = github.Github(base_url=self.config.url, auth=auth)
            else:
                # Standard GitHub
                self.github_api = github.Github(auth=auth)

            # Test authentication by getting the authenticated user
            user = self.github_api.get_user()
            Logger.debug(f"authenticated as: {user.login}")

        except github.BadCredentialsException:
            Logger.error("authentication failed: invalid token")
            sys.exit(EXIT_AUTH_ERROR)
        except Exception as e:
            Logger.error(f"failed to initialize github api: {e}")
            sys.exit(EXIT_GITHUB_ERROR)

    def _collect_repositories(self) -> None:
        """Collect all repositories from the user or organization."""
        Logger.info(
            f"getting repositories: {self.config.target_name} "
            f"({self.config.target_type})"
        )

        if self.github_api is None:
            Logger.error("github api not initialized")
            sys.exit(EXIT_GITHUB_ERROR)

        try:
            # Determine if we're accessing own repositories
            auth_user = self.github_api.get_user()
            is_own_account = (
                self.config.target_type == TargetType.USER
                and auth_user.login.lower() == self.config.target_name.lower()
            )

            entity: Union[
                "github.Organization.Organization",
                "github.NamedUser.NamedUser",
                "github.AuthenticatedUser.AuthenticatedUser",
            ]

            if self.config.target_type == TargetType.ORGANIZATION:
                entity = self.github_api.get_organization(self.config.target_name)
                Logger.debug(f"found organization: {self.config.target_name}")
                repos = entity.get_repos()
            elif is_own_account:
                # Use authenticated user to access private repos
                entity = auth_user
                Logger.debug(f"found authenticated user: {self.config.target_name}")
                repos = entity.get_repos(  # type: ignore
                    affiliation="owner", sort="updated"
                )
            else:
                # Get public repos for other users
                entity = self.github_api.get_user(self.config.target_name)
                Logger.debug(f"found user: {self.config.target_name}")
                repos = entity.get_repos(type="owner")  # type: ignore

            for repo in repos:
                if not self._is_excluded(repo.name):
                    self.repositories.append(repo)
                    Logger.debug(f"found: {repo.full_name}")
                else:
                    Logger.warn(f"excluding: {repo.full_name}")

            Logger.info(f"found {len(self.repositories)} repositories to process")

            # If no repositories found for a user, provide helpful guidance
            if (
                len(self.repositories) == 0
                and self.config.target_type == TargetType.USER
            ):
                Logger.warn("no repositories found. this could mean:")
                Logger.warn("- the user has no repositories")
                Logger.warn(
                    "- All repositories are private and your token lacks 'repo' scope"
                )
                Logger.warn(
                    "- Check your token has the necessary permissions for private repos"
                )

        except github.GithubException as e:
            if e.status == 404:
                Logger.error(
                    f"{self.config.target_type.value.capitalize()} "
                    f"'{self.config.target_name}' not found"
                )
            else:
                Logger.error(
                    f"failed to get {self.config.target_type.value} repositories: {e}"
                )
            sys.exit(EXIT_GITHUB_ERROR)
        except Exception as e:
            Logger.error(f"unexpected error while collecting repositories: {e}")
            sys.exit(EXIT_GITHUB_ERROR)

    def _is_excluded(self, repo_name: str) -> bool:
        """Check if repository matches exclusion pattern."""
        if self.config.exclude:
            return self.config.exclude in repo_name
        return False

    def _process_repositories(self) -> None:
        """Clone or fetch all collected repositories."""
        for repo in self.repositories:
            self._process_single_repository(repo)

    def _process_single_repository(self, repo: "github.Repository.Repository") -> None:
        """Process a single repository - clone or fetch."""
        Logger.info(f"processing: {repo.full_name}")

        # Get repository paths
        if self.config.clone_method == CloneMethod.SSH:
            remote_url = repo.ssh_url
        else:
            remote_url = repo.clone_url
        local_path = PathManager.calculate_local_path(
            repo.full_name,
            self.config.path,
            self.config.target_name,
            self.config.disable_root,
        )

        Logger.debug(f"remote: {remote_url}")
        Logger.debug(f"path: {local_path}")

        # Create parent directories
        PathManager.ensure_parent_directories(local_path)

        # Clone or fetch
        if not os.path.isdir(local_path):
            GitOperations.clone_repository(remote_url, local_path)
        else:
            GitOperations.fetch_repository(local_path)

    def _cleanup(self) -> None:
        """Clean up resources."""
        if self.github_api:
            self.github_api.close()


def parse_arguments() -> Config:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Clone all repositories from a GitHub user or organization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s -o myorg
  %(prog)s -u username
  %(prog)s -o myorg -p /path/to/repos --dry-run
  %(prog)s -u username --exclude archived
  %(prog)s -o myorg --url https://github.enterprise.com/api/v3
        """,
    )

    parser.add_argument(
        "--url",
        dest="url",
        default="https://api.github.com",
        help="Base URL of the GitHub API (default: https://api.github.com)",
    )

    parser.add_argument(
        "-t",
        "--token",
        dest="token",
        help="GitHub API token (can also use GITHUB_TOKEN env var)",
    )

    # Mutually exclusive group for target specification
    target_group = parser.add_mutually_exclusive_group(required=True)
    target_group.add_argument(
        "-o",
        "--organization",
        dest="organization",
        help="GitHub organization to clone repositories from",
    )
    target_group.add_argument(
        "-u",
        "--user",
        dest="user",
        help="GitHub user to clone repositories from",
    )

    parser.add_argument(
        "-p",
        "--path",
        dest="path",
        default=os.getcwd(),
        help="Destination path for cloned projects (default: current directory)",
    )

    parser.add_argument(
        "--disable-root",
        action="store_true",
        dest="disable_root",
        help="Do not create root organization folder in path",
    )

    parser.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        dest="dry_run",
        help="List the repositories without clone/fetch",
    )

    parser.add_argument(
        "-e",
        "--exclude",
        dest="exclude",
        help="Pattern to exclude from repository names",
    )

    parser.add_argument(
        "--clone-method",
        dest="clone_method",
        choices=[method.value for method in CloneMethod],
        default=CloneMethod.HTTPS.value,
        help="Clone method: https or ssh (default: https)",
    )

    args = parser.parse_args()

    # Handle token
    token = args.token or os.getenv("GITHUB_TOKEN")
    if not token:
        Logger.error(
            "error: GitHub token not provided. "
            "use -t or set GITHUB_TOKEN environment variable"
        )
        sys.exit(EXIT_AUTH_ERROR)

    if args.token:
        Logger.warn(
            "warning: token provided via command line argument "
            "(consider using environment variable)"
        )

    # Determine target type and name
    if args.organization:
        target_type = TargetType.ORGANIZATION
        target_name = args.organization
    else:  # args.user must be set due to mutually exclusive group
        target_type = TargetType.USER
        target_name = args.user

    return Config(
        url=args.url,
        token=token,
        target_type=target_type,
        target_name=target_name,
        path=args.path,
        disable_root=args.disable_root,
        dry_run=args.dry_run,
        exclude=args.exclude,
        clone_method=CloneMethod(args.clone_method),
    )


def main() -> NoReturn:
    """Main entry point."""
    if __name__ != "__main__":
        sys.exit(EXIT_EXECUTION_ERROR)

    config = parse_arguments()
    cloner = GitHubCloner(config)
    sys.exit(cloner.run())


if __name__ == "__main__":
    main()
