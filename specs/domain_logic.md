# Domain Logic

This file is now the domain behavior index. Detailed contracts are split into focused specs:

- [Domain: Transcription & Chat](domain_transcription_and_chat.md)
- [Domain: Playback & Start Cycle](domain_playback_and_startup_cycle.md)
- [Domain: API Usage Limits](domain_api_usage_limits.md)

## Scope Split Rationale
- Transcription/chat behavior has separate state machines, payload contracts, and API interactions.
- Playback/startup gating is mostly UI/runtime orchestration logic.
- API usage guardrails are a distinct policy layer with persistence semantics.

## High-Level Invariants
- Active runtime behavior must be taken from `ui_ux_team/blue_ui/` and imported helpers.
- Prototype and legacy modules are historical unless active imports prove runtime usage.
- Domain rules should remain grounded in implementation modules, not historical design docs.
