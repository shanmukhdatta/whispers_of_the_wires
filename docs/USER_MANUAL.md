# Whispers of the Wires — User manual and FAQ

## Setup
Use Python 3.11. Check out `mentor-readiness-dashboard`; install
`pip install -e ".[dev,studio]"`; launch with `python run_studio.py`.
Only the local loopback API is supported; no account or payment is required.

## Compose tab
1. Choose one of the situation templates or type an English mood/context story.
2. Choose tempo, bar count, key, genre and lead General MIDI program.
3. Optionally choose activity, weather scenario or time of day. These are
   **your stated scenario**, not live location/weather observations.
4. Click **Analyze and create plan**. Check mood stages, including valence,
   arousal and dominance values; edit before generation.
5. Select `rule_based` for the immediately usable four-track local baseline.
   `midigpt` generates a pending Kaggle batch job, not live streamed music.
6. Click generate and inspect the resulting MIDI/WAV player and waveform.
7. Use the metrics and spectral features panes for descriptive music properties.
   Pitch distribution, MFCC, centroid and rolloff **do not measure happiness**.

## Change and export
- Create a variation: change seed. Extend the final section by additional bars.
- Select a track and a zero-based half-open bar range to change locally.
- Export the current version as MIDI, WAV, or full ZIP.
- MP3 requires an installed FFmpeg binary on the system PATH.
- Earlier versions are preserved under the job's version history.

## My Albums & Library
- View previously completed compositions saved locally.
- Mark favorites and create playlists of your own generated music.
- Choose a saved composition to reopen its editing session.
- The dashboard is not a public streaming catalog. No third-party albums
  are included.

## Insights
- Review counts and descriptive ratings.
- Real listener ratings can be entered voluntarily after hearing the audio.
- No mood-alignment percentage is inferred from note velocity or MFCC scores.

## FAQ
**Why does my output sound electronic?**
The basic CPU renderer uses simple synthesized tones, not professional sampled
instruments. MIDI can be played in a separate DAW/synthesizer.

**Why is cloud generation pending?**
The Kaggle model is a batch job. Follow `docs/CLOUD_WORKFLOW.md`; GPU
availability and notebook permissions depend on your own Kaggle account.

**How do I change the generated notes?**
Use the bar/track editor, which creates a new version and preserves other notes.

**Why does an empty playlist have no music?**
Generate a composition, then add it through My Albums & Library.

**Where are my compositions?**
The default workspace `.wow_workspace/` stores SQLite and music artifacts.
Treat it as private local data, back it up before moving machines.

**Can I use generated tracks commercially?**
Do not assume so. Check pretrained checkpoint licenses and any third-party
sounds before use. Music generated with noncommercial model weights cannot
automatically be marketed as commercially licensed.

**Does it support voice, haptic, real-time EQ or social sharing?**
No. These are optional/extended ideas in the PDFs, not verified features.
