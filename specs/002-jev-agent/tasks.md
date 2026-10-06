# Tasks 002 — Jev plays cub3D_bonus (v0.9: the checklist)

> **Changes since v0.8 (2026-10-06, after L1 and L2 passed on the owner's Linux): the game is
> no longer handed in at 42, so the rules that protected it are retired.** See "Decided
> 2026-10-06" below. In short:
> - the work goes on `feature/jev-agentv1` alone, and the game may change on it when a task
>   needs it;
> - `agent/check_isolation.sh` is out of the checkpoints and of T10 (it stays as a file);
> - the x86_64 ledger rows (7 and 11) are closed;
> - norminette on `sources/jev/` is no longer a gate (it passes today);
> - nothing was deleted, and `main` is as it was.

> **Changes since v0.7 (2026-10-05, the owner's rule: everything that needs Linux is written
> down, in the phases, so that nothing is forgotten):**
> - **A "Linux ledger"** (below) lists every check that only the owner's Linux can settle,
>   with its command, what to report, and the machine-dependent ways it may fail.
> - **L1 and L2 are both due.** Phase 1 was not stopped at its checkpoint (T3 started
>   without L1), which the protocol forbids. Run L1 first, then L2.
> - **T3e is now the regression only.** The fixtures were moved to the tasks that first use
>   them, as the owner's YAGNI rule says ("fixtures live in the commit of the test that uses
>   them"): `idle_seed7.jsonl` to T4b and `moves_seed7.jsonl` to T4c.
> - `--local` of `check_isolation.sh` was rehearsed in a fresh copy inside the container (a
>   Linux, though not the owner's machine): it passes.

> **Changes since v0.6 (2026-10-05, a game defect found by T3c):**
> - Strafing was a third slower than walking (0.79 against 1.2 cells/s: the game strafed along
>   `plane`, which is 0.66 long). The owner asked for it fixed, in the game and on the base
>   branch: `ad4244a` on `feature/jev-agent`, with a test in `tests/check.sh`.
> - **The base moves from `0ac5649` to `ad4244a`.** AC1 still means "objects identical to the
>   base", now the fixed one. This branch took the fix by a merge (`e5f8ad4`).
> - `check_isolation.sh` accepts `ISOLATION_BASE=<ref>`, to check against a base that is not
>   pushed yet. Without it, it compares with `origin/feature/jev-agent` as before.
> - `check_bridge.py` expects 1.2 cells/s for the strafes again.
>
> **Changes since v0.5 (2026-10-05, the owner's decisions 5-8 in `spec.md`):**
> - The C bridge folder is `sources/jev/` (it was `sources/agent/`), so `agent/` is the only
>   folder named agent.
> - **Five phases, each ending with a Linux checkpoint (L1-L5)** that the owner runs natively.
>   - `check_isolation.sh --local` and `agent/check_bridge.py` make every check runnable there.
>   - AC13 moves from T10's in-container workaround to those checkpoints.
> - **Every run's logs are committed** (FR15, AC14):
>   - richer `result.json` and `episode.jsonl`;
>   - decisions logged for every policy;
>   - git carries the spend ledger between machines.
> - T3b-T3d keep their checks in `agent/check_bridge.py`, so T3d now has code and a commit.
> - `run` and `eval` take `--map`, for harder maps after v1 (`agent/maps/`, never `maps/`).
>
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
>   - AC6 is checked on the real decision log;
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
> - Make **one commit per task**, with the given message. A task's commit includes the runs
>   it made under `agent/runs/` (FR15). **Never push** unless the owner asks.
> - **Each phase ends with a Linux checkpoint (L1-L5).**
>   1. 🛑 Stop and give the owner the phase's summary. The owner asks for the push.
>   2. The owner pulls the branch on Linux and runs the checkpoint's commands.
>   3. The owner reports the results, and the checkpoint is ticked in the next commit with
>      them.
>
>   A failure seen only on Linux comes back with its output and is fixed here, never by hand
>   on Linux. The next phase starts only after its checkpoint passes.
> - 🛑 means stop, report to the owner, and wait. Stop also whenever a check fails for a reason
>   you do not understand, or a task seems to need a change to the game itself (the sources
>   outside `sources/jev/`, `includes/`, `libft/`, the `Makefile`): that is allowed since
>   2026-10-06, but ask first and keep `tests/check.sh` passing.
>
> Paths are relative to the repo root. "The container" is `kube-dev` (see `START_HERE.md`,
> "Environment"). "The base" is `origin/feature/jev-agent` (`ad4244a`: `0ac5649`, where spec
> 001 was completed, plus the strafing fix). "Linux" is the owner's
> machine; its one-time setup is in `START_HERE.md`, section 2b.

## Linux ledger: what only the owner's machine can settle

Nothing in this ledger counts as verified until the owner pastes the output and a row says
so. At the end of every phase the summary lists the rows due at that checkpoint, each with its
command. A row leaves the ledger only when the owner reports that it passed. **Do not drop a
row because it is awkward: move it to a later checkpoint and say why.**

What a container on the Mac cannot show: the owner's hardware speed, distribution and
compiler, x86_64 against aarch64, the real packages and `uv`, and a real screen.

| # | What | State today | Due |
|---|---|---|---|
| 1 | The one-time setup of `START_HERE.md` 2b: the `apt` packages, `uv` 0.8.24, `norminette==3.3.60` | **DONE 2026-10-06** on the owner's Linux, with three fixes to the instructions (see L1) | L1 |
| 2 | `make && make bonus` from scratch | **DONE 2026-10-06**: the MiniLibX cloned at `f07d00f`, binaries of 109,088 and 139,376 bytes, the same as in the container | L1 |
| 3 | `bash tests/check.sh`: `ALL PASSED`, 10 sections | **DONE 2026-10-06**: `ALL PASSED`; the `minimal` rate was 75 fps against the 75 baseline | L1 |
| 4 | `agent/check_isolation.sh --local` | **DONE 2026-10-06** on the owner's machine: PASS, 71 identical objects, 101 files OK | L1, L2 |
| 5 | `make -C agent` with the owner's compiler under `-Werror` | **DONE 2026-10-06**: gcc 11.4.0, exit 0, a binary of 144,760 bytes (the same as in the container) | L2 |
| 6 | `python3 agent/check_bridge.py`: 24 checks | **DONE 2026-10-06**: 24 of 24 | L2 |
| 7 | An x86_64 machine: AC1 and one episode on it. 42's machines are x86_64 | **CLOSED 2026-10-06, not done: no longer needed.** The owner's Linux is aarch64 (UTM, Ubuntu 22.04.5), the same architecture as the Mac's container, and the game is no longer handed in at 42, whose machines are x86_64 | (L5) |
| 8 | The Python agent: `uv sync` (Python 3.12, `typesafe-sdk` 0.7.2), `pytest`, `--runner local` | **DONE 2026-10-06** on the owner's Linux: CPython 3.12.11, 19 packages with `typesafe-sdk` 0.7.2, **234 tests passed in 3.87 s**, and the `local` runner played 4 episodes (see L3) | L3 |
| 9 | Seeing the game on the real display (`DISPLAY=:0`) | **DONE 2026-10-06**: the owner saw the game window on the real desktop, it ran smoothly, and 3 episodes ran that way and won | L3 |
| 10 | The key file on Linux (`START_HERE.md` 2b, step 3) and one paid run | does not exist yet | L4 |
| 11 | The final x86_64 check of AC1 and one episode | **CLOSED 2026-10-06, not done: no longer needed** (see row 7) | (L5) |

## Decided 2026-10-06: the game is no longer handed in at 42

The owner said the game will no longer be used at 42, and after L1 and L2 passed asked to
simplify. What changed:

- **One working branch.** The work goes on `feature/jev-agentv1`. `feature/jev-agent` stays
  on GitHub as it is (`ad4244a`: spec 001 plus the strafing fix) and is not touched again. It
  was kept apart so the agent never mixed with the game handed in; that reason is gone. The
  earlier idea of putting only the game into `main` when finished is dropped with it.
- **The game may change on this branch** when a task needs it (for example the harder maps
  the owner wants to try later), keeping `tests/check.sh` passing. FR1 and AC1 of `spec.md`
  are retired, and so is the "only these paths may change" rule of `START_HERE.md`.
- **`agent/check_isolation.sh` is out of the checkpoints and of T10.** The file stays, and its
  header says it is retired: it still proves the game is as it was, but a change to the game
  would now fail it on purpose.
- **Norminette is no longer a gate for `sources/jev/`.** The code passes today and may keep
  passing, but the 42 norm (5 functions per file, 25 lines, no ternary) does not bind.
  `tests/check.sh` still runs norminette on the game, so it stays installed.
- **The x86_64 ledger rows (7 and 11) are closed,** as not needed: they existed for 42's
  machines.
- **Nothing was deleted and `main` was not touched.** The local `main` is still 16 commits
  ahead of `origin/main`; pushing it, and Rodrigo's part in the repository, are left for the
  owner to decide.

What does not change: the tests, the honest measurement, and the agent itself.

## Phase 1 — Setup

- [x] **T0** — Owner decisions. **Done 2026-09-29:** `spec.md`, "Decisions": map
  `subject_map`, dev seeds 1-20 and test seeds 101-120, 180 s cap, $1 total, the key from
  `~/jev/libros/.env`. Decisions 5-8 were added on 2026-10-05.
- [x] **T1** — The environment works on this branch (no code).
  - **Read:** `START_HERE.md` ("Environment").
  - **Do:** `colima start` if it is not running, then `dev/dev.sh up`, then `dev/dev.sh check`.
  - **Verify:** the last line is `ALL PASSED` (10 sections).
  - **Done when:** it passes. Commit: none; tick it in T2's commit.
  - **Done 2026-10-05:** Colima was off and `colima start` brought it up; `dev/dev.sh up` reused
    the existing `kube-dev` image. `dev/dev.sh check` ended with `ALL PASSED` in 2 min 31 s,
    all 10 sections PASS. Measured: W for 2 s moved 2.43-2.44 cells in both binaries and maps
    (expected 2.4), Left for 1 s turned 1.82-1.83 rad (expected 1.8), and `cub3D_bonus` on
    `minimal` ran at 69 fps against the 75 baseline. That is 8% under, inside the check's 15%
    band; the VM had just started.
- [x] **T2** — Isolation guard `agent/check_isolation.sh` (AC1).
  - **Read:** `spec.md` AC1; `plan.md`, "Layout"; `dev/dev.sh` (how the tree is copied into
    the container).
  - **Do:** a bash script that:
    1. checks that nothing outside the allowed paths changed or was added. With the pathspec
       `-- . ':(exclude)agent' ':(exclude)sources/jev' ':(exclude)specs' ':(exclude)CLAUDE.md'`,
       both `git diff --stat origin/feature/jev-agent <pathspec>` (committed and uncommitted
       changes) and `git ls-files --others --exclude-standard <pathspec>` (new untracked
       files, which `git diff` does not list) must print nothing;
    2. builds the base and the working tree with `make -s && make -s bonus`, and compares the
       sorted `sha256sum` lists of every `obj/**/*.o` and `obj_bonus/**/*.o` (same files, same
       hashes):
       - the base: `git archive origin/feature/jev-agent`, extracted into an empty folder;
       - the working tree: the files `dev/dev.sh sync` copies (tracked, plus untracked but
         not ignored);
       - each gets a copy of `minilibx-linux/` when it exists, so MiniLibX is not cloned
         again;
       - the top-level `Makefile` compiles with relative paths (`$<`), so objects from two
         directories can match byte for byte;
    3. runs `norminette sources includes libft` (exit 0).

    **Where it builds:**
    - by default, on the Mac, parts 2 and 3 run in the container: the base goes to
      `/tmp/base` and the working tree is `/kube` after `dev/dev.sh sync`;
    - with `--local`, on Linux, they run in two temporary folders on the machine itself. The
      Mac cannot build this MiniLibX, so `--local` is first run for real at L1.

    It prints PASS or FAIL per part and exits 1 on any failure.
  - **Verify:** it passes. Then **see each part fail once**, reverting after each edit:
    - change a number in a statement of `sources/render/shotgun.c` (for example `0.08` to
      `0.09`): parts 1 and 2 FAIL, part 3 passes;
    - add a norm error that leaves the object unchanged in `sources/render/raycasting.c` (for
      example a trailing space at the end of a line): parts 1 and 3 FAIL, part 2 passes;
    - create an untracked `includes/probe.h`: part 1 FAILs.

    After the last revert it passes again. A part never seen failing proves nothing.
  - **Commit:** `agent: add the isolation guard for spec 002 (AC1)`.
  - **Done 2026-10-05:** on a clean tree the guard prints PASS on all three parts in about 7 s
    (base `0ac5649`; 71 objects in the base and 71 in this tree; 94 files OK in norminette).
    Each part was then seen failing, and every edit was reverted (`git diff --quiet` confirmed
    the files were identical to HEAD afterwards):

    | Edit | paths | objects | norm |
    |---|---|---|---|
    | `0.08` to `0.09` in `shotgun.c` | FAIL | FAIL (only `obj_bonus/render/shotgun.o` differs) | PASS |
    | trailing space on line 17 of `raycasting.c` | FAIL | PASS | FAIL (`SPC_BEFORE_NL`) |
    | untracked `includes/probe.h` | FAIL | PASS | PASS (95 files OK) |

    The last row is why part 1 also lists untracked files: nothing else sees that file.
    `--local` is **not** run yet: the Mac cannot build the X11 MiniLibX, so it is first run for
    real at L1.
- [x] 🔑 **L1** — Linux checkpoint, phase 1 (the owner, on Linux; see "How to use"). **Done
  2026-10-06, see the note at the end of this checkpoint.** Ledger rows 1, 2, 3, 4 and 7.
  - The first time, set up the machine (`START_HERE.md`, 2b, "On a Linux machine"). Then, from
    the repo root, after `git pull --ff-only`:

    ```bash
    uname -m; cc --version | head -1; python3 --version; head -2 /etc/os-release
    Xvfb :99 -screen 0 1280x720x24 & export DISPLAY=:99
    make && make bonus
    bash tests/check.sh                          # last line: ALL PASSED
    agent/check_isolation.sh --local             # RETIRED 2026-10-06: skip it (was: PASS on all three)
    ```

    The virtual display `:99` keeps the checks off the real screen: `check.sh` moves the
    mouse.
  - **Report back** (paste the text; do not summarise it): the first line of output (the
    `uname`, compiler, Python and distribution lines), any command that failed during the
    setup, the last lines of `make` and `make bonus`, all of `check.sh`'s output, and all of
    `check_isolation.sh`'s.
  - **Ways it can fail because of the machine and not the code**, so they are not read as
    bugs:
    - `fps vs baseline (AC7)` expects `cub3D_bonus` on `minimal` at 75 fps ±15%. That 75 was
      measured on the Mac's container (the container gives 69-77). A faster or slower
      machine can fail it. If it is the only failure, report the printed number: the baseline
      then needs recording on that machine, which is a decision, not a fix;
    - the MiniLibX prints one warning, `mlx_new_image.c: ignoring return value of 'write'`.
      It is the library's own and does not stop the build;
    - `valgrind` and `norminette` must be installed (setup 2b). A missing one fails with
      "command not found".
  - **Done when:** every line passed. The tick records `uname -m` and each last line.
  - **Done 2026-10-06**, on the owner's machine, commit `8104824`: a UTM virtual machine,
    **aarch64**, Ubuntu 22.04.5, gcc 11.4.0, Python 3.10.12, `norminette` 3.3.60, `uv` 0.8.24.
    - `make` and `make bonus` from scratch: exit 0; the MiniLibX cloned at the pinned
      `f07d00f`; its only warning is its own (`mlx_new_image.c`, `write`). `git status` was
      clean after building;
    - `bash tests/check.sh`: `ALL PASSED`, 10 of 10 sections. W for 2 s moved 2.43-2.45
      cells, A and D 2.42-2.43 (the strafing fix holds on native Linux), and `cub3D_bonus` on
      `minimal` ran at **75 fps against the 75 baseline**, so the machine-dependent check did
      not fail;
    - `agent/check_isolation.sh --local`: ALL PASSED, 71 identical objects, 101 files OK. It
      was the first run of `--local` outside the container.
    - **Three fixes to the setup instructions came out of it** (all in `START_HERE.md` 2b):
      the one long `apt` line was cut in two when pasted, and four packages were left
      uninstalled; the `uv` 0.8.24 installer does not create `~/.local/bin/env`, so the step
      is an `export` of `~/.local/bin`; and the machine already had a `norminette` 3.3.59 (an
      old `pip --user`), so `uv tool install norminette==3.3.60` failed to link and needs
      `--force`.
    - The machine is **aarch64, like the Mac's container**, so this checkpoint does not settle
      the x86_64 row.

## Phase 2 — C bridge (`sources/jev/`, `agent/Makefile`)

- [x] **T3a** — Skeleton that builds and runs like the bonus.
  - **Read:**
    - `plan.md`: "Build", "C bridge";
    - `sources/main.c`, `sources/mlx_loop_and_hook/mlx.c`, `sources/render/game_loop.c`;
    - `includes/cub3d.h` (the prototypes).
  - **Do:**
    - `agent/Makefile`, and `agent/.gitignore` with only `cub3D_agent` and `obj/` (`runs/` is
      not ignored: FR15). T4a adds the Python entries when there is Python to ignore;
    - `sources/jev/agent_main.c` (`<map> <seed>`, overriding the seed after `init_game`),
      `agent_loop.c` (no key or mouse hooks), `agent_frame.c` (the copied frame). No I/O yet;
    - the seed must be 1 to 9 digits, or `Error` and exit 1: `ft_atoi` reads `abc` as 0
      without a word and does not detect overflow, so a typo would silently change the
      experiment;
    - **no `agent.h` yet:** it would be an empty header (YAGNI). T3b creates it with the first
      bridge prototypes.
  - **Verify**, in the container, after `dev/dev.sh sync`:
    - `make -s -C agent` builds `agent/cub3D_agent`;
    - `DISPLAY=:99 timeout 5 ./agent/cub3D_agent maps/bonus/subject_map.cub 1; echo $?` prints
      `124`, meaning it was still alive. A hung process also gives 124, so take a screenshot
      too (`xwd`): the screen must hold many colors, where an empty one holds 1;
    - `./agent/cub3D_agent maps/bonus/subject_map.cub` prints `Error` and exits 1, and so do
      a seed `abc` and a 10-digit seed;
    - `norminette sources/jev` exits 0;
    - `agent/check_isolation.sh` passes.
  - **Commit:** `agent: C skeleton of cub3D_agent (bonus frame, seed argument)`.
  - **Done 2026-10-05:** `make -s -C agent` built `agent/cub3D_agent` (139,416 bytes) and
    `norminette sources/jev` printed OK for all three files. `timeout 5` returned 124. The
    screenshot after 3 s on seed 1 held 1,224 colors, against 1 on the empty screen, and shows
    the minimap, the weapon, the health bar and two zombies. No seed, seed `abc` and seed
    `1234567890` each printed `Error` with exit 1, and so did `maps/bad/wall_hole.cub`
    (`Map is not closed`) and a missing map. `check_isolation.sh`: ALL PASSED, 71 objects
    identical, 97 files OK in norminette.
- [x] **T3b** — The init line and one obs line per frame (AC2).
  - **Read:** `plan.md`: "Contracts / Game -> agent", "C bridge" (non-blocking, 4096 bytes).
  - **Do:**
    - `sources/jev/agent.h`, the bridge's prototypes (it includes `cub3d.h`); it is created
      here, not in T3a, so that it is never an empty header;
    - `agent_io.c` (`agent_init_io`: the init line, then `O_NONBLOCK` on stdout unless it is a
      terminal; stdin gets the flag in T3c, when it is first read; and `agent_fail`);
    - `agent_obs.c` (`agent_print_obs`, `drops`);
    - the two call sites: `agent_init_io` in `agent_main.c` and `agent_print_obs` in
      `agent_frame.c`;
    - `agent/check_bridge.py`, Python's standard library only. It starts
      `./agent/cub3D_agent` itself, with stdin held open and stdout read as it comes. It
      prints PASS or FAIL per check and exits 1 on any failure. Its checks, on `subject_map`,
      seed 1:
      - the init line matches the map file, which the script reads itself (the start cell is
        floor in the init map);
      - the first observation matches the start, with 3 grunts on floor cells;
      - every line is valid JSON with exactly the contract's fields, in order and with their
        types, and some enemy rows were seen;
      - at least 40 obs lines per second of `t`, over a 10 s run;
      - `drops == 0` and no frame number missing, with a reader that keeps up;
      - **a stalled reader** (nothing read for 5 s, so the pipe fills): the game is not
        blocked, no line is cut, and `drops` equals the number of missing frame numbers;
      - stderr is empty.
  - **Verify:** `docker exec -e DISPLAY=:99 -w /kube kube-dev python3 agent/check_bridge.py`
    passes. See it fail twice, restoring each file from a copy afterwards:
    - rename one obs field in `agent_obs.c`: the field checks FAIL;
    - drop `O_NONBLOCK` in `agent_io.c`: the stalled-reader check FAILs.
  - **Commit:** `agent: print the init line and one observation per frame`.
  - **Done 2026-10-05:** `norminette sources/jev` OK on all 6 files and a clean build. Final
    run on the restored tree, 8 of 8 PASS: 803 observations and 2,409 enemy rows checked,
    80.9 observations per second of `t` over 9.9 s, and the stalled reader kept 394 lines and
    dropped 245 while the game reached 7.9 s. The rate varied between 66.6 and 80.9 across the
    runs of the day, always over the 40 needed. The longest line seen was 559 bytes, against
    the 4,096 limit. `check_isolation.sh`: ALL PASSED, 100 files OK in norminette. Two
    findings:
    - the first run failed on the init check, and it was my check that was wrong: the game
      turns the player's start cell into floor (`set_player_at`), so the init map has `0`
      where the file has `N`. The expectation was fixed from the code, not from the output;
    - the two deliberate breaks failed the right checks: renaming `weapon_ready` failed the
      two field checks and nothing else; keeping stdout blocking failed only the stalled
      reader, with 0 dropped and game time stuck at 4.8 s instead of 7.9 s.
- [x] **T3c** — Commands, fire, `Q` and EOF (AC3).
  - **Read:** `plan.md`: "Agent -> game", "C bridge / Commands";
    `sources/movement/input_bonus.c` (what Up does); `sources/movement/player.c`.
  - **Do:** `agent_read_commands`, in the new file `sources/jev/agent_cmd.c` (`agent_io.c` was
    kept for the setup: `set_nonblocking` now serves stdout and stdin, not on a terminal).
    Add these checks to `check_bridge.py`, which writes timed lines to the game's stdin.
    Write them first and see them fail against the T3b binary.
    - They use `maps/bonus/subject_map.cub`, seed 1: the player starts at (26.5, 11.5) facing
      north, with 5 free cells ahead (rows 6-10 of column 26).
    - Each step is measured between obs lines by their `t`:
      - `C 1 0 0 0 0 0 0` for 1 s moves the player about 1.2 cells (±10%);
      - `C 0 0 0 0 1 0 0` for 1 s changes the heading by about 1.8 rad (±10%), and turns
        left: the change of `atan2(dy, dx)`, unwrapped into (-pi, pi] as `turn()` in
        `tests/check.sh` does, is negative in y-down;
      - a fire pulse, `C 0 0 0 0 0 0 1` and then `C 0 0 0 0 0 0 0` about 0.1 s later, makes
        `weapon_ready` drop to 0, and it is back to 1 about 0.6 s after the drop. A held fire
        keeps it at 0, because the weapon refires the moment it is ready (`plan.md`,
        "C bridge / Commands");
      - `Q` exits with code 0;
      - closing stdin exits with code 0 within 1 s;
      - with no input, the obs rate on `maps/good/minimal.cub` is 75 ± 10% (the 001
        baseline). "No input" means stdin is open and silent: EOF would quit at once.
    - Also checked: malformed lines (7 kinds) are ignored whole and each leaves a warning on
      stderr; back and both strafes move the right way; a command cut in two writes still
      works; and a terminal (a pty) as stdin and stdout leaves the game running.
  - **Verify:** `check_bridge.py` passes, with the T3b checks and these. Seen failing first
    against the T3b binary (11 of the 12 new checks; the rate check does not need commands),
    then three deliberate breaks of `agent_cmd.c`, each restored from a copy:
    - strafe left and right swapped: only the two strafe checks FAIL;
    - the half-received line thrown away every frame: the forward command (sent in two
      writes) FAILs;
    - the held fire made one-shot: only the held-fire check FAILs;
    - the terminal guard removed: the terminal check FAILs with 0 observations.
  - **Commit:** `agent: apply C/Q commands from stdin; exit on EOF`.
  - **Done 2026-10-05:** `norminette sources/jev` OK on all 7 files, a clean build, and
    `check_bridge.py`: 21 of 21 PASS, three times in a row on the last fixes. Measured:
    forward 1.20 cells/s, back 1.20, turns 1.80 rad/s, the weapon 0.61 s not ready after a
    pulse, `Q` and closing stdin both exit with code 0 in 0.00-0.01 s, 355 observations in 4 s
    on a terminal. valgrind on both ways out: 0 bytes in use at exit, 0 errors.
    `check_isolation.sh`: ALL PASSED, 71 objects identical, 101 files OK. Findings:
    - **strafing was 0.79 cells/s, not 1.2.** The game strafed along `plane` (length 0.66), so
      1.2 × 0.66 = 0.792 [calc], and the measured 0.79 agreed. My first expectation was wrong.
      It was the game's own defect, outside this spec's paths, so it was reported first. The
      owner then asked for it fixed on the base: `ad4244a` (`tests/check.sh` gained an A and D
      probe that failed before the fix with 1.60 and 1.59 cells in 2 s, against 2.4, and
      passes after with 2.42 and 2.43). Merged here as `e5f8ad4`; through the bridge, strafing
      now measures 1.20 cells/s and `check_bridge.py` expects 1.2 again (21 of 21 PASS);
    - the fire-pulse check was timing-dependent: the first observation read was sometimes
      already after the shot. It now reads 0.2 s first so the weapon is seen ready;
    - the rate check on `minimal` measured 64.5 once, with 5.7 s of game time in 6 s of wall
      time (a stall of the VM; the other values of the day were 73-77). It now takes the best
      of three stretches of 3 s, since noise only slows a run down.
- [x] **T3d** — Fair timing and the seed (AC4, AC5).
  - **Do:** no game code is expected: spec 001 made movement time-based, and T3a set the
    seed. Add these checks to `check_bridge.py`:
    - AC4: forward for 2 s gives 2.4 cells ± 10% on two maps with different frame rates: the
      corridor and the test_map-facing-east maps of `tests/check.sh` `probe_maps()`.
      `check_bridge.py` writes the same two map texts into a temporary folder (and checks
      that the `0N0` to `0E0` turn of test_map changed something). Do not source `check.sh`:
      sourcing it runs every section. The check also measures each map's observations per
      second and **fails if they differ by less than 10%**: the same distance on two maps
      shows nothing about frame rate if the frame rates are the same.
    - AC5: two idle runs with seed 7 print **identical `enemies` (x, y, type, hp)** in their
      first obs that has enemies. The spawn does not depend on `dt`; see `plan.md`,
      "C bridge", `agent_main.c`. A run with seed 8 must print different ones, so the
      comparison is seen able to fail.
  - **Verify:** `check_bridge.py` passes. Then two deliberate breaks, each file restored from
    a copy:
    - the seed line of `agent_main.c` removed: only the same-seed check FAILs;
    - a fixed `dt` of 0.0125 in `tick_clock` of `agent_frame.c`, so movement is per frame:
      the fair-timing check FAILs.
  - **Commit:** `agent: check fair timing and seeded spawns (AC4, AC5)`.
  - **Done 2026-10-05:** no C change was needed. `check_bridge.py`: 24 of 24 PASS, and
    `check_isolation.sh` ALL PASSED against the pushed base `ad4244a` (71 identical objects,
    101 files OK). Measured:
    - AC4: 2.38 cells on the corridor and 2.39 on test_map, both 1.20 cells/s, while the maps
      ran at 77 and 100 observations per second. Four more runs of the same sessions gave
      74-77 and 90-99, so the difference is stable;
    - AC5: seed 7 twice gave the same 3 enemies, the first at (26.41, 7.35); seed 8 gave (25.66,
      7.63);
    - the breaks: with no seed, the two seed-7 runs spawned enemies at (24.55, 6.42)… and
      (25.58, 7.45)…, and only the same-seed check failed; with a fixed `dt`, test_map moved
      2.97 cells against 2.4 and only the fair-timing check failed.

    Finding: **test_map is now the fast map** (90-100 observations per second) **and the
    corridor the slow one** (71-87), the other way round from the 44-56 and 74-78 fps measured
    before spec 001 (research R1). The cause was not investigated: AC4 only needs the rates to
    differ, and the check now enforces it. The comment of `probe_maps()` in `tests/check.sh`
    still calls the corridor fast and test_map slow; it belongs to the base branch and was left
    alone.
- [x] **T3e** — The regression of phase 2 (it was "Fixtures and the regression").
  - **Do:** nothing new is written. The two fixtures this task used to record moved to the
    tasks that first use them, in the commit of the test that uses them (the owner's YAGNI
    rule): `idle_seed7.jsonl` to T4b and `moves_seed7.jsonl` to T4c.
  - **Verify:** `agent/check_isolation.sh` passes, `check_bridge.py` passes, and
    `dev/dev.sh check` prints `ALL PASSED`. Also rehearse the Linux commands of L1 and L2 in a
    clean copy of the repository inside the container (it is a Linux): `tar` the tree with its
    `.git` and without build outputs into a new folder, then run `make && make bonus`,
    `agent/check_isolation.sh --local`, `make -C agent` and `python3 agent/check_bridge.py`
    there. It cannot stand in for the owner's machine (ledger), but it finds what is wrong in
    the commands themselves.
  - **Commit:** `agent: phase 2 regression, Linux ledger and fixtures moved to T4 (tasks v0.8)`.
  - **Done 2026-10-05:**
    - `dev/dev.sh check`: ALL PASSED, 10 of 10 sections (strafing probes 2.42-2.44 cells, the
      `minimal` rate 76 fps);
    - `check_bridge.py`: 24 of 24 PASS;
    - `check_isolation.sh`: ALL PASSED against the pushed base `ad4244a` (71 identical
      objects, 101 files OK);
    - the rehearsal, in a fresh copy of the repository (`.git` included, 2.5 MB) in the
      container, Linux aarch64: `make` cloned the MiniLibX at the pinned `f07d00f` and built
      both binaries; **`check_isolation.sh --local` passed on its first real run** (71
      identical objects, 101 files OK); `make -C agent` built the 144,760-byte binary; and
      `check_bridge.py` gave 24 of 24 (rate on `minimal` 73.8-77.7, the maps at 72 and 98
      observations per second).
    - Not rehearsed: `tests/check.sh` in the copy (the same suite passed through
      `dev/dev.sh check`), and everything in the ledger that depends on the owner's machine.
- [x] 🔑 **L2** — Linux checkpoint, phase 2. **Done 2026-10-06, see the note at the end of
  this checkpoint.** Ledger rows 4, 5 and 6.
  On Linux, after `git pull --ff-only`, with `DISPLAY=:99` as in L1:

  ```bash
  make -C agent
  python3 agent/check_bridge.py                # 24 checks, ALL PASSED
  agent/check_isolation.sh --local             # RETIRED 2026-10-06: skip it (was: PASS on all three)
  ```

  - **Report back** (paste the text): the output of `make -C agent` (it should print nothing
    but the compile lines) and all of `check_bridge.py`'s output, which prints its numbers.
  - **Ways it can fail because of the machine and not the code:**
    - `no commands: 75 observations per second on minimal.cub (+-10%, best of 3)` compares
      with the 75 measured on the Mac's container (the container gives 73-78 there). The
      check takes the best of three stretches, so a passing stall of the machine does not
      fail it, but a machine that is slower or faster by more than 10% does. Report the three
      numbers it prints;
    - `2 s of forward moves 2.4 cells on two maps with different frame rates` also fails if
      the two maps happen to run at frame rates under 10% apart on your machine (here they
      were 72-87 and 90-100). It then says so in its message: that is a reason to pick other
      maps, not a bug;
    - `-Werror` turns every compiler warning into an error, and a newer compiler than the
      container's gcc 11.4 may add some. Report the message;
    - the checks need `python3` 3.10 or newer (tested on 3.10.12), the `pty` module (standard
      on Linux) and `DISPLAY` pointing at a running X server.
  - **Done when:** every line passed. The tick records each check's numbers.
  - **Done 2026-10-06**, on the owner's machine (as in L1), commit `8104824`:
    `make -C agent` exit 0 (a 144,760-byte binary), and `check_bridge.py` **24 of 24 PASS**,
    exit 0. Its machine-dependent numbers:
    - the rate on `minimal` (best of three): 78.5, 73.1 and 76.8 observations per second, the
      best within the 75 ±10% band;
    - the fair-timing check: the corridor ran at 76 and `test_map` at 100 observations per
      second, as in the container, and both moved 2.39-2.41 cells in 2 s;
    - the rate on `subject_map`: 82.0 observations per second;
    - the stalled reader kept 399 lines and dropped 180, with the game reaching 7.5 s;
    - `Q` and closing stdin exited with code 0 in 0.02 and 0.00 s;
    - strafing 1.20 cells/s, as walking.
    - **The same seeds spawn the same enemies on the Linux machine as in the Mac's
      container:** seed 7 gave the first enemy at (26.41, 7.35) and seed 8 at (25.66, 7.63) on
      both. Both machines are aarch64, so this does not show it holds across architectures.

## Phase 3 — Python agent and baselines (`agent/`, runs on the host)

- [x] **T4a** — Package skeleton. **Done 2026-10-06, see the note at the end of this task.**
  - **Read:** `plan.md`: "Layout", "SDK facts".
  - **Do:**
    - `agent/pyproject.toml`: uv, Python >= 3.12, `typesafe-sdk==0.7.2`, pytest, the
      `kube-agent` script;
    - `agent/.python-version` with `uv python pin 3.12`. This Mac has 3.12, 3.13 and 3.14, so
      without a pin uv picks whichever it finds, and the SDK's support for 3.14 is not
      verified;
    - the Python entries of `agent/.gitignore`: `.venv/`, `__pycache__/`, `.pytest_cache/`;
    - `src/kube_agent/__init__.py`;
    - `cli.py`, with subcommands that print "not implemented yet";
    - `config.py`;
    - commit `agent/uv.lock`.
  - **Verify:** `cd agent && uv sync && uv run python --version && uv run kube-agent --help &&
    uv run pytest -q`. Python reports 3.12.x, and pytest runs 0 tests or a trivial one.
  - **Commit:** `agent: Python package skeleton`.
  - **Done 2026-10-06:**
    - the Verify commands ran as written: Python 3.12.7, `kube-agent --help` lists
      `run`, `eval`, `spend`, `latency` and `order-check`, and pytest passes 10 tests;
    - the installed `kube-agent run` exits with code 1 and prints
      `kube-agent run: not implemented yet` on stderr, so a stub cannot pass for a success;
    - `uv.lock` pins 21 packages, `typesafe-sdk` at 0.7.2 and pytest at 9.1.1, with no absolute
      path in it (`uv lock --check` passes);
    - the 10 tests were seen failing first (`No module named 'kube_agent.cli'`), and 7
      deliberate breaks were each caught: exit code, message, a dropped subcommand, an optional
      subcommand, a dropped `--map`, a wrong map default and a wrong map path;
    - **a trap in that method:** my first pass of breaks gave 3 wrong counts and a final
      `3 failed` after a restore that `cmp` said was identical. Python's `.pyc` cache is
      invalidated by the source's mtime in seconds and its size, and `subject_map` and
      `no_such_map` have the same length. Deleting `__pycache__` brought back `10 passed`.
      The breaks were rerun with `PYTHONDONTWRITEBYTECODE=1` and the counts then matched what
      each break should hit. Do the same for any later break that keeps a file's size;
    - `config.py` holds only `DEFAULT_MAP`, the one constant in use. The question and the
      config hash arrive with the tasks that use them;
    - not checked here: `uv sync` on the owner's Linux, whose Python is 3.10.12 and so needs
      uv to fetch 3.12 (ledger row 8, L3).
- [x] **T4b** — `bridge.py`. **Done 2026-10-06, see the note at the end of this task.**
  - **Do:**
    - an asyncio subprocess;
    - runner `docker` (`docker exec -i -e DISPLAY=:99 -w /kube kube-dev ./agent/cub3D_agent
      <map> <seed>`) or `local` (`./agent/cub3D_agent <map> <seed>`, cwd = repo root, the
      host's `DISPLAY`);
    - parse `init` and `obs` lines; `send(command_line)`; `close()` sends `Q`, then waits;
    - **record the first fixture, in this commit:** `agent/tests/fixtures/idle_seed7.jsonl`,
      5 s of `subject_map` with seed 7 and stdin open and silent. Record it inside the
      container to a file, so a full pipe cannot drop lines, then copy it out:
      `docker exec -e DISPLAY=:99 -w /kube kube-dev bash -c 'sleep 5 | ./agent/cub3D_agent
      maps/bonus/subject_map.cub 7 > /tmp/idle_seed7.jsonl'` and `docker cp`. The input ends
      after 5 s, so the game exits on its own. Check that line 1 is the init line, that
      `drops` is 0 everywhere and that the file is under 500 KB (about 190 KB [calc]).
  - **Verify:** pytest with a fake child process: a tiny Python script that prints that
    fixture and echoes stdin to a file. Lines parse, commands arrive in order, and `close()`
    ends the child.
  - **Commit:** `agent: game bridge over stdin/stdout (docker and local runners)`.
  - **Done 2026-10-06:**
    - **the fixture** `idle_seed7.jsonl` was recorded in the container as written above: the
      game exited with code 0, and a script checked that line 1 is the init line (33 x 14,
      seed 7), the other 464 lines are obs with consecutive frames 1 to 464, `drops` is 0 in
      all of them, the longest line is 559 bytes, and the file is **155 KB** (the estimate
      said about 190 KB). The first enemy is at (26.41, 7.35), as in the seed note of L2;
    - **the tests:** 30 in the suite (19 new for the bridge and one for `REPO_ROOT`, on top of
      T4a's 10), the final suite run five times in a row with 30 passed each time, about 1 s.
      The bridge ones use `tests/fake_game.py`, a stand-in
      that prints the fixture and echoes stdin to a file, with modes that misbehave (no output,
      garbage, not an init line, a list instead of an object, an unknown line type, a crash
      after init, ignoring `Q`, never printing init). They cover: init parsed, 464 obs in
      order, commands in order with `Q` last, a clean exit, `close()` with 155 KB unread, the
      working directory, each failure message (it names the command and the game's last stderr
      lines), the game terminated after a failed start or a timeout, a newline refused, and
      the two runners' commands;
    - **18 deliberate breaks**, each caught by the test meant for it (no newline, no `Q`, no
      draining, no cwd, ignored exit code, unchecked init and obs types, ignored start timeout,
      uncaught bad JSON and non-object, stderr left out, no terminate on a close timeout or a
      failed start, no newline guard, unwrapped send error, a wrong docker display, a wrong
      local command, an accepted unknown runner), and `bridge.py` restored identical (`cmp`).
      Without draining, 6 tests fail and not only the one aimed at it: the fake blocks on its
      write and never sees `Q`, so the drain is needed everywhere;
    - **two mistakes of mine on the way, both caught:** a test read to the end of the output,
      but a live game keeps stdout open until `Q` (the 20 s guard stopped it, and it now reads
      by count); and my first run of breaks never ran, because zsh does not split a variable
      into words, so its "restored, identical" line proved nothing;
    - **against the real game through the docker runner** (a one-off script, not a test):
      init after 0.13 s and equal to the recorded one; the first obs equal to the recorded one
      (same seed, same player and enemies); `C 1 0 0 0 0 0 0` moved the player 1.211 cells in
      1.009 game seconds, 1.20 cells/s; 119 obs with `drops` 0; `close()` took 0.02 s with exit
      code 0; no game left in the container (`pgrep` found one while it ran, as the control, and
      none afterwards); a map that does not exist raised `BridgeError` naming the command and
      the game's own message (`Error | maps/does_not_exist.cub: No such file or directory`);
    - **not checked here:** the `local` runner, which needs a Linux with the game built: it is
      ledger row 8, L3 (`--runner local`, once T5c exists).
- [x] **T4c** — `features.py` (AC6). **Done 2026-10-06, see the note at the end of this task.**
  - **Read:** `plan.md`: "Conventions", "Semantic features".
  - **Do:** obs + map + short history -> the semantic state dict. **Record the second
    fixture, in this commit:** `agent/tests/fixtures/moves_seed7.jsonl`, the T3c sequence
    (the `script_moves` of `check_bridge.py`, with seed 7), written from `game.lines` of a
    `Game` in the container with a one-off `python3 -c` that imports `check_bridge`. Keep it
    under 500 KB: cut lines if needed, but keep line 1.
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
  - **Done 2026-10-06:**
    - **the fixture** `moves_seed7.jsonl` was recorded in the container with the T3c
      `script_moves` and seed 7: 345 obs, line 1 the init line, frames 1 to 345 consecutive,
      `drops` 0, 3.7 s of game time, 115 KB. The player walks forward (y from 11.50 to 10.36)
      and loses hp (100 to 90) when the zombies arrive, so `being_hit` has real data;
    - **the code:** `features.py` holds pure functions (`relative`, `distance_band`,
      `health_band`, `direction_name`, `in_view`, `open_directions`, `semantic_state`) and
      `HpHistory`, which the episode loop must feed on every observation. 64 tests in
      `test_features.py`, 94 in the suite;
    - **all the checks of the Verify list**, plus the edges the plan leaves implicit: the two
      sides of every band edge, both signs of every sector edge (22.4 / 22.6 degrees and so on),
      `in_view` at 0.58 and 0.59 rad on both sides and with `los` 0, `open_directions` from the
      four headings on a lopsided map and with the map's edge (a wrapped negative index), the
      closed and open door, `close_count` at 2.49 and 2.5, an unknown enemy type (a
      `ValueError` naming it), and a hand calculation on the first recorded obs (the nearest
      grunt is `ahead`, `medium`, at -21.3 degrees, 1.2 degrees from the sector edge);
    - **being_hit against a brute force:** over the 345 recorded obs, the deque-based history
      agrees with a reading that scans every earlier obs; it is false for the first 100 and
      true in some of the rest;
    - **AC6:** over the 464 + 345 recorded states, the longest is **388 characters** (the limit
      is 2,000 and the plan's target 1,500) and none holds a float or a decimal. Caveat: both
      recordings are wave 1, so they hold only grunts and the bands `touching`, `close` and
      `medium`; runners, the boss, the `far` band and the wave strings are covered by the
      hand-made tests only;
    - **30 deliberate breaks**, each caught by the test meant for it: every band and health
      edge, the field of view too wide and too narrow, left and right swapped, the sign of
      `relative`, two sector edges, the right vector, the missing bounds check, closed doors
      made walkable, the hit window edge, a history that never forgets and one that forgets too
      much, `<` turned into `<=` in `being_hit`, `wounded` and `close_count`, the weapon flag
      inverted, `in_view` counting everything, the boss type, the wave total, the unchecked enemy
      type, `nearest` taken as the farthest, the `cornered` threshold, a hard-coded tactic, a
      float leaking into the state and a state past 2,000 characters. `features.py` was
      restored identical (`cmp`);
    - **a mistake of mine on the way, caught before the code existed:** the first draft of the
      heading test ended in `... or True` and an assertion joined with `or`, which could not
      fail. It was replaced by four headings on a lopsided map, each result worked out by hand;
    - **decision recorded in `plan.md`:** `weapon` is `ready` or `reloading`, and `being_hit` is
      false in an episode's first second, when no sample is a full second old.
- [x] **T5a** — `controller.py`. **Done 2026-10-06, see the note at the end of this task.**
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
  - **Done 2026-10-06:**
    - **the code:** `controller.py` has pure functions (`pick_target`, `turn_toward`,
      `should_fire`, `movement_flags`, `reachable`) and `Controller`, with `decide(obs, tactic)`
      (the line wanted now) and `command(obs, tactic)` (that line, or `None` if it is the one in
      force). `features.walkable` became public for it. 73 tests in `test_controller.py`, 167 in
      the suite; the shared hand-made observations moved to `tests/helpers.py`;
    - **the v0.3 trap, seen failing as the task asks:** the test with a target 9.5 cells ahead
      and 0.049 rad off the line (0.466 cells: outside the 0.45 margin, inside the old 0.05 rad)
      was run against the old angular dead zone, and it failed there, together with 3 other
      tests. With the dead zone in cells, the player turns and the test passes;
    - **36 deliberate breaks**, each caught by the test meant for it: the v0.3 rule, the dead
      zone too wide and too narrow, abreast counted as ahead, the tie turning left, each fire
      condition (margin, range, `dot == 0`, weapon, line of sight), the target ignoring line of
      sight, the movement threshold both ways, `w` not normalised, the right vector flipped,
      RETREAT without its depth limit and preferring more steps or the nearest cell, KITE not
      probing behind or never falling back, ENGAGE and RETREAT aiming at nothing, SEARCH aiming
      at the enemy or going for the target, SEARCH failing on the player's own cell, the BFS
      ignoring its depth, the stuck distance both ways, the stuck window, the stuck side, stuck
      while holding still, the unsticking strafe added and not replacing, repeated lines sent,
      the last line never stored, the first all-zero line sent, and an unknown tactic accepted.
      `controller.py` was restored identical (`cmp`);
    - **three gaps found in my own tests before the breaks** and closed: abreast with a hair of
      offset, the controller's use of the depth limit (the BFS test alone did not show it), and
      that the unsticking strafe replaces the path's strafe;
    - **on the real recordings** (464 + 345 obs, all four tactics): no exception, 0 invalid
      lines, and `decide()` takes 0.003-0.043 ms on average and 0.106 ms at most. That is small
      because of the map, see the next point;
    - **a finding about the map, measured:** from the start cell (26, 11) the search reaches
      **21 of the map's 195 walkable cells**, 7 steps at the deepest. The start is a small room
      whose exit is a closed door `D` at (23, 8), and the bridge has no flag to open it (the
      game opens doors with a key, `toggle_door`), so that room is the agent's arena. The three
      wave-1 zombies are inside it. I did not check whether zombies cross closed doors or where
      waves 2 and 3 spawn;
    - **decisions where `plan.md` was silent** are written in its "Controller (exact)": the
      initial `C` state, the stuck strafe's side and replacement, and SEARCH's goal;
    - **not checked:** how the controller plays a whole episode, which needs T5b and T5c.
- [x] **T5b** — `policies.py`: idle and scripted. **Done 2026-10-06, see the note at the end of this task.**
  - **Verify:** pytest on the scripted rules in `plan.md` ("Controller (code, every
    observation)", "Scripted policy"), one case per rule. The scripted policy decides on Jev's
    schedule (every 0.5 s and on events), not on every obs. The initial tactic is ENGAGE.
    Idle never sends a command.
  - **Commit:** `agent: idle and scripted policies`.
  - **Done 2026-10-06:**
    - **the code:** `policies.py` holds `DecisionSchedule` (when a decision is due),
      `scripted_tactic` (the four rules as a pure function), `IdlePolicy` and `ScriptedPolicy`.
      A policy gets every observation through `step(obs)`, answers with a decision row
      (`t`, `state`, `tactic`, `applied`: the fields `plan.md` "Logs" gives for every policy)
      when it decided on that observation, and `None` otherwise; its `tactic` is the one in
      force. Idle's `tactic` is `None`, which tells the episode to send the game nothing. 27
      tests in `test_policies.py`, 194 in the suite;
    - **one case per rule**, plus the precedence between them: low health with something close
      is RETREAT even when it is behind the player (health 29) and KITE at 30; something close
      beats something in view; low health with nothing close is ENGAGE, not RETREAT; and a
      hidden enemy or none at all is SEARCH;
    - **the schedule:** the first observation decides; then every 0.5 s since the last decision
      (`>=`: exactly 0.5 s counts); a late decision moves the next one with it; a new wave and a
      health band drop each decide at once and only once; a rising band is not an event, but a
      later drop is; and a decision made for an event restarts the 0.5 s. Over 100
      observations 10 ms apart (one second) it decides twice, at 0.0 and at 0.5;
    - **over both recordings:** every decision row is under 2,000 characters with no float in
      its state, and the number of rows is every 0.5 s plus a few events (AC6 on the decision
      rows, the way T5c's logs will be checked). On the recordings the policy plays ENGAGE while
      the three zombies approach and KITE once they are close, with `being_hit` true when hp
      drops. Both players there are idle, so that says nothing about how well the policy plays;
    - **19 deliberate breaks**, each caught by the test meant for it: the interval both ways and
      a strict `>`, the first observation not deciding, a new wave and a health drop ignored, a
      rise counted as a drop, an event not restarting the timer, rule 1 removed or on the wrong
      band, "close" needing two enemies, ENGAGE on any enemy left, the default turned into
      ENGAGE, the initial tactic, the history fed only at decisions, the row showing the new
      tactic, not applied, a zero time, and idle with a tactic. `policies.py` was restored
      identical (`cmp`);
    - **two slips of mine, caught:** a float trap in my own test (`1.2 - 0.7` is not exactly 0.5,
      so I used 0.75 and 1.25), and a gap that the first run of breaks found: an event decision
      that did not restart the timer passed all 193 tests, and now has its own test. Three of
      those breaks first showed "not caught" only because I had mistyped the test name I
      expected; I reran them with the right name and the right test failed;
    - **a correction in `plan.md`:** I had written that the scripted policy and the controller
      need `being_hit`. They do not (the controller never reads it and the rules do not use
      it). The history is fed on every observation because a state is built only at a decision
      and a drop between two decisions must still count; there is a test for that case;
    - **not checked:** the policies in a whole episode, which is T5c.
- [x] **T5c** — `episode.py` and `kube-agent run` (AC14). **Done 2026-10-06, see the note at the end of this task.**
  - **Read:** `plan.md`: "Logs", "Runtime expectations".
  - **Do:**
    - one episode ends on `state != 0` (win or lose) or at `--max-seconds` (default 180),
      then sends `Q`;
    - `--map` (default `maps/bonus/subject_map.cub`) and `--runner` (default `docker`);
    - write `agent/runs/<id>/` exactly as `plan.md` "Logs" describes: `result.json`,
      `episode.jsonl`, and `decisions.jsonl` with the scripted policy's decisions too (idle's
      file is empty). Kills are the enemies that die (this said "the enemies that disappear
      within the same wave" until T5c measured that it misses the last enemy of each wave: see
      `plan.md` "Logs");
    - `stalls` counts gaps above 100 ms between observations handled by the controller, timed
      with the host's monotonic clock. Unit-test the counter with a fake loop that blocks for
      0.2 s every 0.5 s: it must count them;
    - `run` ends with its one-line summary.
  - **Verify:**
    - run idle and scripted on seeds 1-5 through the docker runner. Every run writes its
      three files with the documented fields;
    - **the scripted median survival is longer than idle's**;
    - AC14: `git status --porcelain agent/runs` lists the 10 new folders;
    - append the numbers to the research as **R11** ("Baselines on dev seeds 1-5").
  - **Commit** (with the 10 runs): `agent: episode runner and first baselines (dev seeds 1-5)`.
  - **Done 2026-10-06:**
    - **the code:** `episode.py` has `StallCounter`, `Tally`, `play()` (the loop of one episode)
      and `run_episode()` (the folder, the three files, `result.json` even when the episode
      fails, never overwriting a folder); `cli.py` has the real `run` (`--policy` and `--seed`
      required, `--map`, `--runner`, `--max-seconds`); `config.py` gained `RUNS_DIR`,
      `DEFAULT_MAX_SECONDS`, `DECISION_INTERVAL` (moved from `policies.py`) and a first
      `config_sha256()`; `policies.py` gained `make_policy`. 234 tests in the suite against 194
      before: 40 new (30 for the episode, 6 for the CLI, 2 for config and 2 for policies);
    - **44 deliberate breaks**, each caught by the test meant for it. Three were missed the
      first time and are now caught: a failed early end that passed because `close()` raised the
      error instead of `play()`; position rounding that could not fail because the recorded
      player is still at (26.5, 11.5); and a wave number going backwards. One more was caught
      but **leaked**: with `--seed` made optional on purpose, a CLI test started a real episode
      and left an `error` run folder in `agent/runs/`. An automatic guard now makes any CLI
      test that reaches `run_episode` fail first, and the same break then creates nothing;
    - **the stalls counter (AC8)**, as the task asks: with an injected clock, and with a real
      loop that blocks 0.15 s three times, which it counts. A slow controller (a block every 40
      calls) shows up in `result.json`'s `stalls`;
    - **the 10 runs**, through the docker runner and the real CLI, on seeds 1-5 (R11 has the
      table): `idle` lost all 5 in 6.6-8.2 s (median 7.26 s) with 100 damage; **`scripted` won
      all 5, in 11.0-14.1 s (median 12.84 s), with 8 kills and 0 damage each**. All 10 exited 0,
      left no game running in the container, and the 130 decision rows of the scripted runs hold
      states of at most 392 characters with no float (AC6 on the real log);
    - **the Verify list:** every run has its three files with the documented fields (checked by
      a script over the 10 folders); the scripted median survival is longer than idle's (12.84 s
      against 7.26 s), **but that comparison says little: a scripted episode ends because it
      won**, so its "survival" is the time to win; AC14: the folders are new in git (see the note
      below on what `git status --porcelain` prints);
    - **two counting errors of mine, found by reconciling the first real run** (6 kills in a won
      game of 8 enemies; 110 damage from 100 hp): kills missed the last enemy of each wave
      (`check_wave_advance` starts the next wave only when none is left, on the same frame), and
      damage counted hp below zero. Both fixed with tests that failed first (`6 == 8`), and
      written into `plan.md` "Logs" as a deviation from this task's earlier text;
    - **same seed, not the same episode:** three scripted runs on seed 1 took 14.1, 16.1 and
      14.1 s to win. The game runs on real time, so only the spawn is fixed by the seed;
    - **stalls on the Mac:** 2 in the 5 idle episodes and 7 in the 5 scripted ones (1, 1, 1, 1
      and 3), about one per episode. I did not look for their cause. T7's AC8 margin ("about as
      often as scripted") should start from that baseline and not from zero;
    - **AC14 and git:** while `agent/runs/` is itself new, `git status --porcelain agent/runs`
      prints one line, `?? agent/runs/`. Each folder is listed once the directory is tracked,
      as from the next run on, and `-uall` lists them from the start;
    - **one stray folder, deleted at the owner's request:** `20261006T165137Z-idle-s1-darwin`
      was the failed run from the leaking break (Docker was off: `outcome: error`, no
      decisions, 671 bytes, $0). It was never committed. `plan.md` says never to delete a run
      because a run's cost would leave the spend ledger; this one had no cost, and the owner
      asked for it to go. `agent/runs/` now holds exactly the 10 runs, all tracked;
    - **not checked:** the `local` runner (L3, on the owner's Linux), and anything with Jev.
- [x] 🔑 **L3** — Linux checkpoint, phase 3. **Done 2026-10-06, see the note at the end of
  this checkpoint.** Ledger rows 8 and 9. First re-run what L1 and
  L2 settled, if anything changed since. On Linux, after `git pull --ff-only`, with
  `DISPLAY=:99` as in L1:

  ```bash
  make -C agent
  cd agent && uv sync && uv run pytest -q      # green
  uv run kube-agent run --runner local --policy scripted --seed 1
  git add runs && git commit -m "agent: Linux checkpoint L3 run" && git push
  ```

  - The run must write its three files and print its summary line. This is AC13's first
    check.
  - **Nothing in the game or the C bridge changed since L2** (checked with `git diff --stat
    8104824..HEAD` over `sources`, `includes`, the Makefiles, `libft`, `maps`, `files`,
    `tests` and `agent/check_bridge.py`: empty), so L1 and L2 are not repeated. `make -C
    agent` stays in the commands because the agent needs the binary.
  - **Expected, from the Mac (R11):** 234 tests pass in about 5 s. `scripted` on seed 1 should
    win in roughly 11-16 s with 8 kills and no damage; `result.json` says `machine: linux`
    and `runner: local`. The run's folder is named `...-scripted-s1-linux`.
  - **Report back** (paste the text): the output of `uv sync` (which Python it picked, and
    whether `typesafe-sdk` 0.7.2 installed), the `pytest` summary, and the run's summary line.
    Machine-dependent: the `uv` download of Python 3.12 needs the network.
  - **Ways it can fail because of the machine and not the code:**
    - `uv sync` has to fetch Python 3.12, because the owner's Linux has 3.10.12;
    - `DISPLAY` must point at the running Xvfb (`:99`), in the same terminal;
    - the game runs on real time, so a slower machine can lose or win differently: report the
      outcome and the `stalls` number, which was about 1 per episode on the Mac;
    - two tests use real sleeps (the stall counter and the slow controller) and count at least
      a number of stalls, so a loaded machine can only add stalls, never remove them.
  - To watch it play instead, use the real display: `DISPLAY=:0 uv run kube-agent run
    --runner local --policy scripted --seed 2`. Not verified yet; L3 is where we find out.
  - **Done when:** pytest is green and the run's `result.json` exists. The tick records the
    test count and the run's summary line.
  - **Done 2026-10-06**, on the owner's machine (UTM, aarch64, Ubuntu 22.04.5), from commit
    `3711261`. Nothing failed, and the owner ran every step:
    - `make -C agent` linked without a warning and gave a binary of **144,760 bytes**, the
      same as in L2 and in the Mac's container;
    - `uv sync`: **CPython 3.12.11** (the Mac has 3.12.7; the `3.12` pin allows both) and the
      same 19 packages as `uv.lock`, with `typesafe-sdk==0.7.2` and `pytest==9.1.1`;
    - `uv run pytest -q`: **234 passed in 3.87 s** (4-5 s on the Mac);
    - **the first run of the `local` runner anywhere**, on the virtual screen `:99`:
      `scripted s1: win after 14.0 s (wave 3, 8 kills), 29 decisions, 29 applied, spend
      $0.0000`. Its `result.json` says `machine: linux` and `runner: local`, 0 damage, 0
      drops and **0 stalls**, and has **the same `map_sha256` and `config_sha256` as the Mac's
      runs**. The owner committed and pushed it from the Linux (`3a79306`); checked from the
      Mac: 3 files, 29 decision rows matching the result, longest state 387 characters, no
      float (AC6 on this machine's log);
    - **row 9, the real display:** three episodes of `scripted` on seed 2 with
      `DISPLAY=:0`. The owner **saw the game window** on the desktop and it **ran
      smoothly**. All three won with 8 kills and 0 stalls: 11.36 s with no damage, 15.04 s
      **with 10 damage**, and 16.44 s with no damage (pushed as `50dd885`);
    - **what the four Linux episodes add to R11:** four wins in four; the same seed 2 took
      11.4, 15.0 and 16.4 s (a spread of 45% of the shortest [calc]), which backs "same seed,
      not the same episode"; and `scripted` is **not untouchable**: one of the four took 10
      damage, where the five Mac runs took none;
    - **ledger:** rows 8 and 9 are closed. Row 10 (L4) is the only one still open, and rows 7
      and 11 stay closed as not needed.

## Phase 4 — Jev in the loop

- [x] **T6** — `jev_client.py` and `kube-agent spend` (AC8, AC10). **Done 2026-10-06, see the note at the end of this task.**
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
  - **Done 2026-10-06:**
    - **what `RetryPolicy.timeout` means** (the task asked for it here; read in `retry.py` and
      tested): it is the total budget for one SDK call, the first attempt and the waits
      included, applied with tenacity's `stop_before_delay`. It is checked **between** attempts
      and never interrupts one in flight, and it stops a retry whose wait would reach the
      budget. So a `Retry-After: 30` against a 3 s budget makes one request and returns in 0.00
      s. The client's own `timeout` is a different thing: an `httpx2.Timeout` that applies one
      number to connect, read, write and pool each (the transport sees four 1.5s), not to the
      attempt as a whole. The only hard bound on a call is `asyncio.timeout`, which I added.
      Both are in `plan.md` "SDK facts";
    - **today's facts were checked first, at the owner's request** (public pages, no key, no
      spend; R2 has the details): the docs, the skill and the SDK are as the context says, the
      only model is `jev-1.13.0`, OpenRouter's `typesafe/jev-1.13` still has the one endpoint
      `TypeSafe | typesafe/jev-1.13-20260917` at $0.042 per Mtok, nothing newer exists, and
      `typesafe-sdk` 0.7.2 is still the latest. **A real call cannot be checked without
      paying**, so that the answering model is the expected one is T6b's job;
    - **the code:** `jev_client.py` (`JevClient`, `JevResult`, `KeyMissing`) and `ledger.py`
      (`read_ledger`, `require_budget`), `config.TOTAL_BUDGET_USD`, and `kube-agent spend`. A
      call returns a `JevResult` (`answers`, `model`, `input_tokens`, `cost`, `latency_ms`,
      `request_id`, `error`; `to_row()` is plain JSON) and **never raises for an API failure**;
      a cancellation does pass through, because the policy cancels a stale request. 56 new
      tests (19 ledger, 33 client, 4 `spend`), 289 in the suite, none touching the network;
    - **the Verify list:** 429, then 529, then 200 is retried in 3 requests while a ticker keeps
      ticking through the waits; when every attempt fails nothing is raised and the row has an
      `error`; a cap of $0.0001 lets two $0.00006 calls through and refuses the third, says why
      in the row and once in the log, and a cap of 0 makes no call; a ledger of ten $0.10 rows
      refuses to start; a missing request id does not raise;
    - **three more facts found while testing**, none in the task text: an API error's text
      includes the body the server sent, so it can repeat the key (the client replaces the key
      with `[key]`, tested with a server that echoes it); a cost of `NaN` or `Infinity` falls
      back to the price per token; and the per-phase timeout reaches the transport as four
      equal numbers;
    - **41 deliberate breaks**, each caught by the test meant for it: 12 in the ledger, 26 in
      the client (the model, the URL, the warnings, each way of reading a cost, the request id,
      the three failure paths, the key scrub, the cap, the key and ledger at start, the latency
      and the retry settings) and 3 in `spend`. One looked uncaught: replacing `fsum` with
      `sum`, because since Python 3.12 the built-in `sum` is compensated and gives 1.0 for ten
      0.1s. A naive `+` loop (0.9999999999999999) is caught by 3 tests;
    - **my slips, caught:** a test ended in a tautology that only used an import, the response
      JSON was parsed twice, and four branches had no test (the error text cut, the timeout
      reaching the transport, the default retry settings and a non-finite cost);
    - **the real ledger** (`kube-agent spend`): `$0.000000 of $1.00 used, $1.000000 left
      (paid calls: 0, decisions files read: 14)`, and a `find` agrees on the 14 files and finds
      no `cost` key in them;
    - **not checked:** any real call, the real `usage.cost` field (it is in the `libros`
      notes, not seen again here), cancellation over a real network, and the tests on Linux
      (they will run at L4).
- [ ] **T6b** — The first real calls, and Jev's latency (the unknown in R2).
  - **Do:** `kube-agent latency --n 50` sends one state recorded from a fixture 50 times,
    sequentially.
  - `git pull --ff-only`, then check `kube-agent spend` first. This costs about $0.003.
  - Load the key as shown in `START_HERE.md`.
  - **Verify:**
    - 50 rows, each with `model`, `input_tokens`, `cost` and `latency_ms`;
    - the answering model is `typesafe/jev-1.13-20260917`. 🛑 **If it is not, stop and tell the
      owner.**
  - Append **R12** to the research: latency p50/p95, tokens per call and cost per call. If
    p95 > 500 ms, switch the policy to event-only decisions (`plan.md`, "Risks") before T7,
    and note it.
  - **Commit** (with the run): `agent: measured Jev latency and cost (R12)`.
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
    - `kube-agent run --policy jev --seed 1 --max-seconds 60` completes. Pull, load the key as
      `START_HERE.md` shows, and check `spend` first (about $0.007 [calc]);
    - AC9: every decision row has the AC9 fields;
    - AC6: the T4c check (under 2,000 characters, no float) passes on every state in this
      run's `decisions.jsonl`;
    - AC8: run scripted on seed 1 with `--max-seconds 60` as well. Jev's `stalls` may exceed
      scripted's by at most 5 (**ASSUMPTION**: a margin for noise). A loop blocked by each
      call would add one stall per decision, about 120 in 60 s [calc].
  - **Commit** (with both runs): `agent: Jev tactic policy in the game loop`.
- [ ] 🔑 **L4** — Linux checkpoint, phase 4 (one paid run, about $0.003 [calc]). Ledger row
  10: first create the key file on Linux (`START_HERE.md` 2b, step 3, the `read -s` variant:
  never paste the key into the chat). On Linux, after `git pull --ff-only` (the spend ledger
  must include the Mac's runs), with `DISPLAY=:99` as in L1:

  ```bash
  make -C agent
  cd agent && uv sync && uv run pytest -q      # green
  uv run kube-agent spend                      # what is left of $1.00
  ( set -a; . ~/jev/libros/.env; set +a; uv run kube-agent run --runner local --policy jev --seed 2 --max-seconds 30 )
  git add runs && git commit -m "agent: Linux checkpoint L4 run" && git push
  ```

  - The parentheses keep the key inside that one command. Never `echo` it.
  - **Done when:** pytest is green, no model warning was printed, and the summary line shows
    decisions applied and a spend above $0. The push carries the run's cost to the Mac's
    ledger.

## Phase 5 — Tuning, evaluation and close

- [ ] **T8** — Tuning on development seeds 1-20 only, then the freeze.
  - **Read:** research R5 (Jev's weak points); `CONTEXT.md`, "Jev in two minutes".
  - **Do:**
    - run the Jev policy on dev seeds and look at `decisions.jsonl` and `episode.jsonl`:
      where does the tactic look wrong, and where are episodes won or lost?
    - **option-order check** (R5, "Choice option order": `jev-1.13` leans toward the first
      option of a Choice). `kube-agent order-check --n 100` takes at least 100 states already
      logged in `decisions.jsonl` on dev seeds. It asks each one twice through `jev_client`,
      once in the current order and once with the options reversed (same criteria text), and
      logs both answers under `agent/runs/order-check-<UTC date-time>-<machine>/`. Report how
      often the `choice` differs, and how often the first-listed option wins in each order.
      The spend counts against the $1 ledger: 200 calls times the tokens per call measured in
      R12, about $0.011 at 1,300 tokens [calc].
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
  - **Commit** (with every tuning run): `agent: freeze the Jev policy config after dev tuning`.
- [ ] **T9** — The final evaluation on test seeds 101-120 (AC11, AC12).
  - **Do:** `kube-agent eval --seeds 101-120 --policies idle,scripted,jev` (in the
    background; up to about 2 h) writes `agent/runs/eval-<UTC date-time>-<machine>/`, one
    folder per episode plus `report.md`. Pull and check `spend` first.
  - **Verify:**
    - AC11: the report shows, per policy:
      - n, and wins with a Wilson 95% interval;
      - survival median/IQR and waves;
      - the share of time in each tactic, in wins and in losses;
      - for Jev, $/episode and latency p50/p95.

      Its config hash equals `frozen.json`'s.
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
  - Append the report's summary to the research as **R14**.
  - 🛑 **Report the results to the owner as they are.** If scripted beats Jev, say so.
  - **Commit** (with the whole evaluation folder): `agent: final evaluation on test seeds
    101-120`.
- [ ] **T10** — Regression on the Mac.
  - **Verify:** `check_bridge.py` passes in the container, `dev/dev.sh check` prints
    `ALL PASSED`, and `cd agent && uv run pytest -q` is green. (`check_isolation.sh` was
    dropped from here on 2026-10-06.)
  - **Commit:** `specs: spec 002 complete`, with `CONTEXT.md` "Status" updated.
- [ ] 🔑 **L5** — Linux checkpoint, the final one. **Every ledger row that is still open**:
  nothing may remain in the ledger when the spec is closed (rows 7 and 11, x86_64, were closed
  on 2026-10-06). On Linux, after `git pull --ff-only`, with `DISPLAY=:99` as in L1:

  ```bash
  uname -m
  make && make bonus && bash tests/check.sh    # ALL PASSED
  make -C agent && python3 agent/check_bridge.py
  cd agent && uv sync && uv run pytest -q
  uv run kube-agent run --runner local --policy scripted --seed 3
  git add runs && git commit -m "agent: Linux checkpoint L5 run" && git push
  ```

  - **Done when:** every line passed.
- [ ] **T11** — (optional, only if the owner asks) Watch or record an episode: on a Linux
  desktop with `DISPLAY=:0` (see L3); on the Mac, `ffmpeg -f x11grab` in the container, or
  `x11vnc` plus macOS Screen Sharing. None of these is verified yet.
- [ ] 🛑 **T12** — The final push, only when the owner asks.
