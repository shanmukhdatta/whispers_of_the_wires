# Kaggle batch inference: request → generated MIDI → imported WAV

The local API does not assume a permanently available Kaggle endpoint.
Free notebook availability, accelerator type and download limits are external.

## 1. Create request locally
Create a blueprint with POST /api/v1/blueprints, set:
`generation.provider="midigpt"`, `generation.checkpoint="yellow_medium"`,
then submit that blueprint to POST /api/v1/jobs.
Response is `state=awaiting_cloud` and a job_id.
The server stores the exact blueprint at:
`WOW_DATA_DIR/artifacts/<job_id>/blueprint.json`.

## 2. Run Kaggle model
On a Kaggle GPU notebook with internet access enabled where permitted:
- Clone/download this repository's accepted branch.
- Install `pip install -e .` and `pip install "midigpt[inference]"`.
- Copy the exact saved blueprint as `/kaggle/working/blueprint.json`.
- Execute `python notebooks/kaggle/batch_generate.py`.
- Inspect logs for CUDA, GPU device, performance and actual generated MIDI.
- Download `job-output/` including the SHA256 manifest.

**Important**: This notebook is an integration candidate and has not been executed
on the user's Kaggle account. MIDI-GPT may change score/track/token behavior;
do not mark this step complete until a real model run succeeds. Outputs must
not be mislabeled when fallback synthesis or other checkpoints are used.

## 3. Import locally
Extract the downloaded `job-output` files to
`WOW_DATA_DIR/incoming/myrun/` on the local machine.
POST /api/v1/jobs/<job_id>/import with `{"folder_name":"myrun"}`.
The importer checks SHA256, requested model, request_id, MIDI validity,
then synthesizes and stores WAV under the job ID.
Verify results using GET /api/v1/compositions/<job_id>.

## Security and cost
Use 127.0.0.1 for local API. Do not expose API routes to the internet;
this MVP does not implement multiuser authorization. Never commit Kaggle
credentials. Job state is durable and manual failures should be documented.
