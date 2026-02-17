# API Key Security Review (DJ Blue AI)
Date: February 17, 2026
Last Updated: February 17, 2026 (P0 remediation applied)
Reviewer: Codex (static code review)

## Change Log
- 2026-02-17: Initial review published.
- 2026-02-17: P0 remediation verified (`.env` copy removed from build scripts); findings and remediation plan updated.

## Scope
Reviewed API key handling across:
- Active app path: `ui_ux_team/blue_ui/`
- Shared helpers: `architects/helpers/`
- Build/distribution scripts: `build_binary.py`, `build_nuitka.py`, `build_appimage.py`
- Transcriber modules: `transcribers/`
- Developer docs and onboarding instructions

## Method
- Static repository scan for key usage, storage, propagation, and logging.
- Pattern scan for hardcoded secrets (`AI_STUDIO_API_KEY`, `OPENAI_API_KEY`, common key formats).
- Line-by-line review of key-management and build paths.

## Executive Summary
- No hardcoded API secrets were found in tracked source files.
- Primary key-management path uses OS keyring with `.env` fallback, which is good for developer ergonomics.
- Previous highest-risk issue (build tooling copying `.env` into output folders) is remediated.
- Current top risks are medium severity: broad propagation of key values into process environment variables and permissive fallback behavior in legacy/transcriber modules.

## Findings

### F-01: `.env` copied into build outputs
Severity: High
Status: Resolved on February 17, 2026

Post-fix evidence:
- `build_binary.py:84`
- `build_binary.py:86`
- `build_nuitka.py:52`
- `build_nuitka.py:54`

Why this matters:
- If `.env` contains API keys, build outputs may contain plaintext secrets.
- This increases exposure through artifact sharing, backups, local packaging handoffs, or accidental uploads.

Recommendation:
- Remove automatic `.env` copying from build scripts.
- If absolutely needed for local dev packaging, gate behind explicit opt-in flag (for example, `--include-env`) and print a high-visibility warning.

---

### F-02: Secrets promoted to global `os.environ` and duplicated under compatibility key
Severity: Medium

Evidence:
- `ui_ux_team/blue_ui/app/secure_api_key.py:46`
- `ui_ux_team/blue_ui/app/secure_api_key.py:47`
- `ui_ux_team/blue_ui/app/secure_api_key.py:68`
- `ui_ux_team/blue_ui/app/secure_api_key.py:69`
- `ui_ux_team/blue_ui/settings.py:25`

Why this matters:
- Process environment variables are inherited by child processes by default.
- This broadens key exposure surface (subprocess trees, diagnostics, crash tooling, environment dumps).
- Duplication to both `AI_STUDIO_API_KEY` and `AI_STUDIO` widens accidental-use paths.

Recommendation:
- Prefer in-memory key passing (dependency injection) over writing secrets into global environment variables.
- Keep `AI_STUDIO` compatibility alias temporary and remove once consumers are migrated.
- For subprocess calls, pass sanitized `env` where possible.

---

### F-03: `.env` fallback is loaded implicitly from runtime working context
Severity: Medium

Evidence:
- `ui_ux_team/blue_ui/settings.py:22`
- `ui_ux_team/blue_ui/views/main_window.py:747`
- `README.md:14`
- `README.md:20`

Why this matters:
- Implicit dotenv loading expands trust boundary to filesystem context.
- In environments without keyring, a local `.env` controls runtime key resolution.
- This is acceptable for development but weaker for production/packaged use.

Recommendation:
- For production mode, prefer keyring-only by default.
- If `.env` is retained, resolve from explicit safe path (not ambient cwd lookup).
- Add startup warning when using `.env` fallback so users know key is file-backed.

---

### F-04: Internal exception details surfaced directly in user-visible status strings
Severity: Low

Evidence:
- `ui_ux_team/blue_ui/app/secure_api_key.py:44`
- `ui_ux_team/blue_ui/app/secure_api_key.py:66`
- `ui_ux_team/blue_ui/app/secure_api_key.py:86`
- `ui_ux_team/blue_ui/views/api_settings_window.py:133`

Why this matters:
- Backend exception text may expose local environment details (backend names, system paths, package state).
- Not a direct secret leak, but unnecessary information disclosure.

Recommendation:
- Map exceptions to user-safe messages in UI.
- Log detailed exception text only in debug mode or structured internal logs.

---

### F-05: Legacy transcriber fallback mixes provider key types and uses URL query-param key on Google path
Severity: Low

Evidence:
- `transcribers/ai_studio_transcriber.py:44`
- `transcribers/ai_studio_transcriber.py:78`

Why this matters:
- Fallback chain can select unexpected key type for a given endpoint.
- Query-param API keys can appear in HTTP logs/proxies more easily than header-based auth.
- This module appears auxiliary/legacy but remains present in repo.

Recommendation:
- Separate key variables by provider strictly.
- Validate key/endpoint pairing before request.
- Prefer header-based auth where endpoint supports it.

## Positive Controls Observed
- `.env` is gitignored: `.gitignore:26`
- Keyring-backed storage is implemented in active UI path: `ui_ux_team/blue_ui/app/secure_api_key.py`
- UI masks key display in status text: `ui_ux_team/blue_ui/views/api_settings_window.py:129`
- No hardcoded API key values detected in tracked files during scan.

## Prioritized Remediation Plan

1. P0 (completed on February 17, 2026)
- Removed `.env` copy behavior from `build_binary.py` and `build_nuitka.py`.
- Build scripts now emit an explicit security message instead of copying secrets.

2. P1 (short-term)
- Refactor active key flow to avoid writing secrets into global environment variables except where strictly required.
- Add production-mode switch to disable dotenv fallback.

3. P2 (medium-term)
- Normalize user-facing error messages for keyring operations.
- Harden or retire legacy `transcribers/ai_studio_transcriber.py` fallback behavior.

## Review Limitations
- Static analysis only; no dynamic runtime instrumentation.
- Did not inspect untracked files, local shell history, OS keychain configuration, or git history leaks.
