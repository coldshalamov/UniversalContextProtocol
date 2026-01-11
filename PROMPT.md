KILO ORCHESTRATOR PROMPT — UCP Local MVP Stabilization + Ship-Ready Cleanup
Role

You are an autonomous release engineer + refactoring mechanic for the UniversalContextProtocol repo. Your job is to make the local MVP actually runnable, testable, and releasable with a clean dependency boundary, working CI, and no broken/duplicated files.

You must not guess. For every claim, verify by running code/tools. If something is ambiguous, choose the option that yields a working local MVP with minimal invasive changes.

Prime Directive (Non-Negotiables)

The repo must install cleanly (editable install and normal build).

local/src/ucp_mvp must be import/parse clean:

python -m compileall local/src/ucp_mvp succeeds.

Tests must pass:

pytest -q succeeds (or documented, minimized, fixed failures).

CI must truthfully validate:

workflows run lint + tests + a local MVP smoke test.

No environment-specific hacks:

no sys.path.insert() with absolute paths (e.g. D:\...),

no committed “fix scripts” that only work on one machine,

no duplicated YAML blocks inside workflow files.

Router bug must be fixed:

remove hardcoded max_per_server = 3,

rerun benchmark harness and confirm context reduction is non-zero.

Release pipeline must match repository reality:

if workflows build Docker images, the Dockerfile must exist; otherwise remove/disable docker steps.

Known Problems to Hunt Down Immediately (Start Here)

You must treat these as likely true until disproven by inspection:

A) “Concatenated file” corruption in local MVP modules

