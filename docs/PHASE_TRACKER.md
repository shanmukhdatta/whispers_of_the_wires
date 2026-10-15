# Phase tracker (engineering code / acceptance separated)

| Phase | Branch | Code pushed | CPU CI at final review | User acceptance |
|---|---|---|---|---|
| 1 Foundation | phase-01-foundation | Yes | See GitHub Actions | Pending |
| 2 Emotion & planning | phase-02-emotion | Yes | See GitHub Actions | Pending |
| 3 Generation & rendering | phase-03-generation | Yes | See GitHub Actions | Pending |
| 4 Studio & editing | phase-04-studio | Yes | See GitHub Actions | Pending |
| 5 Evaluation | phase-05-evaluation | Yes | See GitHub Actions | Pending |
| 6 Hardening/cloud adapter | phase-06-hardening | Yes | See GitHub Actions | Pending |

**Important:** Code pushed is not equal to Kaggle-tested, accepted, merged or production-ready.
PRs are stacked: Phase 2 depends on 1, Phase 3 on 2, etc. The owner reviews and
merges only after local/Kaggle verification. `original` is the design baseline;
`main` is preserved.

## Current implementation caveats
Later branches implement the complete CPU-first baseline feature set and
a testable cloud-job adapter, not verified neural GPU generation.
Use `all-phases-complete` for an integrated code snapshot; PR #1–6 remain
separate, stacked review points. No phase was merged to `main`.

CI is expected to cover dependency checks, syntax compilation, unit tests,
CPU end-to-end smoke and Ruff. Manual Studio/browser and Kaggle GPU acceptance
must still be recorded by the repository owner.
