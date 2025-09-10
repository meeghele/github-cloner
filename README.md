# GitHub Cloner

<div align="center">
  <img src="images/github-cloner_512.png" alt="GitHub Cloner Logo" width="200"/>
</div>

[![CI](https://github.com/meeghele/github-cloner/actions/workflows/ci.yml/badge.svg)](https://github.com/meeghele/github-cloner/actions)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A Python command-line tool that automates the process of cloning all repositories from a GitHub user or organization.

## Features

- **Complete repository cloning**: Clone all repositories from a specified GitHub user or organization
- **Smart sync**: If a repository is not cloned already, it will be cloned; if it exists, it will be fetched
- **Exclusion patterns**: Option to exclude specific repositories based on name patterns
- **Dry-run mode**: List all repositories without actually cloning them
- **Flexible destination**: Configurable destination path for cloned repositories
- **Organization handling**: Option to disable root organization/user folder creation
- **Enterprise support**: Support for GitHub Enterprise instances with custom API URLs
- **Robust error handling**: Clear error messages and appropriate exit codes

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python github-cloner.py [options]
```

### Authentication

Set your GitHub token using one of these methods:

1. **Environment variable (recommended):**
   ```bash
   export GITHUB_TOKEN=your-api-token
   python github-cloner.py -o myorg
   ```

2. **Command line argument:**
   ```bash
   python github-cloner.py -o myorg -t your-api-token
   ```

### Command Line Options

| Option | Long Option | Description |
|--------|-------------|-------------|
| `-o` | `--organization` | GitHub organization to clone from |
| `-u` | `--user` | GitHub user to clone from |
| `-t` | `--token` | GitHub API token (can also use `GITHUB_TOKEN` env var) |
| `-p` | `--path` | Destination directory (default: current directory) |
| `-d` | `--dry-run` | List repositories without cloning |
| `-e` | `--exclude` | Exclude repositories containing this pattern |
| | `--disable-root` | Don't create organization/user folder |
| | `--url` | GitHub API URL for Enterprise (default: `https://api.github.com`) |
| `-h` | `--help` | Show help message and exit |

### Examples

**Basic usage:**
```bash
python github-cloner.py -o myorg
```

**Clone from user:**
```bash
python github-cloner.py -u username
```

**Clone to specific directory:**
```bash
python github-cloner.py -o myorg -p /path/to/repos
```

**Dry run to see what would be cloned:**
```bash
python github-cloner.py -u username --dry-run
```

**Exclude archived repositories:**
```bash
python github-cloner.py -o myorg --exclude archived
```

**Clone without creating root folder:**
```bash
python github-cloner.py -o myorg --disable-root
```

**Use GitHub Enterprise:**
```bash
python github-cloner.py -o myorg --url https://github.company.com/api/v3
```

## Exit Codes

| Code | Description |
|------|-------------|
| 0 | Success |
| 1 | Execution error |
| 2 | Missing required arguments |
| 10 | Destination path error |
| 20 | Git executable not found |
| 21 | Git clone error |
| 22 | Git fetch error |
| 30 | GitHub API error |
| 40 | Authentication error |

## Token Permissions

Your GitHub token needs:
- **For private repositories**: `repo` scope
- **For public repositories only**: No special scopes required

Create a token at: https://github.com/settings/tokens

## License

This project is licensed under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit issues, feature requests, or pull requests.