# Tasks 002 — Jev plays cub3D_bonus (v0.5: the checklist)

> **Changes since v0.4 (2026-10-05, a review of every task against the code):**
> - **Checks that could not work as written:**
>   - T9's `grep "sk-or-"` always matched these docs. It now looks for a full key.
>   - T7's gap check read the game's clock, which a Python stall never touches (the pipe
>     buffers). It now times the controller on the host and compares with scripted.
>   - T3c's fire check: a held fire keeps `weapon_ready` at 0, so the check fires a pulse.
>   - T2 saw only its first part fail. Now each part must fail once, and new untracked files
>     are caught too.
> - **Defects in the design:**
>   - the 0.05 rad aim dead zone could stop the aim where a target beyond ~9 cells is never
>     shot; the dead zone is now in cells (`plan.md`, "Controller (exact)");
>   - the RETREAT description told Jev "turn away", while the controller keeps facing the
>     threat;
>   - "stale answers" could not happen with one request in flight; they are now defined by
>     events.
> - **Gaps filled:**
>   - AC5 is exact, with a second seed as a negative control;
>   - AC7 moved to T7, where the gate is built;
>   - AC6 is checked on the real decision log, AC13 has a task (T10), and T9's report is
>     copied where git keeps it;
>   - T3c names its map and how to unwrap the heading;
>   - "no input" runs keep stdin open, because EOF quits;
>   - T4a pins Python 3.12 and commits `uv.lock`;
>   - T8's cost uses the tokens R12 measures;
>   - the scripted policy decides on Jev's schedule;
>   - the initial tactic is ENGAGE;
>   - `-D AGENT` is dropped, since nothing reads it.
>
> **Changes since v0.3 (2026-10-03):** T8 gained the option-order check, because TypeSafe's
> docs now say `jev-1.13` leans toward the first option of a Choice. Nothing else moved.
>
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
    1. checks that nothing outside the allowed paths changed or was added. With the pathspec
       `-- . ':(exclude)agent' ':(exclude)sources/agent' ':(exclude)specs' ':(exclude)CLAUDE.md'`,
       both `git diff --stat origin/feature/jev-agent <pathspec>` (committed and uncommitted
       changes) and `git ls-files --others --exclude-standard <pathspec>` (new untracked
       files, which `git diff` does not list) must print nothing;
    2. in the container, builds the base and the working tree with `make -s && make -s bonus`
       and compares the sorted `sha256sum` lists of every `obj/**/*.o` and `obj_bonus/**/*.o`
       (same files, same hashes):
       - the base: `git archive origin/feature/jev-agent` piped into `/tmp/base`, with
         `/kube/minilibx-linux` copied next to it;
       - the working tree: `dev/dev.sh sync`, then `/kube`;
       - the top-level `Makefile` compiles with relative paths (`$<`), so objects from two
         directories can match byte for byte;
    3. runs `norminette sources includes libft` (exit 0).

    It prints PASS or FAIL per part and exits 1 on any failure.
  - **Verify:** it passes. Then **see each part fail once**, reverting after each edit:
    - change a number in a statement of `sources/render/shotgun.c` (for example `0.08` to
      `0.09`): parts 1 and 2 FAIL, part 3 passes;
    - add a norm error that leaves the object unchanged in `sources/render/raycasting.c` (for
      example a trailing space at the end of a line): parts 1 and 3 FAIL, part 2 passes;
    - create an untracked `includes/probe.h`: part 1 FAILs.

    After the last revert it passes again. A part never seen failing proves nothing.
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
    timed lines to the game's stdin while its stdout is captured. Use
    `maps/bonus/subject_map.cub`, seed 1: the player starts at (26.5, 11.5) facing north, with
    5 free cells ahead (rows 6-10 of column 26). Measure each step between obs lines by their
    `t`:
    - `C 1 0 0 0 0 0 0` for 1 s moves the player about 1.2 cells (±10%);
    - `C 0 0 0 0 1 0 0` for 1 s changes the heading by about 1.8 rad (±10%), and turns left:
      the change of `atan2(dy, dx)`, unwrapped into (-pi, pi] as `turn()` in `tests/check.sh`
      does, is negative in y-down;
    - a fire pulse, `C 0 0 0 0 0 0 1` and then `C 0 0 0 0 0 0 0` about 0.1 s later, makes
      `weapon_ready` drop to 0, and it is back to 1 about 0.6 s after the drop. A held fire
      keeps it at 0, because the weapon refires the moment it is ready (`plan.md`,
      "C bridge / Commands");
    - `Q` exits with code 0;
    - closing stdin exits with code 0 within 1 s;
    - with no input, the obs rate on `maps/good/minimal.cub` is 75 ± 10% (the 001 baseline).
      "No input" means stdin is open and silent (`sleep 6 | ...`): EOF would quit at once.
  - **Commit:** `agent: apply C/Q commands from stdin; exit on EOF`.
