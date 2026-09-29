# Tasks 002 — Jev plays cub3D_bonus (v0.3: the checklist)

> **How to use this file.** Start with `START_HERE.md`.
> - Work top to bottom, one task at a time. Before a task, read its **Read** list.
> - When its **Verify** passes, tick `[x]` and append `Done <date>:` with the evidence
>   (numbers, not adjectives).
> - Make **one commit per task**, with the given message. **Never push** unless the owner asks.
> - 🛑 means stop, report to the owner, and wait. Stop also whenever a check fails for a reason
>   you do not understand, or a task seems to need a path outside `agent/`, `sources/agent/`,
>   `specs/` or `CLAUDE.md`.
>
> Paths are relative to the repo root. "The container" is `kube-dev` (see `START_HERE.md`,
> "Environment"). "The base" is `origin/feature/jev-agent` (`0ac5649`).

## Setup

- [x] **T0** — Owner decisions. **Done 2026-09-29:** `spec.md`, "Decisions": map
  `subject_map`, dev seeds 1-20 and test seeds 101-120, 180 s cap, $1 total, the key from
  `~/jev/libros/.env`.
- [ ] **T1** — The environment works on this branch (no code).
  - **Read:** `START_HERE.md` ("Environment").
  - **Do:** `colima start` if it is not running, then `dev/dev.sh up`, then `dev/dev.sh check`.
  - **Verify:** the last line is `ALL PASSED` (10 sections).
  - **Done when:** it passes. Commit: none; tick it in T2's commit.
- [ ] **T2** — Isolation guard `agent/check_isolation.sh` (AC1).
  - **Read:** `spec.md` AC1; `plan.md`, "Layout"; `dev/dev.sh` (how the tree is copied into
    the container).
  - **Do:** a bash script, run on the Mac, that:
    1. checks that `git diff --stat origin/feature/jev-agent -- . ':(exclude)agent'
       ':(exclude)sources/agent' ':(exclude)specs' ':(exclude)CLAUDE.md'` is empty;
    2. in the container, builds the base and the working tree with `make -s && make -s bonus`
       and compares the `sha256sum` of every `obj/**/*.o` and `obj_bonus/**/*.o`:
       - the base: `git archive origin/feature/jev-agent` piped into `/tmp/base`, with
         `/kube/minilibx-linux` copied next to it;
       - the working tree: `dev/dev.sh sync`, then `/kube`;
    3. runs `norminette sources includes libft` (exit 0).

    It prints PASS or FAIL per part and exits 1 on any failure.
  - **Verify:** it passes. Then make a one-character edit in a comment of
    `sources/render/raycasting.c`: the script must FAIL. Revert the edit: it passes again.
    Seeing it fail once is mandatory.
  - **Commit:** `agent: add the isolation guard for spec 002 (AC1)`.

## C bridge (`sources/agent/`, `agent/Makefile`)

- [ ] **T3a** — Skeleton that builds and runs like the bonus.
  - **Read:**
    - `plan.md`: "Build", "C bridge";
    - `sources/main.c`, `sources/mlx_loop_and_hook/mlx.c`, `sources/render/game_loop.c`;
    - `includes/cub3d.h` (the prototypes).
  - **Do:**
    - `agent/Makefile` and `agent/.gitignore`;
    - `sources/agent/agent.h`, `agent_main.c` (`<map> <seed>`, overriding the seed after
      `init_game`), `agent_loop.c` (no key or mouse hooks), `agent_frame.c` (the copied frame).
      No I/O yet.
  - **Verify**, in the container, after `dev/dev.sh sync`:
    - `make -s -C agent` builds `agent/cub3D_agent`;
    - `DISPLAY=:99 timeout 5 ./agent/cub3D_agent maps/bonus/subject_map.cub 1; echo $?` prints
      `124`, meaning it was still alive;
    - `./agent/cub3D_agent maps/bonus/subject_map.cub` prints `Error` and exits 1;
    - `norminette sources/agent` exits 0;
    - `agent/check_isolation.sh` passes.
  - **Commit:** `agent: C skeleton of cub3D_agent (bonus frame, seed argument)`.
