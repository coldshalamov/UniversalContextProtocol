# CI/CD Setup and Release Process

This document explains how to configure GitHub Actions for automated testing, linting, and releases for the Universal Context Protocol (UCP).

## Overview

UCP uses GitHub Actions for continuous integration and deployment:

- **Tests Workflow** (`.github/workflows/test.yml`): Runs tests with coverage on every PR and push to main
- **Lint Workflow** (`.github/workflows/lint.yml`): Runs code quality checks on every PR and push to main
- **Release Workflow** (`.github/workflows/release.yml`): Builds and publishes packages on version tags

## Setting Up GitHub Secrets

To enable automated releases, you need to configure the following secrets in your GitHub repository:

### Required Secrets

#### For PyPI Publishing

1. **PYPI_API_TOKEN**: API token for publishing to PyPI
   - Generate at: https://pypi.org/manage/account/token/
   - Scope: "Entire account" (recommended) or specific to UCP packages
   - Permissions: Upload packages

#### For Docker Hub Publishing

2. **DOCKER_USERNAME**: Your Docker Hub username
3. **DOCKER_PASSWORD**: Your Docker Hub password or access token
   - Generate an access token at: https://hub.docker.com/settings/security
   - Use access tokens instead of passwords for better security

### How to Add Secrets

1. Go to your repository on GitHub
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add each secret:
   - Name: `PYPI_API_TOKEN`
   - Value: Your PyPI API token
   - Click **Add secret**
5. Repeat for `DOCKER_USERNAME` and `DOCKER_PASSWORD`

### Secret Best Practices

- Never commit secrets to the repository
- Use access tokens instead of passwords where possible
- Rotate tokens regularly (e.g., every 90 days)
- Limit token scopes to minimum required permissions
- Enable secret scanning in repository settings

## CI/CD Workflows

### Test Workflow

**File**: `.github/workflows/test.yml`

**Triggers**:
- Pull requests to `main` branch
- Pushes to `main` branch

**What it does**:
1. Sets up Python 3.11 environment
2. Installs dependencies for all packages (ucp-core, ucp-mvp, ucp-cloud)
3. Runs pytest with coverage
4. Fails if coverage drops below 80%
5. Uploads coverage reports to Codecov
6. Uploads HTML coverage artifacts

**Viewing Results**:
- Check the **Actions** tab in your repository
- Click on a test run to see detailed logs
- Download coverage artifacts for detailed reports

### Lint Workflow

**File**: `.github/workflows/lint.yml`

**Triggers**:
- Pull requests to `main` branch
- Pushes to `main` branch

**What it does**:
1. Sets up Python 3.11 environment
2. Runs ruff for linting
3. Runs mypy for type checking
4. Runs black for code formatting checks
5. Runs ruff format check

**Viewing Results**:
- Linting errors appear directly in PR diffs
- Check the **Actions** tab for detailed logs

### Release Workflow

**File**: `.github/workflows/release.yml`

**Triggers**:
- Tags matching `v*` (e.g., `v1.0.0`, `v0.1.0-alpha1`)

**What it does**:
1. Builds Python packages (wheels + sdist) for all three packages
2. Builds Docker image
3. Publishes packages to PyPI
4. Pushes Docker image to Docker Hub
5. Creates GitHub Release with artifacts

## Release Process

### Prerequisites

Before creating a release:

1. **All tests must pass**: Ensure CI checks are green
2. **Coverage threshold met**: Code coverage must be ≥ 80%
3. **Version updated**: Update version numbers in all `pyproject.toml` files
4. **Changelog updated**: Document changes in `CHANGELOG.md`

### Creating a Release

#### Step 1: Update Version Numbers

Update versions in all `pyproject.toml` files:

```bash
# shared/pyproject.toml
version = "0.2.0"

# local/pyproject.toml
version = "0.2.0"

# cloud/pyproject.toml
version = "0.2.0"
```

#### Step 2: Update CHANGELOG.md

Add release notes to `CHANGELOG.md`:

```markdown
## [0.2.0] - 2025-01-11

### Added
- Feature A
- Feature B

### Changed
- Improved C

### Fixed
- Bug fix D
```

#### Step 3: Commit and Push

```bash
git add .
git commit -m "Release v0.2.0"
git push origin main
```

#### Step 4: Create and Push Tag

```bash
git tag v0.2.0
git push origin v0.2.0
```

#### Step 5: Monitor Release

