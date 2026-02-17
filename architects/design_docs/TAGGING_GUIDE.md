# Git Tagging & Versioning Design Document

## 1. Overview
This document defines the standard procedure for marking release points in the repository using Git tags. Proper tagging ensures that specific versions of the software can be identified, audited, and redeployed reliably.

## 2. Tagging Standards
We follow **Semantic Versioning (SemVer)** for all release tags.

**Format:** `v<Major>.<Minor>.<Patch>-<Pre-release>`
*   **Major:** Incompatible API changes.
*   **Minor:** Added functionality in a backwards-compatible manner.
*   **Patch:** Backwards-compatible bug fixes.
*   **Pre-release:** (Optional) Alpha, beta, or release candidate (e.g., `v0.2.11-alpha`).

---

## 3. Tag Types

| Tag Type | Usage | Command |
| :--- | :--- | :--- |
| **Annotated** | **Official Releases.** Stores author, date, and message. | `git tag -a v1.0.0 -m "message"` |
| **Lightweight** | **Internal Bookmarks.** Simple pointers to commits. | `git tag v1.0.0-lw` |

> **Policy:** All production and staging releases **must** use Annotated tags.

---

## 4. Operational Workflow

### 4.1 Creating a New Release
When the code is ready for a release (e.g., `v0.2.11-alpha`):

1. **Ensure you are on the correct branch:**
   ```bash
   git switch main
   git pull origin main
   ```

2. **Create the annotated tag:**
   ```bash
   git tag -a v0.2.11-alpha -m "Release version 0.2.11-alpha"
   ```

3. **Push the tag to the remote server:**
   ```bash
   git push origin v0.2.11-alpha
   ```

### 4.2 Reviewing Tags
To verify local and remote tags:

*   **List all tags:** `git tag`
*   **Show tag details:** `git show v0.2.11-alpha`
*   **Verify remote tags:** `git ls-remote --tags origin`

### 4.3 Correcting Errors
If a tag was created on the wrong commit or has a typo:

1. **Delete locally:** `git tag -d v0.2.11-alpha`
2. **Delete remotely:** `git push origin --delete v0.2.11-alpha`
3. **Re-tag** using the correct commit hash: `git tag -a v0.2.11-alpha <commit-hash> -m "Corrected release"`

---

## 5. Automation & CI/CD
*   **Triggering Builds:** Pushing a tag matching the pattern `v*` triggers the automated build/deployment pipeline.
*   **Changelogs:** The messages attached to annotated tags (`-m`) serve as the source of truth for automated changelog generation.

---

## 6. Quick Command Cheat Sheet
```bash
# List tags in creation order
git tag --sort=creatordate

# Tag a specific past commit
git tag -a v0.1.0 <commit-sha> -m "Backdated tag"

# Push all local tags to origin
git push origin --tags

# Checkout the code at a specific tag
git checkout tags/v0.2.11-alpha -b branch-name
```