- [ ] **T3b** — The init line and one obs line per frame (AC2).
  - **Read:** `plan.md`: "Contracts / Game -> agent", "C bridge" (non-blocking, 4096 bytes).
  - **Do:** `agent_io.c` (`agent_init_io`: `O_NONBLOCK` on stdin and stdout, then the init
    line) and `agent_obs.c` (`agent_print_obs`, `drops`).
  - **Verify:** run 10 s on `subject_map`, seed 1, with stdout to `/tmp/obs.jsonl`. Then, with
    `python3` in the container:
    - line 1 has `type == "init"` and a map of `height` rows of `width` characters;
    - there are at least 40 obs lines per second of `t`;
    - every line is valid JSON with exactly the contract's fields;
    - `drops == 0`.
  - **Commit:** `agent: print the init line and one observation per frame`.
- [ ] **T3c** — Commands, fire, `Q` and EOF (AC3).
  - **Read:** `plan.md`: "Agent -> game", "C bridge / Commands";
    `sources/movement/input_bonus.c` (what Up does); `sources/movement/player.c`.
  - **Do:** `agent_read_commands` in `agent_io.c`.
  - **Verify** with a small feeder, a bash or `python3` script in the container that writes
    timed lines to the game's stdin while its stdout is captured:
    - `C 1 0 0 0 0 0 0` for 1 s moves the player about 1.2 cells (±10%);
    - `C 0 0 0 0 1 0 0` for 1 s changes the heading by about 1.8 rad (±10%), and turns left:
      `atan2(dy, dx)` decreases in y-down;
    - `C 0 0 0 0 0 0 1` makes `weapon_ready` drop to 0, and it is back to 1 after about 0.6 s;
    - `Q` exits with code 0;
    - closing stdin exits with code 0 within 1 s;
    - with no input, the obs rate on `maps/good/minimal.cub` is 75 ± 10% (the 001 baseline).
  - **Commit:** `agent: apply C/Q commands from stdin; exit on EOF`.
- [ ] **T3d** — Fair timing and the seed (AC4, AC5).
  - **Do:** nothing new is expected. Spec 001 already made movement time-based, and T3a set
    the seed.
  - **Verify:**
    - AC4: forward for 2 s gives 2.4 cells ± 10% on two maps with different frame rates. Use
      the corridor and the test_map-facing-east maps that `tests/check.sh` builds in
      `probe_maps()`;
    - AC5: two idle runs with seed 7 give **the same cells (floor of x, y) and types** for
      wave 1, read from the first obs where enemies appear. Exact float positions may differ
      by the first frame's `dt`.
  - **Commit** (only if code changed): `agent: ...`. Otherwise tick it in the next commit.
- [ ] **T3e** — Fixtures and the regression.
  - **Do:** record `agent/tests/fixtures/idle_seed7.jsonl` (5 s, no input) and
    `agent/tests/fixtures/moves_seed7.jsonl` (the T3c sequence). Keep each under 500 KB: cut
    lines if needed, but keep line 1.
  - **Verify:** `agent/check_isolation.sh` passes, and `dev/dev.sh check` prints `ALL PASSED`.
  - **Commit:** `agent: record observation fixtures for the Python tests`.

## Python agent (`agent/`, runs on the Mac)

- [ ] **T4a** — Package skeleton.
  - **Read:** `plan.md`: "Layout", "SDK facts".
  - **Do:** `agent/pyproject.toml` (uv, Python >= 3.12, `typesafe-sdk==0.7.2`, pytest, the
    `kube-agent` script), `src/kube_agent/__init__.py`, `cli.py` (subcommands that print
    "not implemented yet"), `config.py`.
  - **Verify:** `cd agent && uv sync && uv run kube-agent --help && uv run pytest -q`, with
    0 tests or a trivial one.
  - **Commit:** `agent: Python package skeleton`.
