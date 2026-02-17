# API Key Security Review (DJ Blue AI)
Date: February 17, 2026
Last Updated: February 17, 2026 (P0 + keyflow hardening applied)
Reviewer: Codex (static code review)

## Change Log
- 2026-02-17: Initial review published.
- 2026-02-17: P0 remediation verified (`.env` copy removed from build scripts); findings and remediation plan updated.
- 2026-02-17: Active Blue UI keyflow refactored to remove `os.environ` mutation and make `.env` fallback explicit/consent-based.

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
- Active Blue UI path now avoids writing API keys into process environment variables.
- `.env` fallback in active Blue UI path is now explicit (user consent popup + persisted preference).
- Remaining notable risk is mostly in legacy/auxiliary paths (for example `transcribers/` provider fallback behavior).

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
Status: Resolved in active Blue UI path on February 17, 2026

Post-fix evidence:
- `ui_ux_team/blue_ui/app/secure_api_key.py:42` (runtime in-memory cache setter)
- `ui_ux_team/blue_ui/app/secure_api_key.py:90` (keyring save updates runtime cache, not environment)
- `ui_ux_team/blue_ui/settings.py:33` (process env is read-only input path)
- `rg -n "os\\.environ\\[|os\\.environ\\.pop\\(" ui_ux_team/blue_ui -g'*.py'` returns no matches

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
Status: Mitigated in active Blue UI path on February 17, 2026

Post-fix evidence:
- `ui_ux_team/blue_ui/views/main_window.py:759` (explicit consent popup for dotenv fallback)
- `ui_ux_team/blue_ui/views/main_window.py:787` (preference-gated fallback path)
- `ui_ux_team/blue_ui/settings.py:18` (persisted allow/deny fallback preference)
- `ui_ux_team/blue_ui/settings.py:54` (`.env` read is blocked unless explicitly allowed)

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

2. P1 (completed for active Blue UI path on February 17, 2026)
- Refactored active key flow to avoid writing secrets into global environment variables.
- Added explicit `.env` fallback consent popup and persisted allow/deny preference.

3. P2 (medium-term)
- Normalize user-facing error messages for keyring operations.
- Harden or retire legacy `transcribers/ai_studio_transcriber.py` fallback behavior.

## Review Limitations
- Static analysis only; no dynamic runtime instrumentation.
- Did not inspect untracked files, local shell history, OS keychain configuration, or git history leaks.