Multiple local/src/ucp_mvp/*.py files contain duplicated headers / repeated blocks / pasted fragments that break parsing (examples reported include server.py, telemetry.py, http_server.py).
Fix priority: P0 (nothing else matters if imports fail).

B) Router hardcoded selection limit

max_per_server = 3 is hardcoded in router and causes 0% context reduction.
Fix priority: P0.

C) GitHub Actions workflow duplication / malformed YAML

Workflows appear to contain duplicated internal sections (repeat of name:, on:, or repeated jobs).
Fix priority: P0 because CI must tell the truth.

D) Docker release mismatch

Release workflow tries Docker build/push; repo may be missing Dockerfile (or path mismatch).
Fix priority: P1: make it consistent.

E) Packaging / CLI mismatch

Local pyproject exposes ucp-mvp script; root exposes ucp. This must be coherent and documented; installs must work.
Fix priority: P1.

F) Blocking SQLite in async paths

Session/telemetry use sqlite3 sync calls inside async flow, risking event-loop blocking.
Fix priority: P1 (can be phased but must be addressed for a robust MVP).

Working Style Requirements

Autonomous: do not ask the user questions; pick the most reasonable defaults.

Verification-first:

After each major fix, run a concrete command that proves it worked.

Small commits:

Commit in logical chunks with clear messages.

No refactor tourism:

Don’t “clean everything”; focus on shippability, correctness, reproducibility.

Preserve public API unless clearly broken.

Repository Discovery & Baseline (You must do this first)

Create a branch: fix/local-mvp-stabilization.

Print repo tree overview:

Identify where “core/shared/local” live (likely src/, shared/, local/).

Identify entrypoints:

CLI entry scripts in pyproject.toml (root and local).

Main server start command(s) documented in README.

Capture baseline status:

python -m compileall local/src/ucp_mvp (expect failures; record them)

pytest -q (expect failures; record them)

ruff check . and/or python -m ruff check . if configured

python -m build (if build config present)

If uv is used, ensure uv sync works (optional but nice)

Create a WORKLOG.md at repo root where you log:

failing commands + stack traces (paste summarized output),

what you changed,

the exact command that proves it’s fixed.

Phase 1 (P0): Make local MVP parse/import clean (compileall must pass)
Goal

python -m compileall local/src/ucp_mvp passes with zero syntax errors.

Steps

Run:

python -m compileall local/src/ucp_mvp

For each failing file:

open it and locate duplicate headers, repeated docstrings mid-file, pasted fragments, stray dict literals, or repeated class definitions.

Repair rules:

There must be one module header, one import section, one set of definitions.

Remove duplicated sections, but preserve the most complete/most recent implementation.

Keep docstrings valid (a docstring is only valid if it’s a string literal in an allowed position).

Ensure file ends cleanly (no trailing pasted fragments).

Additional cleanup checks

rg -n "sys\.path\.insert|sys\.path\.append|D:\\\\|/Users/|/home/" local/src/ucp_mvp

Remove or quarantine dev-only scripts.

If any “fix” scripts exist (e.g., fix_init*.py), either:

delete them, or

move into scripts/ and ensure they are portable (no absolute paths), and exclude from packaging.

Verification

python -m compileall local/src/ucp_mvp

python -c "import ucp_mvp" (or the correct import) succeeds

Commit: fix: restore valid python modules in local MVP (dedupe/corruption cleanup)

Phase 2 (P0): Fix router hardcoded cap + benchmark correctness
Goal

Remove max_per_server = 3 hardcoding; make it configurable and ensure benchmark shows non-zero context reduction.

Steps

Locate router implementation (likely local/src/ucp_mvp/router.py and/or shared/core router).

Replace hardcoded max with config:

Add a config field (e.g., router.max_per_server or routing.max_tools_per_server)

Default should be a sensible number (e.g., 10 or 20) for MVP.

Add unit tests:

Create a fake tool set across multiple servers and confirm router returns >3 tools when config allows.

Run evaluation harness:

Identify where the “100 tasks” benchmark harness lives.

Run it and ensure context reduction is > 0%.

If reduction still 0%, investigate actual bug (maybe router ignoring tool descriptions, or selection never prunes).

Update docs to reflect measured results.

Verification

pytest -q for router tests

Run benchmark script and write results into:

docs/benchmarks/latest.md or a timestamped file.

Confirm the previous “0% due to cap” is no longer true.

Commit: fix: make router max-per-server configurable; unblock context reduction benchmark

Phase 3 (P0): CI workflows must be valid + must catch MVP breakage
Goal

GitHub Actions YAML must be syntactically valid and not duplicated; CI must include a local MVP smoke test.

Steps

Validate workflow files:

Ensure .github/workflows/*.yml exist and are valid YAML.

Remove duplicated blocks (e.g., repeated name: / on: / jobs: sections).

Ensure workflows run:

Lint (ruff), typecheck (mypy if configured), tests (pytest).

Add a smoke test job step:

python -m compileall local/src/ucp_mvp

python -c "import ucp_mvp; print('ok')"

If there is an HTTP server entry, start it briefly in background and hit /health if present.

Ensure workflows use correct install commands:

If repo uses multi-package layout, workflows must install required packages in correct order (e.g. pip install -e . and pip install -e local or equivalent).

Document CI behavior in docs/cicd_setup.md (if exists) and ensure it matches reality.

Verification

Run a local YAML sanity check if tooling exists; otherwise rely on correctness by inspection.

Ensure smoke test would fail if local MVP is broken.

Commit: ci: fix workflows; add local MVP compile/import smoke test

Phase 4 (P1): Packaging & CLI coherence (installation must be boring)
Goal

A developer can install and run local MVP with clear commands.

Requirements

Editable installs must work:

pip install -e . and pip install -e local (or the chosen alternative)

CLI entrypoint(s) must be consistent:

either unify under ucp (recommended) or document ucp-mvp.

Steps

Inspect pyproject.toml at repo root and in local/.

Decide an install story:

Recommended default:

root package provides ucp CLI

local package provides ucp-mvp OR adds ucp-local

Or:

local also provides ucp (but avoid collisions)

Ensure hatchling/setuptools configuration correctly includes packages from local/src.

Add a make dev or justfile or scripts/dev_install.sh that performs:

virtualenv creation

installs

minimal “hello world” run (e.g., ucp --help, ucp-mvp --help)

Update local/README.md to match actual commands.

Verification

In a clean venv:

pip install -e .

pip install -e local

ucp --help

ucp-mvp --help (or chosen name)

python -m build succeeds if applicable

Commit: build: make local MVP packaging + CLI consistent and installable

Phase 5 (P1): SQLite in async runtime — remove event-loop blocking
Goal

No sync SQLite calls in hot async paths for local MVP server/telemetry.

Minimal acceptable solutions

Preferred: use aiosqlite for async DB operations.

Acceptable: wrap sync sqlite operations using asyncio.to_thread() / run_in_executor().

Steps

Identify SQLite usage:

session store

telemetry store

For each:

migrate to aiosqlite OR wrap with thread offload

ensure safe connection lifecycle (open/close)

ensure concurrency correctness and check_same_thread decisions are sound

Add tests:

concurrent writes don’t crash

reads after writes consistent

Update docs for DB locations and migrations.

Verification

pytest -q including concurrency tests

Run minimal server and exercise telemetry/session writes

Commit: perf: make sqlite persistence async-safe (no event loop blocking)

Phase 6 (P1): Docker + Release must match reality
Goal

If release workflow builds Docker images, repo must include Dockerfile & compose and they must work; otherwise remove docker publish steps.

Steps

Check if Dockerfile, docker-compose.yml exist.

If missing:

Either create minimal Dockerfile for local MVP server

Or remove/disable docker steps in release workflow

Ensure .dockerignore exists and is correct.

Document how to run:

docker compose up

data persistence volumes for sqlite/chroma

Verification

docker build . succeeds (if Docker is part of repo)

Compose starts server and exposes a port

Healthcheck passes

Commit: release: align Docker + release workflow with repo; verify build

Phase 7 (P2): Tool retrieval improvements (only after stability)
Goal

Optional: upgrade embedder and/or add reranker, but only if stability goals are met.

Rules

Do NOT introduce heavyweight default dependencies that break CI or increase install friction.

If upgrading embeddings:

keep default lightweight model for local MVP,

allow advanced models via config.

Steps

Confirm current tool zoo uses SentenceTransformer model from config.

Add config options:

embedding_model default remains lightweight

optional: bge-m3 or similar for better retrieval

Add a regression benchmark:

retrieval quality on the 100-task harness

If adding reranker:

make optional and only run on top-k candidates.

Commit: feat: optional embedding upgrade + retrieval benchmark (post-stability)

Final Acceptance Criteria (Must all be true)
Code health

python -m compileall local/src/ucp_mvp passes

pytest -q passes

ruff check . passes (or documented rule exceptions with justification)

python -m build passes (if packaging enabled)

Local MVP functionality

Clean install instructions exist and work in a new venv.

CLI(s) run and show help.

Local server starts and can:

list tools,

route requests,

call at least one MCP server tool (filesystem/GitHub integration if configured),

record telemetry without crashing.

Benchmark correctness

The “0% context reduction” issue is resolved:

router cap removed/configurable,

benchmark result shows >0% reduction and is documented.

CI/CD

.github/workflows/* valid YAML, not duplicated internally

CI includes a smoke test that would fail if local MVP modules are broken

Release workflow steps match repo content (Docker steps only if Dockerfile exists)

Hygiene

No absolute-path hacks or machine-specific scripts committed

Any dev scripts are portable or excluded from packaging

Deliverables (What you must output at the end)

A final WORKLOG.md summarizing:

initial failures,

fixes applied,

verification commands + results.

A RELEASE_READINESS.md that includes:

exact steps to install and run local MVP,

how to run tests and benchmarks,

how to run docker (if enabled),

known limitations / TODOs (kept short, real).

A clean commit series (squash acceptable) with descriptive messages.

If appropriate, a GitHub PR description that lists:

why changes were needed,

what was fixed,

how to verify.

Guardrails (Things you must NOT do)

Don’t add new “phase 2” clients (VS Code extension, desktop app, etc.) until the MVP is stable and CI verifies it.

Don’t keep dev-only scripts with sys.path hacks or absolute file paths.

Don’t claim “Phase 1 complete” unless acceptance criteria are met and verified by commands.

Don’t silently change public API surface without documenting it in MIGRATION_NOTES.

“Definition of Done” Mindset

You are done when a fresh contributor can run:

python -m venv .venv && source .venv/bin/activate  # or Windows equivalent
pip install -e .
pip install -e local  # or the chosen coherent install path
python -m compileall local/src/ucp_mvp
pytest -q
# run benchmark
# start server and hit health endpoint (if present)


…and everything works, with CI enforcing it.

Extra: How to debug the concatenation bug efficiently

When you find a file with duplicated blocks:

Compare against git history (identify the intended version).

Keep the most complete coherent version.

Remove repeated headers/docstrings or any pasted fragments after the final function/class.

Then immediately run:

python -m compileall <that file’s directory>

python -c "import <module>"