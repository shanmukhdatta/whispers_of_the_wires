# Model selection and licensing

| Function | Model or algorithm | Evidence status |
|---|---|---|
| Prompt analysis | Heuristic English emotion segments, optional `j-hartmann/emotion-english-distilroberta-base` | CPU rule path tested; transformer optional/not benchmarked |
| Music blueprint | RuleBasedTrajectoryPlannerV1 | Verified Pydantic section constraints |
| Local composition | RuleBasedComposerV1 (four-role MIDI) | CPU-tested, *not* a pretrained generator |
| Symbolic AI composition | Metacreation MIDI-GPT `yellow_medium` | Kaggle adapter coded; real GPU run pending |
| Preview synthesis | NumPy + soundfile waveform synthesis | CPU baseline, not professional audio |
| Audio export | pretty_midi, FFmpeg optionally | MIDI/WAV available; MP3 requires installed codec |
| Evaluation | note/duration/audio constraints and human ratings | Objective metrics real; human study pending |

Why symbolic MIDI: permits track-level editing and exact preservation tests.
Audio-only models do not guarantee editable note events. MIDI-GPT
`yellow_medium` supports 4/8-bar contexts; the proposed notebook chunks
longer composition plans and must be tested for continuity and instrument roles.

**Copyright and licenses:** The MIDI-GPT *code* is MIT-licensed while published
checkpoint weights have a separate non-commercial research/education license.
See https://github.com/Metacreation-Lab/MIDI-GPT and inspect the checkpoint
terms before usage. Use only authorized source music, SoundFonts and artwork.
The blue dashboard is a layout interpretation, not a copy of album assets.
