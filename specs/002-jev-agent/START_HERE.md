# START HERE — implementing spec 002 (Jev plays cub3D_bonus)

> For the model (or person) that implements this spec. It is self-contained: everything
> decided and verified so far is in `specs/`, so nothing needs to be rediscovered. Written
> 2026-09-29; updated 2026-10-03 (T8 option-order check, new Jev rate limits) and 2026-10-05
> (every task re-checked against the code; then the owner's decisions 5-8: `sources/jev/`,
> Linux checkpoints, kept logs, harder maps later; `tasks.md` v0.6).

## 1. The mission in seven lines

1. Build `cub3D_agent`, a **separate** binary of the game. Every frame it prints the state as
   one JSON line on stdout, and it takes movement/turn/fire commands on stdin.
2. Build a Python agent on the Mac that reads those lines, turns them into a state **in
   words**, and drives the player. **Code aims, fires and moves.**
3. **Jev** (TypeSafe's decision model, through OpenRouter) only picks the tactic: ENGAGE, KITE,
   RETREAT or SEARCH. It is asked every 0.5 s, and its confidence is used.
4. Compare Jev against an idle player and a hand-written rule policy on the same seeds, and
   report it honestly, with its cost.
5. **The game is no longer handed in at 42** (the owner, 2026-10-06), so it is no longer
   protected: it may change on this branch when a task needs it, keeping `tests/check.sh`
   passing. Spec 001 polished it; the agent is still built as new files by design.
6. **Keep every run's logs in git.** The owner studies them to see how the game gets beaten,
   and may later add obstacles where a pattern shows.
7. **Develop on the Mac (Colima); prove each phase on Linux.** The owner re-runs each phase's
   checks natively on Linux before the next phase starts.

## 2. Where you are

- **Branch:** `feature/jev-agentv1`, the only working branch (since 2026-10-06).
  `feature/jev-agent` (`ad4244a`: spec 001 plus a strafing fix of 2026-10-05) is the old base and
  is not touched again.
- **Done (2026-10-06): T0 to T3e, that is phases 1 and 2.** The C bridge `cub3D_agent`
  (`sources/jev/`), its 24 checks in `agent/check_bridge.py`, and **L1 and L2 passed on the
  owner's Linux** (UTM, aarch64, Ubuntu 22.04.5).
- **Phase 3 has started: T4a and T4b are done.** T4a is the Python package skeleton
  (`agent/pyproject.toml`, `uv.lock`, `src/kube_agent/` with `cli.py` and `config.py`). T4b is
  `bridge.py`, the pipe to the game, with its first fixture; 30 tests in all.
- **Next: T4c**, then T5a to T5c. Phase 3 ends with checkpoint L3 on the owner's Linux: stop
  there and list every open row of the Linux ledger in `tasks.md`.
- **Already in the repo:**
  - the game;
  - `dev/dev.sh`, a Linux container on macOS;
  - `tests/check.sh`, the 10 acceptance checks of spec 001;
  - the C bridge and its checks;
  - the specs.
- **Not started:** everything in `specs/002-jev-agent/tasks.md` from T4c on.
- **The container may be off.** `colima status` tells; `colima start && dev/dev.sh up` brings it
  back (section 5).

## 2b. On a new machine (do this once)

The repo carries everything **except the API key**, which must never be in it.

1. **Tools.** On the original Mac they came from Homebrew:

   ```bash
   brew install colima docker uv
   ```

   That gave colima 0.9.1, docker 28.5.0 and uv 0.8.24; Lima comes in as a Colima dependency.

   **On a Linux machine** (the owner's, for the checkpoints L1-L5), everything runs natively,
   with no Docker. On Ubuntu or Debian:

   ```bash
   sudo apt install -y build-essential git curl libx11-dev libxext-dev libbsd-dev
   sudo apt install -y zlib1g-dev xvfb xdotool valgrind
   curl -LsSf https://astral.sh/uv/0.8.24/install.sh | sh     # the Mac's uv version
   export PATH="$HOME/.local/bin:$PATH"                       # uv is installed there
   uv tool install --force norminette==3.3.60                 # the container's version
   ```

   - `--force` is there because a machine can already hold an older `norminette`. On
     2026-10-06 the owner's had 3.3.59 (an old `pip --user`), `uv` printed `Executable already
     exists` and `norminette --version` kept answering 3.3.59. Check with
     `norminette --version`: it must say 3.3.60, the version the container and the checks use.

   - On 2026-10-06 the `uv` 0.8.24 installer printed `everything's installed!` but did not
     create `~/.local/bin/env`, so `source $HOME/.local/bin/env` failed. The `export` line
     is what makes the terminal find `uv` and, later, `norminette`. A terminal opened after a
     new login may find them by itself; one opened before does not.

   - The apt line is split in two on purpose. On 2026-10-06 the single long line was cut in
     two when the owner pasted it into a terminal: the second half ran as a command
     (`zlib1g-dev: command not found`) and four packages were never installed. **Keep every
     command short enough to paste in one piece.**
   - The packages are the image's (`dev/Dockerfile`), minus the screenshot tools.
   - The `uv` installer URL with a version is the official form (docs.astral.sh, checked
     2026-10-05, and this URL answered 200).
   - Python 3.12 comes through `uv` (`agent/.python-version`). `check_bridge.py` uses the
     system `python3`, which must be 3.10 or newer.
   - The list has not been run on a fresh Linux yet; L1 is where it is tried.
2. **The branch:**

   ```bash
   git clone -b feature/jev-agentv1 git@github.com:CristianYepes/Kube.git
   ```

   Or run `git fetch && git checkout feature/jev-agentv1` in an existing clone. `main` does
   not have any of this.
3. **The key**, at the same path the docs use, so nothing else changes. Copy the OpenRouter
   key in the browser first, then, on macOS:

   ```bash
   mkdir -p ~/jev/libros && printf 'OPENROUTER_API_KEY=%s\n' "$(pbpaste | tr -d '[:space:]')" > ~/jev/libros/.env && chmod 600 ~/jev/libros/.env && pbcopy < /dev/null
   grep -qE '^OPENROUTER_API_KEY=sk-or-v1-[0-9a-f]{64}$' ~/jev/libros/.env && echo "key file OK"
   ```

   On Linux:

   ```bash
   read -s -p "OpenRouter key: " k && mkdir -p ~/jev/libros && printf 'OPENROUTER_API_KEY=%s\n' "$k" > ~/jev/libros/.env && chmod 600 ~/jev/libros/.env && unset k
   ```

   **The key never goes into the chat,** and it is never pasted as a command argument.
4. **Start:** on the Mac, `colima start`, then `dev/dev.sh up`, then `dev/dev.sh check`. That
   is task T1. On Linux, start with checkpoint L1 in `tasks.md`.

These steps were written from the original Mac and have not been run on a fresh machine: if
one fails, fix it and correct this section in the same commit.

## 3. Reading order (about 20 minutes; do not skip)

1. `specs/CONTEXT.md`: the goal, "Jev in two minutes", the game's rules, the hard rules.
2. `specs/002-jev-agent/spec.md`: requirements FR1-FR15, acceptance criteria AC1-AC14,
   "Decisions" 1-8.
3. `specs/002-jev-agent/plan.md`: **"Implementation decisions" is binding.** It covers the
   layout, build, bridge, the sign conventions with a worked example, the exact features and
   controller, the SDK facts, the key and the budget.
4. `specs/002-jev-agent/tasks.md`: **your checklist.** Tick it as you go.
5. As needed: `specs/research-2026-09-28.md`. R2 is Jev access, R4 the game's numbers, R5
   Jev's weak points, R7 the architecture choice, R8-R10 the build, memory and fps facts.

## 4. Hard rules

1. **Work on `feature/jev-agentv1` only.** `feature/jev-agent` (`ad4244a`) stays as it is and
   is not touched again. The old rule that only `agent/`, `sources/jev/`, `specs/` and
   `CLAUDE.md` may change is **retired** (2026-10-06): the game was protected because it was
   handed in at 42, and it no longer is. Ask before changing it, and keep `tests/check.sh`
   passing. `agent/check_isolation.sh` is retired too: it would fail on purpose after such a
   change.
2. **English** in every file, comment, identifier and commit message. Talk to the owner in
   **Spanish**.
3. **YAGNI.** Build only what a task needs. No placeholders, no speculative options.
4. **C in `sources/jev/` passes `norminette` today; keep it so when it is easy.** It is no
   longer a gate (2026-10-06): the 42 norm does not bind. Run it rather than guess.
5. **The API key:** never print, log, commit, or pass it to Docker. Load it only into the
   command that uses it (section 5).
6. **Budget:** $1 in total for every Jev call of this spec. Check `kube-agent spend` before any
   paid run. 🛑 Stop if a run would cross it.
7. **Verify, do not assume.** A number you computed is labelled a calculation. A result that
   cannot be true (0 fps, an impossible distance) means the instrument is broken: fix it
   before reporting. A zero proves nothing until you have seen the same check find something.
8. **One commit per task,** with the message given in `tasks.md`. **Never push** unless the
   owner asks.
9. **Runs are kept.** Every run's folder under `agent/runs/` is committed with its task, and
   no run is ever deleted: the logs are the owner's material, and their costs are the ledger.
10. **Phases end on Linux.** After a phase's last task, stop (🛑). The owner asks for the push
    and runs the phase's Linux checkpoint. The next phase starts only after it passes.

## 5. Environment (commands verified on 2026-09-29)

The Mac cannot build this X11 MiniLibX, so the game builds and runs in a Linux container
(Colima + Docker, Ubuntu 22.04 aarch64, a virtual display `:99`).

```bash
colima status || colima start                 # the Linux VM; stop it later with: colima stop
dev/dev.sh up                                 # builds image kube-dev, starts container kube-dev + Xvfb :99
dev/dev.sh check                              # sync + build + the 10 checks of spec 001 (~2.5 min)
dev/dev.sh sync                               # mirror the working tree into /kube (wipes all but minilibx-linux/)
docker exec kube-dev make -s -C agent         # build agent/cub3D_agent (after every sync)
docker exec -i -e DISPLAY=:99 -w /kube kube-dev ./agent/cub3D_agent maps/bonus/subject_map.cub 7
dev/dev.sh down                               # remove the container
```

From T3c on, `cub3D_agent` quits on EOF. A run "with no input" keeps stdin open without
writing to it. `sleep 10 | ./agent/cub3D_agent ...` does that, and it ends the run cleanly
after 10 s.

The Python agent runs on the Mac, from `agent/`, with `uv` (0.8.24 is installed):

```bash
cd agent && uv sync && uv run pytest -q
set -a; . ~/jev/libros/.env; set +a; cd agent && uv run kube-agent run --policy jev --seed 1
```

The second line loads the owner's OpenRouter key into that shell only. Every Bash call is a
new shell, so load it in the same call that needs it. Never `echo` it.

**On Linux** the same commands run without the container:
- `make -C agent` builds the binary;
- `--runner local` replaces the default `--runner docker`;
- the virtual display is started once per shell:
  `Xvfb :99 -screen 0 1280x720x24 & export DISPLAY=:99`.

The checkpoints in `tasks.md` (L1-L5) list the exact commands.

## 6. Workflow

0. At the start of a session, `git pull --ff-only`. The owner may have pushed Linux runs, and
   the spend ledger needs them.
1. Take the first unticked task in `tasks.md` and read its **Read** list.
2. Implement only that task. Write its tests first and see them fail; a check never seen
   failing proves nothing.
3. Run its **Verify**. If it fails, find out why; do not loosen the check to make it pass.
4. Tick it: `[x]` plus `Done <date>:` and the evidence (numbers).
5. Commit with the task's message, including the runs it made.
6. Give the owner a two-line status in Spanish, then take the next task.
7. **At the end of a phase,** stop. Give the owner the phase's summary, the checkpoint's
   commands, and **every open row of the "Linux ledger" in `tasks.md`**, not only the ones
   due: the owner asked that nothing be forgotten. Wait for the push request and then for the
   Linux results. Tick the checkpoint and the ledger rows with those results in the next
   commit. Anything a check cannot settle off the owner's machine goes into the ledger the
   moment it is found.

## 7. When to stop and ask the owner (🛑)

- the tasks marked 🛑: T6b if the answering model is unexpected, T8 before freezing, T9's
  results, T12 push;
- the end of every phase: the Linux checkpoints L1-L5 (🔑, run by the owner);
- a check fails and you do not understand why;
- a task seems to need a path outside the allowed ones (rule 1);
- spend would cross $1, or a decision is not covered by `plan.md`.

## 8. Map of what you will touch or read

| Path | What it is |
|---|---|
| `sources/render/game_loop.c:15-54` | the bonus frame to copy into `agent_frame.c` (`tick_clock` + `game_loop`) |
| `sources/mlx_loop_and_hook/mlx.c:17-27` | the bonus `loop()` to copy without key and mouse hooks |
| `sources/main.c:15-33` | `main` to copy into `agent_main.c` (plus the seed) |
| `sources/movement/input_bonus.c` | what the Up key does to fire: `data->fire = 1; fire_shotgun(data);` |
| `sources/movement/player.c` | movement and turning by `dt` (spec 001); `is_wall` |
| `sources/bonus/mod/utils.c` | `has_los(data, x, y)`: line of sight, used for `los` in obs |
| `sources/bonus/mod/combat.c` | the hitscan rule the controller mirrors |
| `sources/bonus/mod/waves.c` | waves, enemy types and spawn hp; `lcg_next(&data->seed)` |
| `includes/cub3d.h` | `t_data` fields: `player`, `enemies`, `enemy_count`, `wave`, `player_hp`, `game_state`, `weapon.state`, `seed`, `map` |
| `tests/check.sh` | patterns to reuse: `probe_maps()`, xdotool and timing helpers |
| `dev/dev.sh` | how the tree gets into the container |

## 9. Traps already paid for (do not rediscover them)

1. **Colima only shares `$HOME` with its VM.** A bind mount from `/tmp` shows up empty. Use
   `dev/dev.sh sync` (tar over `docker exec`).
2. **`~/.docker/config.json` has `"credsStore": "desktop"`**, but Docker Desktop is not
   installed, so pulling a new image fails. Use a temporary `DOCKER_CONFIG` holding `{}` for
   that one pull. The `kube-dev` image already exists, so normally you never need this.
3. **In sed, `\&` inserts a literal `&` and `&` inserts the match.** A probe built with the
   wrong one did not compile, and the measurement read 0 fps.
4. **Random spawns make fps on `subject_map` swing from 76 to 92 for the same code.** Use
   `maps/good/minimal.cub` to compare performance.
5. **Timing-dependent checks need their precondition forced,** or they pass or fail by chance.
6. **OpenRouter:**
   - `typesafe/jev-1.13` does not appear in the public `/api/v1/models` listing, but it works;
   - it answers as `typesafe/jev-1.13-20260917`;
   - `r.request_id` may raise, so read the header;
   - `usage.cost` is only in the raw JSON;
   - `models.list()` fails.
7. **`typesafe-sdk` uses `httpx2`,** not `httpx`, so mock with `httpx2.MockTransport`.
8. **The container is aarch64,** and so is the owner's Linux (UTM). 42's machines were x86_64,
   but that no longer matters (2026-10-06). If you ever emulate x86_64 anyway, `cc1` crashes
   now and then under QEMU: that is not your code.
9. **Jev** cannot do arithmetic or compare numbers, reads literally, and its answers to
   different questions are not mutually coherent. Hence: words, not numbers, in the state, and
   one question. It also leans toward the first option of a Choice, so T8 checks the order of
   the tactics before the config is frozen.
10. **Two traps found by reading the code on 2026-10-05:**
    - **EOF on stdin quits `cub3D_agent`,** so a run whose stdin is closed or `/dev/null`
      ends at once. `docker exec` without `-i` is expected to be such a case (not checked
      yet). Keep stdin open (section 5).
    - **A held fire never shows `weapon_ready == 1`.** The weapon refires in the same frame
      it becomes ready, before the obs line is printed.

    A terminal on stdin or stdout is safe: `cub3D_agent` leaves it alone (no `O_NONBLOCK`) and
    does not read commands from it, so a hand-typed run just plays without a driver.

## 10. The owner's working Jev client (from `~/jev/libros/src/libros/jev.py`, inlined for sessions without `~/jev`)

```python
PRECIO_ENTRADA_POR_MTOK = 0.042   # $ per million input tokens; output is free (verified 2026-09-23)

def _request_id(respuesta) -> str | None:
    # SystemOneResponse.request_id raises TypeSafeError when the header is missing; through OpenRouter it can be missing
    return respuesta.raw_http_response.headers.get("x-typesafe-request-id")

def _coste(respuesta: dict) -> float:          # respuesta = r.raw_http_response.json()
    uso = respuesta.get("usage") or {}
    if isinstance(uso.get("cost"), (int, float)):  # OpenRouter adds usage.cost
        return float(uso["cost"])
    return (uso.get("input_tokens") or 0) * PRECIO_ENTRADA_POR_MTOK / 1e6

# client: AsyncTypeSafeClient(api_key=key, base_url="https://openrouter.ai/api",
#                             model="typesafe/jev-1.13", transport=transport)
# after each paid call it commits the row at once, so what was paid is kept even if the run dies.
```

## 11. Glossary

- **Base:** `origin/feature/jev-agent`, the game after spec 001 and the strafing fix. AC1
  compares against it.
- **Episode:** one run of `cub3D_agent` with one map, seed and policy, ending on a win, a loss
  or 180 s.
- **Policy:** who picks the tactic: `idle` (nothing), `scripted` (rules), `jev`.
- **Tactic:** ENGAGE, KITE, RETREAT or SEARCH. The controller turns it into keys.
- **obs:** one JSON line per frame from the game. **State:** the words sent to Jev.
- **Dev seeds** 1-20 are for tuning. **Test seeds** 101-120 are measured once, after the freeze.
- **Phase:** a group of tasks in `tasks.md` (1 setup, 2 C bridge, 3 Python agent, 4 Jev,
  5 tuning and evaluation). **Checkpoint (L1-L5):** the owner re-running that phase's checks
  on native Linux.
- **Run:** one folder under `agent/runs/`, committed. Its `decisions.jsonl` rows carry what
  each Jev call cost, so all runs together are the spend ledger.
