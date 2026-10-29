# Optional blinded listening study (no data invented)

The evaluation guides require both technical analysis and real listener ratings.
These scripts prepare a blind packet *from the music your app actually generated*.

1. Generate at least two compositions in the app. For a **model comparison**
   include at least two providers and ideally matched prompts/seeds/lengths;
   otherwise this is only a local pilot.
2. Run `python scripts/prepare_listener_study.py --root .wow_workspace --out study_output`.
3. Keep `PRIVATE_stimulus_key.json` out of the participants' view, your Git
   commits and cloud sharing.
4. Ask volunteers who consent to listen to the generated clips and fill
   `ratings_template.csv` (1–5 ratings with anonymous IDs, no personal data).
5. Run `python scripts/analyze_listener_study.py --key study_output/PRIVATE_stimulus_key.json --ratings <genuine-ratings.csv>`.
6. Present the actual count/mean ratings, as a small **descriptive pilot**,
   with known limitations. Never call them "85% emotional accuracy".

The study bundle contains no third-party copyrighted tracks; it uses only
app-generated audio. No evaluations have been performed by these scripts
just by being committed. Do not fabricate participants, statistical
significance or perceptual model-quality claims.
