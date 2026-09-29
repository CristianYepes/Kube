# Tasks 002 — Jev plays cub3D_bonus

> Build order. 🔑 = needs the user. Each task is closed by a check, not a vibe.
> **Starts only when spec 001 (game-ready) is complete**: its last commit is "the base".
> Nothing is committed or pushed until T0 is answered.

- [ ] 🔑 **T0** — Answer the spec's four NEEDS CLARIFICATION items: where the code lives,
  evaluation map, episode budget, which key.
  **Done when:** the answers are written into `spec.md` (v0.2) and the working branch exists
  locally.
- [ ] **T1** — Reuse spec 001's dev container (`dev/`). Add a tool only if a task below
  needs it.
  **Done when:** `dev/dev.sh build` builds the base in the container, and the 001 test suite
  is green there.
- [ ] **T2** — Isolation guard: `agent/check_isolation.sh` builds the base and the working tree
  in the container and compares the sha256 of `obj/*.o` and `obj_bonus/*.o`. It also runs the
  AC1 `git diff` and `norminette sources includes libft`.
  **Done when:** it passes on the untouched tree, and fails when a deliberate one-character
  edit is made to `sources/render/raycasting.c`. That second run proves the guard can fail.
- [ ] **T3** — C bridge: `agent/Makefile` (reusing the MiniLibX pinned by spec 001),
  `sources/agent/{agent.h,agent_main.c,agent_loop.c,agent_frame.c,agent_io.c}`
  implementing the two contracts in `plan.md`.
  **Done when:**
  - AC2: >= 40 obs/s on `subject_map`, every line valid JSON;
  - AC3: scripted `C` lines move, turn and fire as expected;
  - AC4: spec 001's movement check still holds through the bridge;
  - AC5: the same seed gives the same spawns;
  - `norminette sources/agent` exits 0;
  - T2 still passes.
- [ ] **T4** — Python package skeleton (`agent/pyproject.toml`, uv) with `bridge.py` (process
  plus line I/O, `--runner docker|local`) and `features.py` (obs -> semantic state).
  **Done when:** pytest passes on fixtures recorded from T3, and AC6 holds: states are under
  2,000 characters with no floats.
- [ ] **T5** — Controller and baselines: `controller.py` (aim, fire, and the four movements;
  BFS over the `init` map), `policies.py` (idle, scripted) and `run.py` (one episode ->
  `agent/runs/<id>/`).
  **Done when:**
  - `run --policy idle --seed 1` and `run --policy scripted --seed 1` both finish with a
    `result.json`;
  - over development seeds 1-5, the scripted median survival is longer than idle's (first
    real baseline numbers).
- [ ] **T6** — Jev client adapted from `~/jev/libros/src/libros/jev.py`: pinned model;
  expected-model warning; `request_id` read from the header; `usage.cost`; retries with a
  1.5 s attempt timeout; budget cap; the `decisions.jsonl` row.
  **Done when:** AC7, AC8 (fake transport) and AC10 pass as unit tests.
- [ ] 🔑 **T6b** — The key available on the Mac host as `OPENROUTER_API_KEY` (the user
  chooses which key, T0).
  **Done when:** one real call returns, logged per AC9, and **Jev latency p50/p95 over 50
  calls** is recorded in the research (the unknown in R2). If p95 > 500 ms, apply the
  event-only mitigation from the plan before T7.
- [ ] **T7** — Jev policy: asynchronous decisions, confidence gate, at most one request in
  flight, fallback to the scripted rules on budget stop.
  **Done when:** a 60 s episode on seed 1 completes with decisions logged, and AC8's frame-gap
  check passes against idle.
- [ ] **T8** — Tuning on development seeds 1-20 only: the criteria text, θ, and the
  decision cadence. Then freeze: write the config sha256 into `agent/frozen.json`.
  **Done when:** the frozen file exists, and the tuning notes (what changed, which dev
  numbers) are appended to the research as R8.
- [ ] **T9** — Final evaluation: `eval --seeds 101-120 --policies idle,scripted,jev` ->
  `agent/runs/eval-<date>/report.md`.
  **Done when:** AC11 holds (per-policy n, wins with Wilson CI, survival median/IQR, waves,
  and Jev cost/latency), the report's config hash equals the frozen one, and AC12 (no key
  anywhere) passes.
- [ ] **T10** — x86_64 check: AC1 and one smoke episode on native x86_64 Linux (campus), or in
  Colima with `--arch x86_64`, which is not verified yet.
  **Done when:** both pass on x86_64.
- [ ] **T11** — (optional) Watch or record: `ffmpeg -f x11grab` in the container to an mp4, or
  `x11vnc` plus macOS Screen Sharing. Neither is verified yet.
  **Done when:** one episode is viewable from the Mac.
- [ ] 🔑 **T12** — Decide what gets committed where, and whether to tell Rodrigo.
  **Done when:** the user says so. Only then commit, with no push unless asked.
