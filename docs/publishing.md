# Publishing to PyPI

This document describes how to release and publish the `cora` package to PyPI.

## Prerequisites

- PyPI account (publisher status approved)
- GitHub repository with push access
- GitHub environment named `pypi` created

## Initial Setup

### 1. Create GitHub Environment

1. Go to repository **Settings** → **Environments**
2. Click **New environment**
3. Name it `pypi`
4. (Optional) Add protection rules (e.g., required reviewers)
5. Click **Save protection rules**

### 2. Configure PyPI Trusted Publishing

1. Go to [PyPI Account Settings](https://pypi.org/manage/account/publishing/)
2. Click **Add pending publisher**
3. Fill in:
   - **Name**: `cora-ai`
   - **Owner**: `SiddharthChillale`
   - **Repository**: `cloud-operations-reasoning-agent`
   - **Workflow**: `publish.yml`
   - **Environment name**: `pypi`
4. Click **Add publisher**

### 3. Verify Build Works Locally

```bash
uv build
```

This should create `dist/cora-0.1.0.tar.gz` and `dist/cora-0.1.0-py3-none-any.whl`.

## Publishing a New Version

### Step 1: Update Version

Edit `pyproject.toml` and bump the version:

```toml
[project]
version = "0.2.0"
```

### Step 2: Build and Test

```bash
uv build
```

### Step 3: Commit and Tag

```bash
git add pyproject.toml
git commit -m "Bump version to 0.2.0"
git tag v0.2.0
git push && git push --tags
```

### Step 4: Create GitHub Release

1. Go to **Releases** → **Draft a new release**
2. Select the tag you just pushed (e.g., `v0.2.0`)
3. Add a title and release notes
4. Click **Publish release**

This triggers the `publish.yml` workflow automatically.

### Alternative: Manual Trigger

If you don't want to create a release, you can manually trigger the workflow:

1. Go to **Actions** → **Publish to PyPI**
2. Click **Run workflow** → **Run workflow**

## Troubleshooting

### "Environment not found"

Ensure the `pypi` environment exists in GitHub repo settings.

### "Trusted publishing configuration not found"

Complete step 2 (Configure PyPI Trusted Publishing).

### Build fails

Run `uv build` locally to debug. Common issues:
- Missing `[build-system]` in pyproject.toml
- Missing `[tool.hatch.build.targets.wheel]` packages config
- Missing dependencies in pyproject.toml

## After Publishing

1. Verify the package appears on PyPI: https://pypi.org/project/cora/
2. Test installation: `pip install cora`
3. Test the command: `cora`
