# Operations: Build & Release

## Scope
- Build scripts, CI workflow, and release/tag operations.
- Main files:
- `.github/workflows/build.yml`
- `build_binary.py`
- `build_appimage.py`
- `build_nuitka.py`
- `architects/design_docs/TAGGING_GUIDE.md`

## CI Trigger Contract
- GitHub Actions build workflow triggers on:
- tag pushes matching `v*`
- manual dispatch
- Build matrix targets Ubuntu, Windows, and macOS.

## CI Pipeline Behavior
- Sets up Python 3.12 and installs dependencies.
- Validates platform icon availability.
- Runs binary build steps and Linux AppImage packaging on Linux.
- Builds an additional Windows debug console binary (`dj-blue-ai-debug.exe`) with PyInstaller `--console --debug=all`.
- Uploads build artifacts.
- Creates GitHub release for tag refs.

## Local Build Tooling
- `build_binary.py` for PyInstaller one-file GUI binary.
- `build_appimage.py` for Linux AppImage packaging (Linux-focused stage).
- `build_nuitka.py` for standalone Nuitka-based build path.

## Tagging Policy
- Release tagging guidance is documented in `architects/design_docs/TAGGING_GUIDE.md`.
- SemVer-like `v*` tags are treated as release automation entrypoints by CI workflow.

## Commit Workflow Policy
- When asked to create a commit, follow this sequence:

1. Validate changes first
- Run project checks (tests/lint/typecheck) relevant to changed files.
- If checks fail, do not commit. Report failures and stop.

2. Review staged scope only
- Show staged files and summarize staged diff only.
- Do not include unstaged changes in commit message reasoning.

3. Message quality
- Use Conventional Commits (`feat`, `fix`, `refactor`, `docs`, `test`, `chore`).
- Keep the subject line at 72 characters or fewer and use imperative mood.
- Body should cover why, key behavior changes, and risk/migration notes if applicable.

4. Safe commit behavior
- Never amend unless explicitly requested.
- Never commit unrelated files.
- Never use destructive git commands (`reset --hard`, file checkout reverts) unless explicitly requested.

5. Skill routing
- Draft message only: use `staged-commit-message`.
- Commit staged changes: use `elevated-staged-commit`.
- Commit plus tag/release flow: use `git-release-orchestrator`.

6. Pre-commit report before finalizing
- Branch name
- Staged files
- Commit title
- Validation commands run plus pass/fail status

## Security-Relevant Build Notes
- Build/release processes avoid bundling local secret files.
- Runtime secret handling remains keyring/process/env based and outside packaged static config.

## Key Invariants
- Tag format drives automated release behavior.
- CI build outputs are platform-specific and published as release artifacts.
