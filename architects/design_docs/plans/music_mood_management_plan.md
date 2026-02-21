# Music Mood Management Plan (Dynamic Replacement for Static Playlist JSON)

- **Last Updated: 2026-02-18**

## Objective
Replace static mood mapping from `mood_readers/data/mood_playlists_organized.json` with a dynamic, inspectable, and self-improving music selection system.

Primary outcomes:
- higher match quality between detected mood and selected tracks
- less repetition and better session flow
- deterministic fallback behavior when metadata is incomplete

## Current Problem
The current model is static lookup:
1. mood label -> list of tracks
2. random selection from that list

Limitations:
- no ranking (all tracks are treated as equally good)
- no context memory (repeats can happen quickly)
- no adaptation to user feedback or skip behavior
- manual JSON maintenance does not scale
- weak guarantees that actual music library matches mapping

## Design Principles
1. Keep runtime deterministic and debuggable.
2. Prefer local/offline ranking first, optional remote intelligence second.
3. Never block playback on advanced scoring failures.
4. Preserve a strict fallback chain so app behavior is predictable.

## Target Architecture
Create a new service layer:
- `architects/helpers/music_mood_manager.py` (new)

Core collaborators:
- `mood_readers` for extracted audio features (BPM, key/Camelot, mood hints)
- `ManagedMem` for lightweight persistence of play history and feedback
- `MainUI` / player flow for runtime requests and transport events

Data sources:
- `music_collection/` (runtime folder)
- track metadata cache (generated index file)
- session context (recent mood sequence, recently played tracks)
- optional user feedback (skip/like/dislike)

## Proposed Data Model
Use two persistent files (runtime-adjacent):
1. `config/music_index.json`
- one entry per track
- fields:
  - `track_id` (stable hash of normalized path)
  - `path`
  - `duration`
  - `bpm`
  - `camelot`
  - `energy`
  - `valence`
  - `mood_scores` (map mood -> 0..1)
  - `last_indexed_at`

2. `config/music_feedback.json`
- aggregated interaction signals:
  - `play_count`
  - `skip_count`
  - `like_count`
  - `last_played_at`
  - `cooldown_until`

## Selection Strategy
For a target mood, candidate score is weighted:
- `MoodFit`: closeness of track mood profile to target mood
- `TransitionFit`: compatibility with previous mood/track (tempo/key continuity)
- `Novelty`: anti-repeat bonus for not recently played tracks
- `Feedback`: penalty for frequent skips, bonus for likes

Example scoring:
`score = 0.50*MoodFit + 0.20*TransitionFit + 0.20*Novelty + 0.10*Feedback`

Selection policy:
1. filter by hard constraints (file exists, supported extension, not in cooldown)
2. compute score for each candidate
3. sample from top-K with weighted randomness (reduces deterministic looping)

## Runtime Flow
1. Mood event arrives from transcription/emotion pipeline.
2. Manager loads current index + feedback.
3. Manager returns best candidate track path + explanation payload.
4. Player starts track.
5. Transport events update feedback:
- normal finish -> positive stability signal
- early skip -> skip penalty
- explicit like/dislike (future UI) -> direct feedback update

## Compatibility and Fallback Chain
Fallback chain must always produce behavior:
1. dynamic manager ranked selection
2. mood-filtered unranked selection from index
3. first playable track in `music_collection/`
4. explicit warning + no autoplay

If index missing/stale:
- run lazy reindex in background
- continue with lightweight filename-based fallback

## Reindexing Strategy
Trigger conditions:
- first launch
- file count/hash change in `music_collection`
- manual reindex from settings (future button)

Mode:
- incremental (only new/modified files)
- non-blocking thread worker
- partial results usable immediately

## UI/UX Changes (Planned)
1. Settings tab: `Music Mood Engine`
- index status
- last reindex timestamp
- missing/invalid tracks count
- reindex button

2. Optional explainability surface:
- show why a track was selected:
  - mood fit
  - novelty
  - transition compatibility

## Migration Plan
Phase 1: Introduce manager in shadow mode
- keep current JSON flow active
- compute dynamic recommendation in parallel and log comparison

Phase 2: Hybrid mode
- dynamic manager primary
- static JSON as fallback

Phase 3: Dynamic primary
- static JSON removed from runtime decision path
- keep optional export tool for compatibility

Phase 4: Feedback loop
- persist skip/finish signals
- adjust ranking over time

## Validation and Metrics
Track per session:
- repeat rate within N tracks
- average skip time
- mood-transition stability score
- selection latency (ms)
- fallback-hit rate

Success criteria:
- reduced short-window repetition
- lower skip rate
- stable selection latency under target (e.g. < 50ms after warm cache)

## Risks and Mitigations
1. Bad metadata -> poor rankings
- mitigation: confidence flags + conservative fallback

2. Large libraries -> indexing delay
- mitigation: incremental indexing + background worker + cache

3. Overfitting to sparse feedback
- mitigation: cap feedback influence and use decay windows

## Implementation Checklist
1. Add `music_mood_manager.py` with ranking API.
2. Add index builder and persistence helpers.
3. Integrate manager into `MainUI` mood-to-track selection path.
4. Wire transport events for skip/finish feedback updates.
5. Add settings diagnostics panel.
6. Add test coverage for scoring and fallback behavior.
