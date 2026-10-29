"""Opt-in Kaggle CLI integration; no background service, credentials or uploads in CI.

Kaggle CLI must be installed and authenticated on the developer's machine.
Preparing jobs never transmits anything. Pushing transmits a *private* kernel and
the requested blueprint only after the operator explicitly runs `push`.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path
from uuid import UUID

from wow.artifacts import verify_manifest
from wow.generation import GenerationService

_NAME = re.compile(r"^[a-zA-Z0-9_-]{2,64}$")


def _identity(value: str, what: str) -> str:
    if not _NAME.fullmatch(value):
        raise ValueError(f"Invalid {what}; only letters, numbers, _ and - are allowed")
    return value


def _job_id(value: str) -> str:
    if str(UUID(value)) != value:
        raise ValueError("Invalid job ID")
    return value


def _run_cli(*args: str) -> str:
    try:
        done = subprocess.run(
            ["kaggle", "kernels", *args],
            check=True, capture_output=True, text=True, timeout=180,
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(
            "Kaggle CLI command failed. Verify installation, credentials, account limits "
            "and notebook status; see docs/CLOUD_WORKFLOW.md"
        ) from exc
    return done.stdout.strip()


def prepare(root: Path, job_id: str, username: str, slug: str = "wow-music") -> Path:
    """Create a private, reproducible Kaggle code bundle for a pending job."""
    job_id = _job_id(job_id)
    username = _identity(username, "Kaggle username")
    slug = _identity(slug, "kernel slug")[:38] + "-" + job_id[:8]
    service = GenerationService(root)
    record = service.jobs.get(job_id)
    if not record or record["provider"] != "midigpt" or record["state"] != "awaiting_cloud":
        raise ValueError("Only pending MIDI-GPT jobs can be prepared")
    source = service.root / "artifacts" / job_id / "blueprint.json"
    if not source.is_file():
        raise FileNotFoundError("Saved blueprint was not found")
    # Parse and reject non-MIDI-GPT blueprints even when the SQLite record is inconsistent.
    from wow.contracts import MusicBlueprint

    bp = MusicBlueprint.model_validate_json(source.read_text(encoding="utf-8"))
    if bp.generation.provider != "midigpt" or bp.generation.checkpoint != "yellow_medium":
        raise ValueError("Unsupported Kaggle blueprint provider/checkpoint")
    # Resolve repository from the installed source package, not cwd.
    repo = Path(__file__).resolve().parents[2]
    runner = repo / "notebooks" / "kaggle" / "batch_generate.py"
    if not runner.is_file():
        raise FileNotFoundError("Kaggle batch runner missing from source checkout")
    target = service.root / "kaggle_jobs" / job_id
    if target.exists():
        raise FileExistsError(
            "A prepared Kaggle bundle already exists; inspect or remove it before rebuilding"
        )
    target.mkdir(parents=True)
    shutil.copyfile(source, target / "blueprint.json")
    shutil.copyfile(runner, target / "batch_generate.py")
    package_dir = target / "src" / "wow"
    package_dir.mkdir(parents=True)
    for module in sorted((repo / "src" / "wow").glob("*.py")):
        shutil.copyfile(module, package_dir / module.name)
    # Kaggle's CLI uploads the designated code file, not arbitrary sibling
    # source files. Embed an auditable UTF-8 copy of all runtime code and the
    # request into that one code file; keep the originals beside it for review.
    payload: dict[str, str] = {
        "blueprint.json": (target / "blueprint.json").read_text(encoding="utf-8"),
        "batch_generate.py": (target / "batch_generate.py").read_text(encoding="utf-8"),
    }
    for module in sorted(package_dir.glob("*.py")):
        payload["src/wow/" + module.name] = module.read_text(encoding="utf-8")
    # JSON encoded twice gives a safe Python string literal. The script can
    # reconstruct its resources on an isolated Kaggle worker without extra
    # data-source attachments, external GitHub cloning, or credentials.
    quoted_json = json.dumps(json.dumps(payload, ensure_ascii=True))
    bootstrap = (
        '"""Private single-file Kaggle MIDI-GPT job. Embedded files are local code."""\n'
        "import json\nimport os\nimport subprocess\nimport sys\n"
        "from pathlib import Path\n"
        "work = Path(os.environ.get('WOW_KAGGLE_WORKING', '/kaggle/working'))\n"
        "work.mkdir(parents=True, exist_ok=True)\n"
        f"payload = json.loads({quoted_json})\n"
        "for rel, body in payload.items():\n"
        "    dest = work / rel\n"
        "    dest.parent.mkdir(parents=True, exist_ok=True)\n"
        "    dest.write_text(body, encoding='utf-8')\n"
        "print('Restored isolated music job:', len(payload), 'source/input files')\n"
        "if '--extract-only' in sys.argv:\n"
        "    sys.exit(0)\n"
        "sys.path.insert(0, str(work / 'src'))\n"
        "sys.path.insert(0, str(work))\n"
        "subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-q', "
        "'midigpt[inference]', 'pretty_midi>=0.2.10,<1', 'pydantic>=2.8,<3'])\n"
        "from batch_generate import main\n"
        "main()\n"
    )
    (target / "run.py").write_text(bootstrap, encoding="utf-8")
    metadata = {
        "id": f"{username}/{slug}", "title": f"Whispers {job_id[:8]}",
        "code_file": "run.py", "language": "python", "kernel_type": "script",
        "is_private": True, "enable_gpu": True, "enable_internet": True,
        "dataset_sources": [], "competition_sources": [], "kernel_sources": [],
    }
    (target / "kernel-metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )
    return target


def push(bundle: Path) -> str:
    """Upload the private kernel to the account configured in Kaggle CLI."""
    bundle = Path(bundle).resolve()
    metadata = json.loads((bundle / "kernel-metadata.json").read_text(encoding="utf-8"))
    if metadata.get("is_private") is not True:
        raise ValueError("Refusing to push nonprivate kernel")
    _run_cli("push", "-p", str(bundle), "--accelerator", "NvidiaTeslaT4")
    return str(metadata["id"])


def status(kernel_ref: str) -> str:
    _validate_ref(kernel_ref)
    return _run_cli("status", kernel_ref)


def _validate_ref(kernel_ref: str) -> None:
    parts = kernel_ref.split("/")
    if len(parts) != 2:
        raise ValueError("Expected Kaggle owner/slug")
    for part in parts:
        _identity(part, "kernel reference")


def collect(root: Path, job_id: str, kernel_ref: str) -> dict:
    """Download outputs and validate/import them only after a completed run."""
    _validate_ref(kernel_ref)
    job_id = _job_id(job_id)
    service = GenerationService(root)
    job = service.jobs.get(job_id)
    if not job or job["provider"] != "midigpt" or job["state"] != "awaiting_cloud":
        raise ValueError("Job is not waiting for cloud output")
    folder = f"cloud_{job_id[:8]}"
    raw = service.root / "kaggle_jobs" / job_id / "download"
    raw.mkdir(parents=True, exist_ok=True)
    # Kaggle downloads kernel-output files; it does not guarantee subdirectory shape.
    _run_cli("output", kernel_ref, "-p", str(raw))
    matches = list(raw.rglob("manifest.json"))
    if len(matches) != 1:
        raise ValueError("Expected exactly one job-output/manifest.json from Kaggle")
    verified = verify_manifest(matches[0].parent)
    if verified.get("request_id") != job["request_id"]:
        raise ValueError("Downloaded manifest belongs to a different request")
    target = service.root / "incoming" / folder
    target.mkdir(parents=True, exist_ok=True)
    for name in ["manifest.json", *verified["outputs"]]:
        shutil.copyfile(matches[0].parent / name, target / name)
    return service.import_kaggle(job_id, folder)
