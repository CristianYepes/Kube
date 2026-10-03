# START HERE — implementing spec 002 (Jev plays cub3D_bonus)

> For the model (or person) that implements this spec. It is self-contained: everything
> decided and verified so far is in `specs/`, so nothing needs to be rediscovered. Written
> 2026-09-29; updated 2026-10-03 (T8 option-order check, new Jev rate limits).

## 1. The mission in five lines

1. Build `cub3D_agent`, a **separate** binary of the game. Every frame it prints the state as
   one JSON line on stdout, and it takes movement/turn/fire commands on stdin.
2. Build a Python agent on the Mac that reads those lines, turns them into a state **in
   words**, and drives the player. **Code aims, fires and moves.**
3. **Jev** (TypeSafe's decision model, through OpenRouter) only picks the tactic: ENGAGE, KITE,
   RETREAT or SEARCH. It is asked every 0.5 s, and its confidence is used.
4. Compare Jev against an idle player and a hand-written rule policy on the same seeds, and
   report it honestly, with its cost.
5. **Do not change the 42 game itself.** Spec 001 already polished it; this spec only adds
   files.

## 2. Where you are

- **Branch:** `feature/jev-agentv1`. The base is `origin/feature/jev-agent` (`0ac5649`), where
  spec 001 is complete and all its checks pass.
- **Already in the repo:**
  - the game;
  - `dev/dev.sh`, a Linux container on macOS;
  - `tests/check.sh`, the 10 acceptance checks of spec 001;
  - the specs.
- **Not started:** everything in `specs/002-jev-agent/tasks.md` after T0.

## 2b. On a new machine (do this once)

The repo carries everything **except the API key**, which must never be in it.

1. **Tools.** On the original Mac they came from Homebrew:

   ```bash
   brew install colima docker uv
   ```

   That gave colima 0.9.1, docker 28.5.0 and uv 0.8.24; Lima comes in as a Colima dependency.
   On Linux, install Docker and `uv` instead: `dev/dev.sh` only needs `docker`.
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
   grep -q '^OPENROUTER_API_KEY=sk-or-' ~/jev/libros/.env && echo "key file OK"
   ```

   On Linux:

   ```bash
   read -s -p "OpenRouter key: " k && mkdir -p ~/jev/libros && printf 'OPENROUTER_API_KEY=%s\n' "$k" > ~/jev/libros/.env && chmod 600 ~/jev/libros/.env && unset k
   ```

   **The key never goes into the chat,** and it is never pasted as a command argument.
4. **Start:** `colima start` (macOS only), then `dev/dev.sh up`, then `dev/dev.sh check`. That is
   task T1.

These steps were written from the original Mac and have not been run on a fresh machine: if
one fails, fix it and correct this section in the same commit.

## 3. Reading order (about 20 minutes; do not skip)

1. `specs/CONTEXT.md`: the goal, "Jev in two minutes", the game's rules, the hard rules.
2. `specs/002-jev-agent/spec.md`: requirements FR1-FR14, acceptance criteria AC1-AC13,
   "Decisions".
3. `specs/002-jev-agent/plan.md`: **"Implementation decisions" is binding.** It covers the
   layout, build, bridge, the sign conventions with a worked example, the exact features and
   controller, the SDK facts, the key and the budget.
4. `specs/002-jev-agent/tasks.md`: **your checklist.** Tick it as you go.
5. As needed: `specs/research-2026-09-28.md`. R2 is Jev access, R4 the game's numbers, R5
   Jev's weak points, R7 the architecture choice, R8-R10 the build, memory and fps facts.

## 4. Hard rules

1. **Only these paths may change:** `agent/`, `sources/agent/`, `specs/` and the root
   `CLAUDE.md`. Never edit the
   top-level `Makefile`, `.gitignore`, `dev/`, `tests/`, `includes/`, `libft/`, `maps/`,
   `textures/`, `files/`, or any other `sources/` file. `agent/check_isolation.sh` (T2)
   enforces it.
2. **English** in every file, comment, identifier and commit message. Talk to the owner in
   **Spanish**.
3. **YAGNI.** Build only what a task needs. No placeholders, no speculative options.
4. **C in `sources/agent/` must pass `norminette`.** Run it; do not guess.
5. **The API key:** never print, log, commit, or pass it to Docker. Load it only into the
   command that uses it (section 5).
6. **Budget:** $1 in total for every Jev call of this spec. Check `kube-agent spend` before any
   paid run. 🛑 Stop if a run would cross it.
7. **Verify, do not assume.** A number you computed is labelled a calculation. A result that
   cannot be true (0 fps, an impossible distance) means the instrument is broken: fix it
   before reporting. A zero proves nothing until you have seen the same check find something.
8. **One commit per task,** with the message given in `tasks.md`. **Never push** unless the
   owner asks.

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

The Python agent runs on the Mac, from `agent/`, with `uv` (0.8.24 is installed):

```bash
cd agent && uv sync && uv run pytest -q
set -a; . ~/jev/libros/.env; set +a; cd agent && uv run kube-agent run --policy jev --seed 1
```

The second line loads the owner's OpenRouter key into that shell only. Every Bash call is a
new shell, so load it in the same call that needs it. Never `echo` it.

## 6. Workflow

1. Take the first unticked task in `tasks.md` and read its **Read** list.
2. Implement only that task.
3. Run its **Verify**. If it fails, find out why; do not loosen the check to make it pass.
4. Tick it: `[x]` plus `Done <date>:` and the evidence (numbers).
5. Commit with the task's message.
6. Give the owner a two-line status in Spanish, then take the next task.

## 7. When to stop and ask the owner (🛑)

- the tasks marked 🛑: T6b if the answering model is unexpected, T8 before freezing, T9's
  results, T12 push;
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
8. **The container is aarch64,** and 42 machines are x86_64. Emulated x86_64 works, but `cc1`
   crashes now and then under QEMU. That is not your code.
9. **Jev** cannot do arithmetic or compare numbers, reads literally, and its answers to
   different questions are not mutually coherent. Hence: words, not numbers, in the state, and
   one question. It also leans toward the first option of a Choice, so T8 checks the order of
   the tactics before the config is frozen.

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

- **Base:** `origin/feature/jev-agent`, the game after spec 001. AC1 compares against it.
- **Episode:** one run of `cub3D_agent` with one map, seed and policy, ending on a win, a loss
  or 180 s.
- **Policy:** who picks the tactic: `idle` (nothing), `scripted` (rules), `jev`.
- **Tactic:** ENGAGE, KITE, RETREAT or SEARCH. The controller turns it into keys.
- **obs:** one JSON line per frame from the game. **State:** the words sent to Jev.
- **Dev seeds** 1-20 are for tuning. **Test seeds** 101-120 are measured once, after the freeze.
