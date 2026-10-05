# Spec 002 — Jev plays cub3D_bonus (v0.5)

> v0.5 (2026-10-05): the owner's decisions 5-8 (see "Decisions") add FR15, AC14, the Linux
> checkpoints and the `sources/jev/` name. See "Changes since v0.5" in `tasks.md`.
> v0.4 (2026-10-05): FR5, AC1, AC4, AC5, AC8 and AC12 corrected after checking them against
> the code; see "Changes since v0.4" in `tasks.md`.

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
- As the developer, I want every episode's decisions and the player's path kept in the repo,
  so that I can look for the ways the game gets beaten, and later make it harder where a
  pattern shows (for example with obstacles).
- As the developer, I want to re-run each phase's checks on my Linux machine, so that what
  works in the Mac's container is proven on real Linux before the next phase starts.

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
  maximum duration. The same seed SHALL spawn the first wave's enemies in the same places.
  Later waves spawn where the player can see, so they repeat only if the player's path does.
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
  the Linux container, and natively on Linux with the same commands. Every check a phase adds
  SHALL also run natively on Linux, so the owner can repeat it there at the end of the phase.
- **FR15 — Kept logs.** Every episode, whatever its policy, SHALL keep its decisions (the state
  sent and the tactic chosen, plus Jev's probabilities and cost), the player's path and its
  result, in the repository. Nothing SHALL delete them. They are the material for studying how
  the game gets beaten, and they carry the spend ledger between machines.

## Acceptance criteria (verifiable)

- **AC1 (FR1)** — Building `make` and `make bonus` on this spec's working tree and on the
  base gives identical `obj/*.o` and `obj_bonus/*.o` (sha256).
  `git diff --stat <base> -- . ':(exclude)agent' ':(exclude)sources/jev' ':(exclude)specs' ':(exclude)CLAUDE.md'`
  is empty, and so is the same path set in `git ls-files --others --exclude-standard`: every
  change, committed or not, and every new file is under those three directories or is the root
  `CLAUDE.md` (the handoff for Claude sessions, which no build reads).
  `norminette sources includes libft` exits 0.
- **AC2 (FR2)** — A 10 s headless run prints one observation per frame (>= 40/s on
  `subject_map`). Every line parses as JSON with the documented fields.
- **AC3 (FR3)** — A scripted sequence of commands ("forward 1 s, then turn left 1 s, then
  fire") changes the observed position, heading and weapon state as expected. With no input at
  all, the frame rate matches the no-agent build within 10%.
- **AC4 (FR4)** — Spec 001's movement check, re-run on `cub3D_agent` through the bridge:
  holding "forward" for 2 s moves the player 2.4 cells within 10% on the two maps of
  `tests/check.sh` `probe_maps()`: a short corridor (fast to render) and `test_map` facing east
  (slow; 44-56 fps before spec 001).
- **AC5 (FR5)** — Two idle runs with the same seed print identical enemies (x, y, type, hp)
  in their first observation that has enemies. A run with another seed prints different ones,
  which shows the comparison can fail.
- **AC6 (FR6)** — Every state sent to Jev in a recorded episode is under 2,000 characters and
  contains no floating-point coordinates. Checked by a test over the decision log.
- **AC7 (FR7)** — A unit test: an answer below the threshold leaves the tactic unchanged.
- **AC8 (FR8)** — A unit test with a fake transport: 429, then 529, then success. The request
  is retried, and the controller loop keeps ticking meanwhile. When every retry fails, the
  episode goes on with the current tactic. In a real episode, the agent's loop stalls about as
  often as with the scripted policy on the same seed and duration (the margin is set in
  `tasks.md`, T7). A stall is a gap above 100 ms between observations handled by the
  controller, timed with the host's monotonic clock.
  - The game's own `t` cannot show such a stall: the game never waits, and the pipe buffers
    the lines it writes meanwhile.
- **AC9 (FR9)** — After a real episode, every decision row has `model`, `input_tokens`,
  `cost`, `latency_ms` and `confidence`. The answering model is `typesafe/jev-1.13-20260917`,
  or a warning was printed.
- **AC10 (FR10)** — A unit test: with a cap of $0.0001, calls stop after the cap and the log
  says why.
- **AC11 (FR11/FR12)** — The evaluation report lists, for each policy on the test seeds:
  n, wins, survival-time median and quartiles, waves cleared, the share of time spent in each
  tactic (in wins and in losses), and Jev $/episode and latency p50/p95. The config hash
  printed on the report matches the frozen one.
- **AC12 (FR13)** — A search for the shape of a real OpenRouter key,
  `sk-or-v1-[0-9a-f]{64}`, finds nothing in the working tree (logs included), the git
  history, the image (`docker history --no-trunc`) or the container's environment.
  - It searches for the full shape, not the bare `sk-or-` prefix, because these docs mention
    the prefix on purpose.
- **AC13 (FR14)** — The same `run` and `eval` commands work with `--runner docker` (Mac) and
  `--runner local` (Linux). The owner checks it on native Linux at every phase checkpoint
  (`tasks.md`, L1-L5), each check with the same command as on the Mac minus the container.
- **AC14 (FR15)** — After any run, `git status --porcelain agent/runs` lists its folder as new:
  it is not ignored. The folder holds `result.json`, `episode.jsonl` and `decisions.jsonl` with
  the fields `plan.md` documents ("Logs").

## Out of scope

- Seeing pixels; any vision model.
- Door tactics (closing a door between the player and the zombies). This is a candidate for
  v2 once v1 is measured.
- Changing the 42 deliverable. The defects listed in the research are fixed by spec 001,
  before this one starts.
- Training or fine-tuning (Jev does not allow it).
- Live viewing or video recording (optional task only). On a Linux desktop, a run on the real
  display (`DISPLAY=:0`) should show the game with no extra tooling (not verified yet).
- **Harder maps (obstacles)**, if the logs show a pattern worth breaking: a v2 candidate.
  - New maps go in `agent/maps/`, never in `maps/`, which belongs to the deliverable.
  - `run` and `eval` already take `--map`, and every `result.json` records which map it used.
  - Each new map is its own experiment, with its own dev/test seeds and freeze.
- Publishing, or commits and pushes to the shared repo, without the user's explicit OK.

## Decisions (answered by the owner on 2026-09-29)

1. **Where the code lives:** in the `Kube` repo, on `feature/jev-agentv1`, branched from
   `feature/jev-agent` (the base, which carries spec 001).
2. **Evaluation map:** `maps/bonus/subject_map.cub` only. It is bonus-valid, under the 64-cell
   flow-field guard, and the zombies spawn at random positions set by the seed.
3. **Episode budget:**
   - development seeds 1-20, used for tuning only;
   - test seeds 101-120, one episode per policy each;
   - a 180 s cap per episode;
   - **$1 total** for every Jev call of this spec: tuning, test and latency probes.
4. **Key:** the same OpenRouter key as `~/jev/libros`, read from `~/jev/libros/.env`
   (`OPENROUTER_API_KEY=...`, chmod 600) into the environment of the agent process only.
   It is never printed, logged, committed, or passed to Docker.

Added by the owner on 2026-10-05:

5. **Names:** the C bridge lives in `sources/jev/`, so that only one folder is called `agent`
   (the root `agent/`, with the Python agent and its Makefile).
6. **Linux after each phase:** development runs on this Mac through Colima. At the end of each
   phase, the owner pulls the branch on a Linux machine and re-runs that phase's checks
   natively (`tasks.md`, checkpoints L1-L5) before the next phase starts.
7. **Logs are kept:** every run's logs are committed (FR15), to study the ways the game gets
   beaten.
8. **Harder maps later:** obstacles may be added after v1, from patterns in the logs (see "Out
   of scope").

No open questions remain. Implementation starts from `START_HERE.md` in this folder.