- [ ] **T3d** — Fair timing and the seed (AC4, AC5).
  - **Do:** nothing new is expected. Spec 001 already made movement time-based, and T3a set
    the seed.
  - **Verify:**
    - AC4: forward for 2 s gives 2.4 cells ± 10% on two maps with different frame rates: the
      corridor and the test_map-facing-east maps of `tests/check.sh` `probe_maps()`. Recreate
      them with that function's two commands (a `printf` and a `sed`). Do not source
      `check.sh`: sourcing it runs every section.
    - AC5: two idle runs with seed 7 (`sleep 3 | ...`) print **identical `enemies` (x, y, type,
      hp)** in their first obs that has enemies. The spawn does not depend on `dt`; see
      `plan.md`, "C bridge", `agent_main.c`. Then a run with seed 8 must print different
      ones, so the comparison is seen able to fail.
  - **Commit** (only if code changed): `agent: ...`. Otherwise tick it in the next commit.
- [ ] **T3e** — Fixtures and the regression.
  - **Do:** record `agent/tests/fixtures/idle_seed7.jsonl` (5 s, no input: `sleep 5 | ...`) and
    `agent/tests/fixtures/moves_seed7.jsonl` (the T3c sequence). Keep each under 500 KB: cut
    lines if needed, but keep line 1.
  - **Verify:** `agent/check_isolation.sh` passes, and `dev/dev.sh check` prints `ALL PASSED`.
  - **Commit:** `agent: record observation fixtures for the Python tests`.

## Python agent (`agent/`, runs on the Mac)

- [ ] **T4a** — Package skeleton.
  - **Read:** `plan.md`: "Layout", "SDK facts".
  - **Do:**
    - `agent/pyproject.toml`: uv, Python >= 3.12, `typesafe-sdk==0.7.2`, pytest, the
      `kube-agent` script;
    - `agent/.python-version` with `uv python pin 3.12`. This Mac has 3.12, 3.13 and 3.14, so
      without a pin uv picks whichever it finds, and the SDK's support for 3.14 is not
      verified;
    - `src/kube_agent/__init__.py`;
    - `cli.py`, with subcommands that print "not implemented yet";
    - `config.py`;
    - commit `agent/uv.lock`.
  - **Verify:** `cd agent && uv sync && uv run python --version && uv run kube-agent --help &&
    uv run pytest -q`. Python reports 3.12.x, and pytest runs 0 tests or a trivial one.
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
    - `nearest` is `null` with no enemies;
    - **AC6:** over every obs of both fixtures, the state is under 2,000 characters and holds
      no float.
  - **Commit:** `agent: semantic state from observations`.
- [ ] **T5a** — `controller.py`.
  - **Read:** `plan.md`, "Controller (exact)".
  - **Verify** with pytest:
    - it turns toward the target's side, and does not turn inside the dead zone;
    - a target 9.5 cells ahead and 0.049 rad off the aim line (0.47 cells, outside the 0.45
      fire margin) is turned toward. The v0.3 rule (0.05 rad) would neither turn nor fire, so
      the player would be stuck. Write this test first and see it fail against that rule;
    - no fire when any single fire condition is false; fire when all hold;
    - the movement projection for each tactic, with `w` normalised;
    - RETREAT and SEARCH BFS on small hand-made maps;
    - stuck detection;
    - no repeated identical `C` lines.
  - **Commit:** `agent: controller (aim, fire, movement, BFS)`.
