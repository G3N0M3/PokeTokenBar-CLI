---
name: ptb-git-workflow
description: Standard git commands, tagging, and release workflow for PokeTokenBar
---

# Git Workflow & Release Tags

This document outlines the standard Git commands and practices used to manage the PokeTokenBar repository, specifically focusing on version bumping and release tagging.

## 1. Standard Commits
Use semantic commit messages when contributing to the codebase:
- `feat: <description>` (for new features)
- `fix: <description>` (for bug fixes)
- `docs: <description>` (for documentation updates)
- `chore: <description>` (for maintenance tasks)

**Example Workflow:**
```bash
git add .
git commit -m "feat: implement token bank system"
git push origin main
```

## 2. Release & Version Bumping
When preparing a new release (e.g., bumping to `1.3.0`), the changes must be committed as a `chore(release)` and the commit must be tagged.

### Step-by-Step Release Process
1. Bump the version strings in:
   - `setup.py`
   - `pyproject.toml`
   - `poketokenbar/__init__.py`
2. Stage and commit the changes:
   ```bash
   git add .
   git commit -m "chore(release): bump version to 1.3.0"
   ```

## 3. Working with Git Tags
Git tags are used to mark specific release points in the repository's history. These tags typically trigger automated build and release pipelines (e.g., GitHub Actions).

**Creating a new lightweight tag:**
Make sure you are on the release commit, then create the tag:
```bash
git tag v1.3.0
```

**Pushing tags to the remote repository:**
By default, `git push` does NOT transfer tags to the remote server. You must push them explicitly:
```bash
# Push commits and all local tags
git push origin main --tags
```
Alternatively, to push a single specific tag:
```bash
git push origin v1.3.0
```

**Viewing existing tags:**
```bash
git tag -l
```

**Deleting a mistake tag:**
If you make a mistake and need to remove a tag:
```bash
# Delete locally
git tag -d v1.3.0
# Delete remotely
git push origin :refs/tags/v1.3.0
```
