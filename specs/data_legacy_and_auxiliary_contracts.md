# Data: Legacy & Auxiliary Contracts

## Scope
- Data contracts that exist in repository but are not primary Blue UI runtime contracts.
- Main evidence files:
- `architects/song.py`
- `transcribers/the_transcribers.py`
- `mood_readers/data/`
- `ui_ux_team/prototype_r/` (legacy boundary)

## Song Object Contract (Legacy/Peripheral)
- `Song` persists by normalized filepath key into `ManagedMem`.
- Declared required metadata fields:
- `mood_tags`
- `camelot_tags`
- `tempo`
- Enrichment methods (`_get_tags`, `_get_camelot`, `_get_tempo`, `_get_duration`) are placeholders in current implementation.

## Legacy Standalone Transcriber Output Shape
- `transcribers/the_transcribers.py` writes JSON records including:
- `version`
- `timestamp`
- `source_file`
- `duration_sec`
- `language`
- `text`
- `segments`
- `metadata`
- This contract applies to legacy standalone transcriber tooling, not Blue UI runtime transcription manager flow.

## Mood Data Artifacts
- Mood playlist mapping under `mood_readers/data/mood_playlists_organized.json` is actively consumed by Blue UI runtime preflight and mood repository loading.
- Additional mood fixtures and metadata files in `mood_readers/data/` may support tooling and analysis workflows but are not all guaranteed active runtime inputs.

## Prototype/Legacy Boundary
- `ui_ux_team/prototype_r/` is historical and not production startup source.
- Data/model references in prototype scripts should be treated as environment-specific unless proven by active runtime imports.

## Key Invariants
- Legacy/auxiliary contracts may drift independently from Blue UI runtime behavior.
- Production data contracts should be sourced from active runtime modules first, then cross-checked against historical artifacts.