- [ ] **T4b** — `bridge.py`.
  - **Do:**
    - an asyncio subprocess;
    - runner `docker` (`docker exec -i -e DISPLAY=:99 -w /kube kube-dev ./agent/cub3D_agent
      <map> <seed>`) or `local` (`./agent/cub3D_agent <map> <seed>`, cwd = repo root);
    - parse `init` and `obs` lines; `send(command_line)`; `close()` sends `Q`, then waits.
  - **Verify:** pytest with a fake child process: a tiny Python script that prints a fixture
    and echoes stdin to a file. Lines parse, commands arrive in order, and `close()` ends the
    child.
  - **Commit:** `agent: game bridge over stdin/stdout (docker and local runners)`.
- [ ] **T4c** — `features.py` (AC6).
  - **Read:** `plan.md`: "Conventions", "Semantic features".
  - **Do:** obs + map + short history -> the semantic state dict.
  - **Verify** with pytest:
    - the worked example (the enemy at (5.5, 4.5) is `left`);
    - every band boundary (0.99 / 1.0, 2.49 / 2.5, 5.99 / 6.0, and health 29 / 30, 59 / 60);
    - all 8 sectors;
    - `in_view` at 0.58 and at 0.59 rad;
    - `being_hit`;
    - `open_directions` on a hand-made map;
    - **AC6:** over every obs of both fixtures, the state is under 2,000 characters and holds
      no float.
  - **Commit:** `agent: semantic state from observations`.
- [ ] **T5a** — `controller.py`.
  - **Read:** `plan.md`, "Controller (exact)".
  - **Verify** with pytest:
    - it turns toward the target's side;
    - no fire when any single fire condition is false; fire when all hold;
    - the movement projection for each tactic;
    - RETREAT and SEARCH BFS on small hand-made maps;
    - stuck detection;
    - no repeated identical `C` lines.
  - **Commit:** `agent: controller (aim, fire, movement, BFS)`.
- [ ] **T5b** — `policies.py`: idle and scripted.
  - **Verify:** pytest on the scripted rules in `plan.md` ("Controller (code, every
    observation)", "Scripted policy"), one case per rule. Idle never sends a command.
  - **Commit:** `agent: idle and scripted policies`.
- [ ] **T5c** — `episode.py` and `kube-agent run`.
  - **Read:** `plan.md`: "Logs", "Runtime expectations".
  - **Do:**
    - one episode ends on `state != 0` (win or lose) or at `--max-seconds` (default 180),
      then sends `Q`;
    - write `agent/runs/<id>/episode.jsonl` and `result.json`: outcome, `survival_s`,
      `wave_reached`, kills (the number of enemies that disappear within the same wave),
      `damage_taken`, drops and `config_sha256`.
  - **Verify:** run idle and scripted on seeds 1-5 through the docker runner. Every run writes
    a `result.json`. **The scripted median survival is longer than idle's.** Append the
    numbers to the research as **R11** ("Baselines on dev seeds 1-5").
  - **Commit:** `agent: episode runner and first baselines (dev seeds 1-5)`.

## Jev

- [ ] **T6** — `jev_client.py` and `kube-agent spend` (AC7, AC8, AC10).
  - **Read:** `plan.md`: "SDK facts", "Key", "Budget ledger", "Jev policy";
    `~/jev/libros/src/libros/jev.py` (the owner's working client: `_request_id`, `_coste`,
    `cargar_clave`); **`typesafe_sdk/_core/retry.py`** in the installed package (what
    `RetryPolicy.timeout` means). Write its meaning into this task's "Done" note.
  - **Do:**
    - a pinned model, and a warning when `r.model != "typesafe/jev-1.13-20260917"`;
    - cost from the raw JSON; request id from the header;
    - retries with a short per-attempt timeout;
    - the budget cap, and one `decisions.jsonl` row per call.
  - **Verify** with pytest and `httpx2.MockTransport`, never the network:
    - AC7: an answer below θ leaves the tactic unchanged;
    - AC8: 429, then 529, then 200 is retried, and a concurrent ticker keeps ticking during
      the retries;
    - AC10: a $0.0001 cap stops the calls and logs why;
    - a missing request-id header does not raise.
  - **Commit:** `agent: Jev client with pinned model, cost, retries and budget cap`.
