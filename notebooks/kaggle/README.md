# Kaggle: MIDI-GPT smoke-test adapter

The cloud notebook is **not** a permanent server. Attach an available Kaggle GPU and
enable network access if your Kaggle settings permit it.

1. Install the MIDI-GPT inference package using the project's published instructions.
2. Load checkpoint `yellow_medium` (code snippet in `smoke_test.py`).
3. Generate only four bars initially; print CUDA availability, allocated device and elapsed time.
4. Save MIDI, environment notes and a checksummed manifest in `/kaggle/working/job-output/`.
5. After the notebook completes, download its output archive using the Kaggle UI/CLI.
6. Import locally after checksum checks, never by trusting remote paths.
7. Do not store Kaggle API credentials in Git. GPU usage and generation are **unverified** until your run succeeds.

Check the upstream MIDI-GPT inference API against its current release before running;
the notebook is an integration starting point, not an assertion that model download succeeded.
