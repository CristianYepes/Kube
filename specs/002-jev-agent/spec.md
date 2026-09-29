# Spec 002 — Jev plays cub3D_bonus (v0.2)

> WHAT and WHY only. HOW lives in plan.md; facts in ../research-2026-09-28.md (wins on conflict).
>
> **Depends on spec 001 (`../001-game-ready/`).** It starts from the commit where 001 is
> complete, called **the base** below: the tip of `feature/jev-agent`. The implementation
> goes on `feature/jev-agentv1`, created from it. 001 makes player movement frame-rate independent, so
> this spec does not reimplement it.

## Problem & goal

Jev decides but does not act or see. We want to know whether a Jev-driven tactic chooser
can keep a player alive in cub3D_bonus's zombie mode, how it compares with a hand-written
rule policy, and what it costs. The goal is to find out, not to prove that Jev wins: the
TypeSafe blog itself says a non-AI bot could play Doom better.

**Success signal:** a report comparing three policies (idle, scripted rules, Jev) over the
same fixed set of unseen seeds. It gives survival time, waves cleared and win rate, each with
its uncertainty, plus the measured Jev cost and latency per episode.

## Scenarios / user stories

- As the developer, I want to run one episode with a chosen policy, map and seed, from this
  Mac, so that I can watch the logs and iterate.
- As the developer, I want to see why the agent did what it did (the state it sent, the
  tactic chosen and its confidence), so that I can fix the criteria rather than guess.
- As the developer, I want a one-command evaluation that runs every policy on the same seeds,
  so that the comparison is fair and repeatable.
- As a 42 student, I want the deliverable untouched, so that the agent can never cost me an
  evaluation.

## Functional requirements

- **FR1 — Isolation.** The agent MUST live in new files only. Building `cub3D` and
  `cub3D_bonus` MUST produce the same result as on the base, and the deliverable MUST still
  pass norminette.
- **FR2 — Observation.** WHILE an episode runs, the game SHALL publish, every frame, what the
  agent needs to know: player position, heading, health and weapon readiness; wave and game
  state; and for every enemy its position, type, health, AI state and line of sight.
- **FR3 — Control.** The game SHALL accept movement, turning and firing commands from the
  agent without ever waiting for them. No command means keep the last one.
- **FR4 — Fair timing.** Player movement and turning SHALL depend on elapsed time, not on
  frame rate, so that runs compare across maps and machines. **Provided by spec 001 (FR1);**
  the agent build inherits it and only re-checks it.
- **FR5 — Reproducibility.** An episode SHALL be fully defined by map, seed, policy and
  maximum duration. The same seed SHALL spawn the same enemies in the same places.
- **FR6 — Code acts, Jev decides.** Aiming, firing, movement and pathing SHALL be done by code.
  Jev SHALL only choose a tactic from a closed set, given a state written in words. The state
  contains no raw coordinates or angles.
- **FR7 — Use the uncertainty.** WHEN Jev's confidence is below a configured threshold THE
  SYSTEM SHALL keep the current tactic instead of switching.
- **FR8 — Never block the game.** WHILE a Jev request is in flight, the game and the
  controller SHALL keep running on the last tactic. Rate limits, overload and timeouts SHALL be
  retried with backoff and SHALL NOT end the episode.
- **FR9 — Pinned and accountable.** Every Jev call SHALL use a pinned model version and SHALL
  log the model that answered, input tokens, cost, latency and confidence. WHEN the answering
  model differs from the expected one THE SYSTEM SHALL warn.
- **FR10 — Budget.** A run SHALL stop calling Jev when a configured spend cap is reached, and
  SHALL say so.
- **FR11 — Baselines.** The same controller SHALL be drivable by an idle policy and by a
  scripted rule policy, choosing from the same tactic set as Jev.
- **FR12 — Evaluation.** The system SHALL tune only on development seeds, freeze the
  configuration, and measure once on test seeds that were never used for tuning.