1. Go to **Actions** tab in GitHub
2. Click on the **Release** workflow run
3. Monitor progress:
   - Build Python packages
   - Build Docker image
   - Publish to PyPI
   - Push to Docker Hub
   - Create GitHub Release

### Release Artifacts

The release workflow creates the following artifacts:

#### Python Packages
- `ucp-core-<version>-py3-none-any.whl`
- `ucp-core-<version>.tar.gz`
- `ucp-mvp-<version>-py3-none-any.whl`
- `ucp-mvp-<version>.tar.gz`
- `ucp-cloud-<version>-py3-none-any.whl`
- `ucp-cloud-<version>.tar.gz`

#### Docker Images
- `docker.io/<username>/ucp:<version>`
- `docker.io/<username>/ucp:latest`

#### GitHub Release
- Release notes with installation instructions
- All Python packages attached as release assets

### Verifying Release

After the release completes:

1. **Check PyPI**:
   - https://pypi.org/project/ucp-core/
   - https://pypi.org/project/ucp-mvp/
   - https://pypi.org/project/ucp-cloud/

2. **Check Docker Hub**:
   - https://hub.docker.com/r/<username>/ucp/tags

3. **Test Installation**:
   ```bash
   # Test PyPI packages
   pip install ucp-core==0.2.0
   pip install ucp-mvp==0.2.0
   pip install ucp-cloud==0.2.0

   # Test Docker image
   docker pull <username>/ucp:0.2.0
   docker run <username>/ucp:0.2.0 ucp --help
   ```

### Rolling Back a Release

If a release has critical issues:

1. **Yank from PyPI**:
   - Go to PyPI project page
   - Click "History" tab
   - Select the version and click "Yank"
   - This prevents new installations but doesn't remove existing ones

2. **Delete Docker tag** (optional):
   ```bash
   docker rmi <username>/ucp:0.2.0
   ```
   Note: You cannot delete public Docker Hub tags, but you can deprecate them.

3. **Create new release**:
   - Fix the issues
   - Bump version (e.g., `v0.2.1`)
   - Follow the release process again

## Troubleshooting

### Release Workflow Fails

**Problem**: PyPI publishing fails

**Solutions**:
1. Verify `PYPI_API_TOKEN` secret is set correctly
2. Check token has "Upload packages" permission
3. Ensure package name doesn't already exist on PyPI (for first release)
4. Check version number follows semantic versioning (MAJOR.MINOR.PATCH)

**Problem**: Docker Hub push fails

**Solutions**:
1. Verify `DOCKER_USERNAME` and `DOCKER_PASSWORD` secrets
2. Check Docker Hub account is active
3. Ensure image name doesn't conflict with existing images
4. Check Docker Hub rate limits

### Test Workflow Fails

**Problem**: Coverage threshold not met

**Solutions**:
1. Add tests for uncovered code
2. Adjust coverage threshold in `.github/workflows/test.yml` if necessary
3. Check coverage report to identify gaps

**Problem**: Tests fail intermittently

**Solutions**:
1. Check for flaky tests (non-deterministic behavior)
2. Add retries or timeouts for network-dependent tests
3. Ensure tests don't depend on external services

### Lint Workflow Fails

**Problem**: Type checking errors

**Solutions**:
1. Add type hints to functions
2. Use `# type: ignore` for intentional violations
3. Update `mypy` configuration in `pyproject.toml`

**Problem**: Formatting issues

**Solutions**:
1. Run `ruff format .` locally to auto-fix
2. Run `black .` locally to auto-fix
3. Configure pre-commit hooks to catch issues early

## Pre-commit Hooks (Optional)

To catch issues before pushing:

```bash
# Install pre-commit
pip install pre-commit

# Create .pre-commit-config.yaml
cat > .pre-commit-config.yaml << EOF
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.9
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
EOF

# Install hooks
pre-commit install
```

## CI/CD Status Badges

Add these badges to your README.md:

```markdown
![Tests](https://github.com/yourusername/UniversalContextProtocol/actions/workflows/test.yml/badge.svg)
![Lint](https://github.com/yourusername/UniversalContextProtocol/actions/workflows/lint.yml/badge.svg)
![Coverage](https://codecov.io/gh/yourusername/UniversalContextProtocol/branch/main/graph/badge.svg)
```

Replace `yourusername` with your actual GitHub username.

## Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [PyPI Publishing Guide](https://packaging.python.org/tutorials/packaging-projects/)
- [Docker Hub Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Semantic Versioning](https://semver.org/)

This document explains how to configure GitHub Actions for automated testing, linting, and releases for the Universal Context Protocol (UCP).

## Overview

UCP uses GitHub Actions for continuous integration and deployment:

- **Tests Workflow** (`.github/workflows/test.yml`): Runs tests with coverage on every PR and push to main
- **Lint Workflow** (`.github/workflows/lint.yml`): Runs code quality checks on every PR and push to main
- **Release Workflow** (`.github/workflows/release.yml`): Builds and publishes packages on version tags

## Setting Up GitHub Secrets

To enable automated releases, you need to configure the following secrets in your GitHub repository:

### Required Secrets

#### For PyPI Publishing

1. **PYPI_API_TOKEN**: API token for publishing to PyPI
   - Generate at: https://pypi.org/manage/account/token/
   - Scope: "Entire account" (recommended) or specific to UCP packages
   - Permissions: Upload packages

#### For Docker Hub Publishing

2. **DOCKER_USERNAME**: Your Docker Hub username
3. **DOCKER_PASSWORD**: Your Docker Hub password or access token
   - Generate an access token at: https://hub.docker.com/settings/security
   - Use access tokens instead of passwords for better security

### How to Add Secrets

1. Go to your repository on GitHub
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add each secret:
   - Name: `PYPI_API_TOKEN`
   - Value: Your PyPI API token
   - Click **Add secret**
5. Repeat for `DOCKER_USERNAME` and `DOCKER_PASSWORD`

### Secret Best Practices

- Never commit secrets to the repository
- Use access tokens instead of passwords where possible
- Rotate tokens regularly (e.g., every 90 days)
- Limit token scopes to minimum required permissions
- Enable secret scanning in repository settings

## CI/CD Workflows

### Test Workflow

**File**: `.github/workflows/test.yml`

**Triggers**:
- Pull requests to `main` branch
- Pushes to `main` branch

**What it does**:
1. Sets up Python 3.11 environment
2. Installs dependencies for all packages (ucp-core, ucp-mvp, ucp-cloud)
3. Runs pytest with coverage
4. Fails if coverage drops below 80%
5. Uploads coverage reports to Codecov
6. Uploads HTML coverage artifacts

**Viewing Results**:
- Check the **Actions** tab in your repository
- Click on a test run to see detailed logs
- Download coverage artifacts for detailed reports

### Lint Workflow

**File**: `.github/workflows/lint.yml`

**Triggers**:
- Pull requests to `main` branch
- Pushes to `main` branch

**What it does**:
1. Sets up Python 3.11 environment
2. Runs ruff for linting
3. Runs mypy for type checking
4. Runs black for code formatting checks
5. Runs ruff format check

**Viewing Results**:
- Linting errors appear directly in PR diffs
- Check the **Actions** tab for detailed logs

### Release Workflow

**File**: `.github/workflows/release.yml`

**Triggers**:
- Tags matching `v*` (e.g., `v1.0.0`, `v0.1.0-alpha1`)

**What it does**:
1. Builds Python packages (wheels + sdist) for all three packages
2. Builds Docker image
3. Publishes packages to PyPI
4. Pushes Docker image to Docker Hub
5. Creates GitHub Release with artifacts

## Release Process

### Prerequisites

Before creating a release:

1. **All tests must pass**: Ensure CI checks are green
2. **Coverage threshold met**: Code coverage must be ≥ 80%
3. **Version updated**: Update version numbers in all `pyproject.toml` files
4. **Changelog updated**: Document changes in `CHANGELOG.md`

### Creating a Release

#### Step 1: Update Version Numbers

Update versions in all `pyproject.toml` files:

```bash
# shared/pyproject.toml
version = "0.2.0"

# local/pyproject.toml
version = "0.2.0"

# cloud/pyproject.toml
version = "0.2.0"
```

#### Step 2: Update CHANGELOG.md

Add release notes to `CHANGELOG.md`:

```markdown
## [0.2.0] - 2025-01-11

### Added
- Feature A
- Feature B

### Changed
- Improved C

### Fixed
- Bug fix D
```

#### Step 3: Commit and Push

```bash
git add .
git commit -m "Release v0.2.0"
git push origin main
```

#### Step 4: Create and Push Tag

```bash
git tag v0.2.0
git push origin v0.2.0
```

#### Step 5: Monitor Release

1. Go to **Actions** tab in GitHub
2. Click on the **Release** workflow run
3. Monitor progress:
   - Build Python packages
   - Build Docker image
   - Publish to PyPI
   - Push to Docker Hub
   - Create GitHub Release

### Release Artifacts

The release workflow creates the following artifacts:

#### Python Packages
- `ucp-core-<version>-py3-none-any.whl`
- `ucp-core-<version>.tar.gz`
- `ucp-mvp-<version>-py3-none-any.whl`
- `ucp-mvp-<version>.tar.gz`
- `ucp-cloud-<version>-py3-none-any.whl`
- `ucp-cloud-<version>.tar.gz`

#### Docker Images
- `docker.io/<username>/ucp:<version>`
- `docker.io/<username>/ucp:latest`

#### GitHub Release
- Release notes with installation instructions
- All Python packages attached as release assets

### Verifying Release

After the release completes:

1. **Check PyPI**:
   - https://pypi.org/project/ucp-core/
   - https://pypi.org/project/ucp-mvp/
   - https://pypi.org/project/ucp-cloud/

2. **Check Docker Hub**:
   - https://hub.docker.com/r/<username>/ucp/tags

3. **Test Installation**:
   ```bash
   # Test PyPI packages
   pip install ucp-core==0.2.0
   pip install ucp-mvp==0.2.0
   pip install ucp-cloud==0.2.0

   # Test Docker image
   docker pull <username>/ucp:0.2.0
   docker run <username>/ucp:0.2.0 ucp --help
   ```

### Rolling Back a Release

If a release has critical issues:

1. **Yank from PyPI**:
   - Go to PyPI project page
   - Click "History" tab
   - Select the version and click "Yank"
   - This prevents new installations but doesn't remove existing ones

2. **Delete Docker tag** (optional):
   ```bash
   docker rmi <username>/ucp:0.2.0
   ```
   Note: You cannot delete public Docker Hub tags, but you can deprecate them.

3. **Create new release**:
   - Fix the issues
   - Bump version (e.g., `v0.2.1`)
   - Follow the release process again

## Troubleshooting

### Release Workflow Fails

**Problem**: PyPI publishing fails

**Solutions**:
1. Verify `PYPI_API_TOKEN` secret is set correctly
2. Check token has "Upload packages" permission
3. Ensure package name doesn't already exist on PyPI (for first release)
4. Check version number follows semantic versioning (MAJOR.MINOR.PATCH)

**Problem**: Docker Hub push fails

**Solutions**:
1. Verify `DOCKER_USERNAME` and `DOCKER_PASSWORD` secrets
2. Check Docker Hub account is active
3. Ensure image name doesn't conflict with existing images
4. Check Docker Hub rate limits

### Test Workflow Fails

**Problem**: Coverage threshold not met

**Solutions**:
1. Add tests for uncovered code
2. Adjust coverage threshold in `.github/workflows/test.yml` if necessary
3. Check coverage report to identify gaps

**Problem**: Tests fail intermittently

**Solutions**:
1. Check for flaky tests (non-deterministic behavior)
2. Add retries or timeouts for network-dependent tests
3. Ensure tests don't depend on external services

### Lint Workflow Fails

**Problem**: Type checking errors

**Solutions**:
1. Add type hints to functions
2. Use `# type: ignore` for intentional violations
3. Update `mypy` configuration in `pyproject.toml`

**Problem**: Formatting issues

**Solutions**:
1. Run `ruff format .` locally to auto-fix
2. Run `black .` locally to auto-fix
3. Configure pre-commit hooks to catch issues early

## Pre-commit Hooks (Optional)

To catch issues before pushing:

```bash
# Install pre-commit
pip install pre-commit

# Create .pre-commit-config.yaml
cat > .pre-commit-config.yaml << EOF
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.9
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
EOF

# Install hooks
pre-commit install
```

## CI/CD Status Badges

Add these badges to your README.md:

```markdown
![Tests](https://github.com/yourusername/UniversalContextProtocol/actions/workflows/test.yml/badge.svg)
![Lint](https://github.com/yourusername/UniversalContextProtocol/actions/workflows/lint.yml/badge.svg)
![Coverage](https://codecov.io/gh/yourusername/UniversalContextProtocol/branch/main/graph/badge.svg)
```

Replace `yourusername` with your actual GitHub username.

## Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [PyPI Publishing Guide](https://packaging.python.org/tutorials/packaging-projects/)
- [Docker Hub Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Semantic Versioning](https://semver.org/)

