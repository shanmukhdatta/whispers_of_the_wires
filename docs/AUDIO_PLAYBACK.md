# Audio playback controls — implementation notes

The local music dashboard now provides non-destructive preview volume
(0–200%), low-pass brightness filtering, and equal-power crossfaded playlist
rendering (0–8 seconds between adjacent user-generated tracks). All saved
compositions and original MIDI remain unchanged.

API contracts:
- `GET /api/v1/compositions/{id}/listen?version=1&volume_percent=80&lowpass_hz=1200`
- `GET /api/v1/playlists/{playlist_id}/listen?fade_seconds=1.5`

The playlist renderer allows up to eight local tracks and a four-minute maximum
mix. It operates synchronously and is **not live streaming**, a DAW mixer, or a
multiuser service. Equal-power crossfade occurs during file rendering.
Advanced mixing/mastering, live EQ automation, spatial audio, and remote
collaboration from the six-week plan remain out of scope for the CPU MVP.