- [ ] **T5b** — `policies.py`: idle and scripted.
  - **Verify:** pytest on the scripted rules in `plan.md` ("Controller (code, every
    observation)", "Scripted policy"), one case per rule. The scripted policy decides on Jev's
    schedule (every 0.5 s and on events), not on every obs. The initial tactic is ENGAGE.
    Idle never sends a command.
  - **Commit:** `agent: idle and scripted policies`.
- [ ] **T5c** — `episode.py` and `kube-agent run`.
  - **Read:** `plan.md`: "Logs", "Runtime expectations".
  - **Do:**
    - one episode ends on `state != 0` (win or lose) or at `--max-seconds` (default 180),
      then sends `Q`;
    - write `agent/runs/<id>/episode.jsonl` and `result.json`: outcome, `survival_s`,
      `wave_reached`, kills (the number of enemies that disappear within the same wave),
      `damage_taken`, drops, `stalls` and `config_sha256`;
    - `stalls` counts gaps above 100 ms between observations handled by the controller, timed
      with the host's monotonic clock (`plan.md`, "Logs"). Unit-test the counter with a fake
      loop that blocks for 0.2 s every 0.5 s: it must count them.
  - **Verify:** run idle and scripted on seeds 1-5 through the docker runner. Every run writes
    a `result.json`. **The scripted median survival is longer than idle's.** Append the
    numbers to the research as **R11** ("Baselines on dev seeds 1-5").
  - **Commit:** `agent: episode runner and first baselines (dev seeds 1-5)`.

## Jev

- [ ] **T6** — `jev_client.py` and `kube-agent spend` (AC8, AC10).
  - **Read:** `plan.md`: "SDK facts", "Key", "Budget ledger", "Jev policy";
    `~/jev/libros/src/libros/jev.py` (the owner's working client: `_request_id`, `_coste`,
    `cargar_clave`); **`typesafe_sdk/_core/retry.py`** in the installed package (what
    `RetryPolicy.timeout` means). Write its meaning into this task's "Done" note.
  - **Do:**
    - a pinned model, and a warning when `r.model != "typesafe/jev-1.13-20260917"`;
    - cost from the raw JSON; request id from the header;
    - retries with a short per-attempt timeout;
    - the budget cap, and one `decisions.jsonl` row per call;
    - `spend`, and the $1.00 refusal shared by every command that calls Jev (`plan.md`,
      "Budget ledger").
  - **Verify** with pytest and `httpx2.MockTransport`, never the network:
    - AC8: 429, then 529, then 200 is retried, and a concurrent ticker keeps ticking during
      the retries;
    - AC8: when every attempt fails, nothing is raised into the caller, and the row has an
      `error`;
    - AC10: a $0.0001 cap stops the calls and logs why;
    - a ledger whose rows add up to $1.00 makes the client refuse to start;
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
- [ ] **T7** — The Jev policy in the loop (AC6, AC7, AC8, AC9).
  - **Do:**
    - decide every 0.5 s or on an event (new wave, health band drop), with at most one request
      in flight;
    - the confidence gate;
    - stale answers, as `plan.md` defines them ("Jev policy"), are logged with
      `applied: false`, and a new request goes out at once;
    - after the budget stop, fall back to scripted.
  - **Verify** with pytest, using a fake client:
    - AC7: an answer below θ leaves the tactic unchanged; one at or above θ changes it;
    - an answer whose state predates a new wave is not applied, and a new request follows;
    - an answer that arrives after the budget fallback is not applied.
  - **Verify** with a real run:
    - `kube-agent run --policy jev --seed 1 --max-seconds 60` completes. Load the key as
      `START_HERE.md` shows, and check `spend` first (about $0.007 [calc]);
    - AC9: every decision row has the AC9 fields;
    - AC6: the T4c check (under 2,000 characters, no float) passes on every state in this
      run's `decisions.jsonl`;
    - AC8: run scripted on seed 1 with `--max-seconds 60` as well. Jev's `stalls` may exceed
      scripted's by at most 5 (**ASSUMPTION**: a margin for noise). A loop blocked by each
      call would add one stall per decision, about 120 in 60 s [calc].
  - **Commit:** `agent: Jev tactic policy in the game loop`.