- **FR13 — Secrets.** The API key SHALL never be printed, logged, committed, or placed in the
  container or its image.
- **FR14 — Same commands on Linux.** Episodes and the evaluation SHALL run on this Mac, through
  the Linux container, and natively on Linux with the same commands.

## Acceptance criteria (verifiable)

- **AC1 (FR1)** — Building `make` and `make bonus` on this spec's working tree and on the
  base gives identical `obj/*.o` and `obj_bonus/*.o` (sha256).
  `git diff --stat <base> -- . ':(exclude)agent' ':(exclude)sources/agent' ':(exclude)specs'`
  is empty: every change is a new path under those three directories.
  `norminette sources includes libft` exits 0.
- **AC2 (FR2)** — A 10 s headless run prints one observation per frame (>= 40/s on
  `subject_map`). Every line parses as JSON with the documented fields.
- **AC3 (FR3)** — A scripted sequence of commands ("forward 1 s, then turn left 1 s, then
  fire") changes the observed position, heading and weapon state as expected. With no input at
  all, the frame rate matches the no-agent build within 10%.
- **AC4 (FR4)** — Spec 001's movement check, re-run on `cub3D_agent` through the bridge:
  holding "forward" for 2 s moves the player the same distance within 10% on `minimal` and
  `test_map`, although their frame rates differ (74-78 vs 44-56 fps).
- **AC5 (FR5)** — Two runs with the same seed and the idle policy log identical enemy spawn
  positions.
- **AC6 (FR6)** — Every state sent to Jev in a recorded episode is under 2,000 characters and
  contains no floating-point coordinates. Checked by a test over the decision log.
- **AC7 (FR7)** — A unit test: an answer below the threshold leaves the tactic unchanged.
- **AC8 (FR8)** — A unit test with a fake transport: 429, then 529, then success. The request
  is retried, and the controller loop keeps ticking meanwhile. In a real episode, no frame
  gap exceeds 100 ms more often than in the idle policy.
- **AC9 (FR9)** — After a real episode, every decision row has `model`, `input_tokens`,
  `cost`, `latency_ms` and `confidence`. The answering model is `typesafe/jev-1.13-20260917`,
  or a warning was printed.
- **AC10 (FR10)** — A unit test: with a cap of $0.0001, calls stop after the cap and the log
  says why.
- **AC11 (FR11/FR12)** — The evaluation report lists, for each policy on the test seeds:
  n, wins, survival-time median and quartiles, waves cleared, and Jev $/episode and
  latency p50/p95. The config hash printed on the report matches the frozen one.
- **AC12 (FR13)** — `grep` for the key prefix over logs, docs, the image
  (`docker history`, `docker run ... env`) and the working tree returns nothing.
- **AC13 (FR14)** — The same `run` and `eval` commands work with `--runner docker` (Mac) and
  `--runner local` (Linux).

## Out of scope

- Seeing pixels; any vision model.
- Door tactics (closing a door between the player and the zombies). This is a candidate for
  v2 once v1 is measured.
- Changing the 42 deliverable. The defects listed in the research are fixed by spec 001,
  before this one starts.
- Training or fine-tuning (Jev does not allow it).
- Live viewing or video recording (optional task only).
- Publishing, or commits and pushes to the shared repo, without the user's explicit OK.

## [NEEDS CLARIFICATION]

1. ~~Where the code lives~~ **Answered 2026-09-29:** in the `Kube` repo, on
   `feature/jev-agentv1`, branched from `feature/jev-agent` (the base, which carries spec 001).
   The owner will give implementation directions before coding starts.
2. **Evaluation map(s):** `subject_map` by default (bonus-valid, 75-105 fps, under the 64-cell
   flow-field guard). Add `doors_test`?
3. **Episode budget:** default 20 development seeds for tuning, 20 test seeds per policy, a
   180 s cap per episode, and a $1 spend cap for the whole evaluation. OK?
4. **Key:** reuse the `libros` OpenRouter key, or create a dedicated key with its own credit
   limit (recommended)?