- [ ] **T6b** — The first real calls, and Jev's latency (the unknown in R2).
  - **Do:** `kube-agent latency --n 50` sends one state recorded from a fixture 50 times,
    sequentially.
  - Check `kube-agent spend` first. This costs about $0.003.
  - Load the key as shown in `START_HERE.md`.
  - **Verify:**
    - 50 rows, each with `model`, `input_tokens`, `cost` and `latency_ms`;
    - the answering model is `typesafe/jev-1.13-20260917`. 🛑 **If it is not, stop and tell the
      owner.**
  - Append **R12** to the research: latency p50/p95, tokens per call and cost per call. If
    p95 > 500 ms, switch the policy to event-only decisions (`plan.md`, "Risks") before T7,
    and note it.
  - **Commit:** `agent: measured Jev latency and cost (R12)`.
- [ ] **T7** — The Jev policy in the loop (AC8, AC9).
  - **Do:**
    - decide every 0.5 s or on an event (new wave, health band drop), with at most one request
      in flight;
    - the confidence gate;
    - stale answers are discarded;
    - after the budget stop, fall back to scripted.
  - **Verify:**
    - `kube-agent run --policy jev --seed 1 --max-seconds 60` completes;
    - every decision row has the AC9 fields;
    - the share of obs gaps above 100 ms is not higher than in an idle run on the same seed
      (AC8).
  - **Commit:** `agent: Jev tactic policy in the game loop`.
- [ ] **T8** — Tuning on development seeds 1-20 only, then the freeze.
  - **Read:** research R5 (Jev's weak points); `CONTEXT.md`, "Jev in two minutes".
  - **Do:**
    - run the Jev policy on dev seeds and look at `decisions.jsonl`: where does the tactic
      look wrong?
    - adjust only the question's criteria text, θ and the decision cadence;
    - log every iteration in the research as **R13**: what changed, dev numbers, spend;
    - never use seeds >= 101;
    - keep `kube-agent spend` under about $0.45 at the end of tuning.
  - 🛑 **Before freezing, show the owner:** R13, the final question and θ, and the dev results
    of idle, scripted and Jev. **Wait for the OK.**
  - **Done when:** the owner said OK, and `agent/frozen.json` holds `config_sha256` plus the
    date.
  - **Commit:** `agent: freeze the Jev policy config after dev tuning`.
- [ ] **T9** — The final evaluation on test seeds 101-120 (AC11, AC12).
  - **Do:** `kube-agent eval --seeds 101-120 --policies idle,scripted,jev` (in the
    background; up to about 2 h) writes `agent/runs/eval-<date>/report.md`.
  - **Verify:**
    - AC11: the report shows, per policy, n, wins with a Wilson 95% interval, survival
      median/IQR and waves; for Jev, $/episode and latency p50/p95. Its config hash equals
      `frozen.json`'s.
    - AC12: `grep -r "sk-or-"` over `agent/`, `specs/` and `docker exec kube-dev env` finds
      nothing.
    - The Wilson function is unit-tested with 47/50, which gives 84-98% (the `libros` result).
  - 🛑 **Report the results to the owner as they are.** If scripted beats Jev, say so.
  - **Commit:** `agent: final evaluation on test seeds 101-120`.
- [ ] **T10** — Regression.
  - **Verify:** `agent/check_isolation.sh` passes, `dev/dev.sh check` prints `ALL PASSED`,
    and `cd agent && uv run pytest -q` is green.
  - **Commit:** `specs: spec 002 complete`, with `CONTEXT.md` "Status" updated.
- [ ] **T11** — (optional, only if the owner asks) Watch or record an episode: `ffmpeg -f
  x11grab` in the container, or `x11vnc` plus macOS Screen Sharing. Neither is verified yet.
- [ ] 🛑 **T12** — Push, only when the owner asks.