- [ ] **T8** — Tuning on development seeds 1-20 only, then the freeze.
  - **Read:** research R5 (Jev's weak points); `CONTEXT.md`, "Jev in two minutes".
  - **Do:**
    - run the Jev policy on dev seeds and look at `decisions.jsonl`: where does the tactic
      look wrong?
    - **option-order check** (R5, "Choice option order": `jev-1.13` leans toward the first
      option of a Choice). `kube-agent order-check --n 100` takes at least 100 states already
      logged in `decisions.jsonl` on dev seeds. It asks each one twice through `jev_client`,
      once in the current order and once with the options reversed (same criteria text), and
      logs both answers under `agent/runs/order-check/`. Report how often the `choice`
      differs, and how often the first-listed option wins in each order. The spend counts
      against the $1 ledger: 200 calls times the tokens per call measured in R12, about
      $0.011 at 1,300 tokens [calc].
      - If the choice differs in more than 10% of the states (**ASSUMPTION**: a starting
        value, the owner may change it), the order is not neutral. Then ask the same Choice
        twice in one request (two question ids, reversed orders; same state, so the state
        tokens are paid once) and apply a tactic only when both agree. Measure that on the
        same states before adopting it.
      - Otherwise keep one question and note the result in R13.
    - adjust only the question's criteria text, θ and the decision cadence (and, if the order
      check calls for it, the two-order question);
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
    - AC12: the pattern `sk-or-v1-[0-9a-f]{64}` (`grep -E`) matches nothing in:
      - `agent/` (logs included) and `specs/`;
      - `git log -p --all`;
      - `docker history --no-trunc kube-dev`;
      - `docker exec kube-dev env`.

      The owner's key has this shape (checked 2026-10-05 without printing it), and the docs
      never do. A bare `sk-or-` would match `START_HERE.md` and `plan.md`, which mention the
      prefix. To see that the search can find something, run it once on a temporary file
      holding a made-up key of that shape.
    - The Wilson function is unit-tested with 47/50, which gives 84-98% (the `libros` result).
  - **Keep the evidence:** `agent/runs/` is gitignored, so copy `report.md` to
    `specs/002-jev-agent/report-<date>.md` and append its summary to the research as **R14**.
  - 🛑 **Report the results to the owner as they are.** If scripted beats Jev, say so.
  - **Commit:** `agent: final evaluation on test seeds 101-120`.
- [ ] **T10** — Regression, and the local runner (AC13).
  - **Verify:** `agent/check_isolation.sh` passes, `dev/dev.sh check` prints `ALL PASSED`,
    and `cd agent && uv run pytest -q` is green.
  - **AC13:** every other run used `--runner docker`. `--runner local` is checked inside the
    container, which is a native Linux. The scripted policy needs no key:

    ```bash
    dev/dev.sh sync && docker exec kube-dev make -s -C agent
    docker exec kube-dev pip3 install uv
    docker exec -e DISPLAY=:99 -w /kube/agent kube-dev \
      uv run kube-agent run --runner local --policy scripted --seed 1 --max-seconds 20
    ```

    It must write a `result.json`. `pip3` exists in the image, because it installs
    norminette. `uv` fetches Python 3.12 and the dependencies over the network.
    - If that fails for a network reason, say so in the Done note: AC13 then stays unverified
      for `local`.
    - Run `dev/dev.sh up` afterwards, so later work starts from a clean container.
  - **Commit:** `specs: spec 002 complete`, with `CONTEXT.md` "Status" updated.
- [ ] **T11** — (optional, only if the owner asks) Watch or record an episode: `ffmpeg -f
  x11grab` in the container, or `x11vnc` plus macOS Screen Sharing. Neither is verified yet.
- [ ] 🛑 **T12** — Push, only when the owner asks.
