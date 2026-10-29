# Cloud GPU workflow — Kaggle MIDI-GPT

The application is a local CPU-first Streamlit + FastAPI project. Kaggle acts
as an optional **batch** model executor, not a permanent inference server.

## Prerequisites
- Python 3.11 and `pip install -e ".[dev,studio,cloud]"` locally.
- Your own Kaggle account, signed-in CLI and GPU notebook eligibility.
- Available Kaggle GPU and model download permission; these cannot be guaranteed.
- Do not commit API keys, cookies, dataset secrets, personal files or music assets.

## Option A — private job upload/download through CLI (preferred)

1. In the Streamlit Studio, choose `midigpt` and submit a reviewed blueprint.
   The API stores a private job with state `awaiting_cloud` and prints a UUID.
2. Prepare local files for the private Kaggle kernel:

   `python scripts/kaggle_job.py prepare JOB_ID --username YOUR_KAGGLE_USERNAME`

   The CLI creates `.wow_workspace/kaggle_jobs/JOB_ID/` with a JSON
   blueprint, Python source, generated `run.py` and `kernel-metadata.json`.
   It doesn't contact Kaggle during `prepare`.
3. Upload the prepared kernel:

   `python scripts/kaggle_job.py push JOB_ID`

   Only this action submits files to Kaggle. Inspect `kernel-metadata.json`
   before submitting: it must contain `"is_private": true`.
4. Read the printed kernel reference `username/slug`, then poll:

   `python scripts/kaggle_job.py status username/slug`

5. After successful completion, fetch model outputs:

   `python scripts/kaggle_job.py collect JOB_ID username/slug`

   The importer validates SHA-256, model/provider identity, matching request ID,
   checkpoint, seed, track count and parsable MIDI. It renders a local WAV.
6. In the Studio, select **Refresh job status** and listen/edit/export.

If the free Kaggle environment rejects upload or fails a model load, keep
the job pending and inspect the actual run logs. The local `rule_based`
provider remains usable without Kaggle.

## Option B — manual Kaggle notebook
Clone or upload the branch in a Kaggle notebook, run
`pip install -e .` and `pip install "midigpt[inference]"`, place the exact
saved blueprint at `/kaggle/working/blueprint.json`, and execute
`notebooks/kaggle/batch_generate.py`. Download `job-output/` and place
its files under `.wow_workspace/incoming/YOUR_SAFE_FOLDER/`.
Invoke `POST /api/v1/jobs/{id}/import` with
`{"folder_name":"YOUR_SAFE_FOLDER"}`.

## Limits
- Upstream MIDI-GPT checkpoint: `yellow_medium`, with 4/8-bar contexts.
  The script creates four-bar segments and assembles them for longer plans.
  Continuity between segments is **not guaranteed**.
- The script's control/instrumentation behavior still needs real model validation.
- This is academic-only until checkpoint, music dataset and SoundFont licenses
  are reviewed. Do not advertise unlimited free cloud use.
- No live HTTP endpoint is exposed from Kaggle. The local API must bind to
  127.0.0.1; multiuser authorization isn't implemented.
- Store Kaggle run URL, accelerator, checkpoint revision, duration, manifest,
  generated MIDI and observed errors for acceptance evidence.


## Single-file Kaggle upload integrity

The prepared `run.py` now **embeds** the requested `blueprint.json`, the
MIDI-GPT generation runner, and the `wow` package as UTF-8 source data. It
reconstructs them in `/kaggle/working` before importing or running the model.
This is necessary because the Kaggle `kernel-metadata.json` `code_file`
specifies one uploaded code script, not arbitrary sibling files. Earlier
versions of this bridge could fail with a missing blueprint/import.

The `push` CLI explicitly requests a `NvidiaTeslaT4` accelerator, subject
to the user's Kaggle quota. The script itself is private and uses the public
MIDI-GPT model from its upstream publisher; model weights are covered by a
separate noncommercial research/education license.

### Offline packaging verification (no GPU or account needed)

Prepare a pending job, then execute its generated script in extraction-only
mode to verify that all runtime files can be reconstructed:

```bash
WOW_KAGGLE_WORKING=/tmp/wow-kaggle-test \
  python .wow_workspace/kaggle_jobs/<JOB_UUID>/run.py --extract-only
```

This checks packaging only. It cannot establish actual checkpoint
compatibility, model quality or GPU runtime success.

## Local direct pretrained-model execution (no Kaggle required)

If you have accepted the checkpoint's separate research license, install
`pip install "midigpt[inference]"` and authenticate to Hugging Face as
required for gated weights. Then generate a `midigpt` pending job in the UI
and run:

```bash
python scripts/run_local_model_job.py <PENDING_JOB_UUID>
```

This invokes the **actual** upstream inference engine in a subprocess, imports
the checksum-verified MIDI, and renders the audio locally. There is no silent
rule-based substitute. CPU execution may require substantial memory/time.

**Kaggle secret:** The generated private Kaggle script can read a user-granted
`HF_TOKEN` via Kaggle's `UserSecretsClient`. Accept the license and
explicitly grant the secret in your own Kaggle account if the checkpoint is
gated; neither token nor license consent is embedded in Git.

A CLI path being implemented does **not** constitute a verified model run.
