# Evaluation protocol (Phase 5)

## Research questions
RQ1: Does section-level emotional trajectory planning improve listener-rated
alignment compared with a global-mood baseline?
RQ2: Do targeted MIDI edits preserve unlocked musical content better than
regenerating the entire composition?
RQ3 (exploratory): Does feedback-based personalization improve individual preference?

## Controlled experiments
Use the same model, seed policy, duration, musical inputs and generation budget
across conditions. Condition A = global mood; B = planned trajectory; C = planned
trajectory + selective edit. Randomize blinded playback order and never reveal
generation condition to listeners.

## Required measurements
- Technical validity: tracks, note ranges, duration, event preservation.
- Per-section onset density and velocity distributions (proxies, not mood scores).
- Rendered audio clipping/silence checks.
- Human 1–5 perceived mood match and 1–5 musical coherence.
- Latency and GPU memory reported separately for actual model hardware.

Use held-out situations (at least 20 for pilot), multiple listeners per
condition, anonymized ratings with explicit consent. Calculate confidence
intervals and paired comparisons where the same listener rates conditions.
Avoid generalizing preliminary or unreplicated sample results. Do not claim
a pretrained model improved emotional alignment without a controlled comparison.

## Licensing and ethics
Only use properly licensed or self-produced melodies/data; model weights and
soundfonts are separately licensed. No medical or emotional treatment claims.
