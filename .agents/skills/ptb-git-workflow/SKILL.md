---
name: ptb-git-workflow
description: Standard git commands, tagging, and release workflow for PokeTokenBar
---

# Git Workflow & Release Tags

This document outlines the standard Git commands and practices used to manage the PokeTokenBar repository, specifically focusing on version bumping, release tagging, and automated version selection.

---

## 1. Commit Standards & Workflow

### A. Semantic Commit Messages with Scopes
Use structured semantic commit messages with explicit subsystem scopes (`<type>(<scope>): <description>`):
- **Types**:
  - `feat`: New user-facing mechanics, subviews, or major systems.
  - `fix`: Bug fixes, state corruption healings, or layout adjustments.
  - `test`: Adding or updating test suites and integration verification.
  - `docs`: Documentation, README, or agent skill updates.
  - `chore`: Maintenance tasks, dependencies, or backward-compatibility cleanup.
- **Common Scopes**:
  - `combat`: Red battle, Rocket battle, Strike Squads, boss retaliation.
  - `nursery`: Egg incubation, nursery subview, paging, egg sorting.
  - `roster`: Companion profile, active companion selection, happiness, living dex.
  - `economy`: Token bank, stocks, term deposits, betting minigames.
  - `expeditions`: Companion dispatches, area rewards, multi-select picker.
  - `skills`: Agent guidelines, architecture, and developer skill files.

*Example:* `feat(nursery): redesign egg handling with interactive nursery subview, pagination, and multi-key sorting`

---

### B. Multi-Commit Atomic Staging Strategy
When committing a body of work containing multiple features or subsystem changes:
1. **Never Default to Blanket `git add .`**: Avoid monolithic commits that lump unrelated subsystems together.
2. **Inspect Unstaged Changes**: Run `git status -s` to analyze modified and untracked files.
3. **Stage Targeted Files Incrementally**:
   ```bash
   git add <subsystem_file_1> <subsystem_file_2>
   ```
4. **Verify Staged Diff Before Committing**:
   ```bash
   git diff --cached --stat
   ```
5. **Commit Incrementally**: Create cohesive, self-contained atomic commits covering one distinct domain at a time (e.g. Combat System ➔ Nursery Subsystem ➔ Battle Encounters ➔ Tests).

---

### C. Pre-Commit Static Compilation Verification
Before creating commits containing Python code, perform a fast static syntax compilation to prevent committing broken syntax or import errors:
```bash
python -m py_compile <modified_python_files>
```
*(Note: Static compilation verifies Python syntax without executing scripts or test suites, fully complying with the `script-execution-policy`.)*

---

### D. Clean Module Deletion Protocol
When deprecating or removing obsolete modules (e.g., removing a legacy modal dialog):
1. Remove or stage the deletion cleanly (`git rm <file>` or `rm <file> && git add <file>`).
2. Ensure all package export points (`__init__.py`), callers in the main loop (`app.py`), and test imports are completely decoupled in the same commit.
3. Verify with `git status` that no dangling untracked remnants or stale `.pyc` files remain.

---

## 2. Release & Version Bumping

**IMPORTANT: Only bump the version strings and perform a release commit when explicitly instructed to do so by the user.**

### Version Control Strategy (SemVer: MAJOR.MINOR.PATCH)
PokeTokenBar strictly adheres to Semantic Versioning (`MAJOR.MINOR.PATCH`):

| Bump Level | Criteria | Examples |
| :--- | :--- | :--- |
| **MAJOR (`X.0.0`)** | Breaking changes, public interface or CLI removals, structural architecture overhauls. | `1.12.0` ➔ `2.0.0` |
| **MINOR (`x.Y.0`)** | Backwards-compatible new features, new tabs, new minigames, substantial subsystem additions. | `2.0.0` ➔ `2.1.0` |
| **PATCH (`x.y.Z`)** | Bug fixes, layout compliance tweaks, formula adjustments, maintenance patches. | `2.0.0` ➔ `2.0.1` |

### Assistant Bumping Protocol: Selection & User Confirmation
**If the user requests a version bump or release without specifying how to bump the version:**
1. **Analyze Developments**: Inspect the staged/unstaged changes and recent git log to determine the scope of changes (breaking changes, new features, or bug fixes).
2. **Select Recommended Bump**: Determine the most appropriate bump type (MAJOR, MINOR, or PATCH) based on SemVer rules.
3. **Confirm with User**: Always propose the recommended version bump and confirm with the user (e.g., using `ask_question` or interactive prompt) before modifying files or creating the release commit.
4. **Execute Release**: Only apply version string updates, commit, and tag once the user confirms or selects their preferred version.

### Step-by-Step Release Process
1. Bump the version strings across all canonical locations:
   - `poketokenbar/__init__.py`: `__version__ = "X.Y.Z"`
   - `setup.py`: `version="X.Y.Z"`
   - `pyproject.toml`: `version = "X.Y.Z"`
   - `README.md`: `[![Version](https://img.shields.io/badge/version-X.Y.Z-blue.svg)]`
2. Stage and commit the changes:
   ```bash
   git add .
   git commit -m "chore(release): bump version to X.Y.Z"
   ```

---

## 3. Working with Git Tags
Git tags are used to mark specific release points in the repository's history. These tags trigger automated package builds and GitHub release notes.

**Creating a new lightweight tag:**
Make sure you are on the release commit, then create the tag:
```bash
git tag vX.Y.Z
```

**Pushing tags to the remote repository:**
By default, `git push` does NOT transfer tags to the remote server. You must push them explicitly:
```bash
# Push commits and all local tags
git push origin main --tags
```
Alternatively, to push a single specific tag:
```bash
git push origin vX.Y.Z
```

**Viewing existing tags:**
```bash
git tag -l
```

**Deleting a mistake tag:**
If you make a mistake and need to remove a tag:
```bash
# Delete locally
git tag -d vX.Y.Z
# Delete remotely
git push origin :refs/tags/vX.Y.Z
```
