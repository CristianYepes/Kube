# Plan 002 — Jev plays cub3D_bonus

> HOW. Every choice is argued on ../research-2026-09-28.md (R-numbers below).
> Starts from **the base**: `origin/feature/jev-agent`, where spec 001 is complete (`0ac5649`),
> plus the strafing fix of 2026-10-05 (`ad4244a`, see "Conventions"): the base is now `ad4244a`.
> Work happens on `feature/jev-agentv1`. The section "Implementation decisions" below is
> binding: follow it rather than re-deciding.

## Tech context

- **Game side (C):** a third binary, `cub3D_agent`, built by its own `agent/Makefile` from the
  deliverable's sources plus `sources/jev/*.c`, with `-D BONUS`. It uses the same
  MiniLibX and libft. Norm-compliant, because it lives in the same tree.
- **Agent side (Python 3.12, uv):** `agent/` package with `typesafe-sdk==0.7.2` (MIT, R2) and
  pytest. It runs **on the host**: the Mac, or the owner's Linux at the checkpoints. It never
  runs in the container, so the key never enters it (FR13). It talks to the game over a pipe
  (the pipe costs 0.2 ms, R1):
  - on the Mac: `docker exec -i -e DISPLAY=:99 -w /kube kube-dev ./agent/cub3D_agent <map> <seed>`;
  - on native Linux, from the repo root: `./agent/cub3D_agent <map> <seed>` (FR14).
- **Runtime for the game on the Mac:** Colima + Docker, Ubuntu 22.04 aarch64, Xvfb `:99`
  (R1). The image and helper script come from spec 001 (`dev/`).
- **Linux checkpoints (owner's decision 6):** at the end of each phase the owner re-runs that
  phase's checks on native Linux (`tasks.md`, L1-L5). Every check script therefore runs in
  both places:
  - the shell scripts take `--local`, meaning "here, without the container";
  - `agent/check_bridge.py` uses only Python's standard library, because the container has
    Python 3.10 and no uv;
  - the agent picks `--runner local`.
- **Jev:** OpenRouter `typesafe/jev-1.13`, expected response model
  `typesafe/jev-1.13-20260917`, $0.042/Mtok input (R2). The client is adapted from
  `~/jev/libros/src/libros/jev.py`, which is the user's own code.

## Constraints check

| Constraint | Respected? | How / why |
|---|---|---|
| 42 deliverable unchanged | ✅ | No existing file is edited. `agent/Makefile` compiles the deliverable's sources except the three it replaces (see below) and adds `sources/jev/`. Top-level `Makefile`, `sources/**` (outside `sources/jev/`), `includes/` and `libft/` are untouched. Checked by AC1 (objects identical to the base) |
| Norminette | ✅ | `sources/jev/*.c` follow the norm too, and `norminette sources` still exits 0 |
| English everywhere | ✅ | code, logs, docs |
| YAGNI | ✅ | One Choice question; four tactics; no door tactics, no viewer, no database (JSONL logs) |
| No push without asking | ✅ | One commit per task on `feature/jev-agentv1`; push only when the owner asks |
| Key never exposed | ✅ | Read from the host environment (`OPENROUTER_API_KEY`); never passed to Docker; never logged |

## Chosen approach

A **thin C bridge plus a Python controller**, with Jev as a slow, asynchronous tactic
chooser on top (R7).

```
 Mac host (Python, key lives here)                    Linux container (or native Linux)
┌──────────────────────────────────────────┐  pipe   ┌──────────────────────────────┐
│ reader  ── obs JSON lines ◄──────────────┼─stdout──┤ cub3D_agent (Xvfb :99)       │
│   │ latest obs                           │         │  game loop, every frame:     │
│   ▼                                      │         │   poll stdin (non-blocking)  │
│ features ─► semantic state (words)       │         │   apply last command         │
│   │                    │                 │         │   move (dt-based, from 001), │
│   │                    │                 │         │   sim,                       │
│   ▼                    ▼ every 0.5 s,    │         │   render                     │
│ controller          policy (idle /       │         │   print 1 obs line           │
│  aim, fire, move     scripted / Jev)     │         └──────────────────────────────┘
│   │  ◄── tactic ───────┘  Jev call is    │
│   ▼                       async, gated   │
│ command line ────────────────────────────┼─stdin──►
└──────────────────────────────────────────┘
```

**The three replaced translation units** (the agent build compiles these instead of the
deliverable's). This is the price of FR1: a little duplication instead of any edit to the
deliverable.

| Deliverable file | Agent replacement | Why |
|---|---|---|
| `sources/main.c` | `sources/jev/agent_main.c` | accept `<map> <seed>`, override `data.seed` after `init_game` (FR5) |
| `sources/mlx_loop_and_hook/mlx.c` | `sources/jev/agent_loop.c` | no keyboard or mouse hooks; the loop hook reads commands (FR3) |
| `sources/render/game_loop.c` | `sources/jev/agent_frame.c` | same frame as the bonus, plus stdin poll and one obs line (FR2) |

**Rejected alternatives**
- `#ifdef AGENT` inside the deliverable's files: less code, but it edits the deliverable (FR1).
- A new target in the top-level `Makefile`: evaluators run that file (FR1).
- Controller in C: more C under the norm and no unit tests without X (R7).
- xdotool for control: one process per key, and it depends on focus (R7). It is kept only for
  smoke tests.
- Four independent Choices (move/look/fire/use) like `jev-doom-agent`: answers are not
  mutually coherent (R5). One tactical Choice instead.
- Fixing frame-rate-dependent movement only inside the agent build (a copied `player.c`):
  it would leave the human game unfair and duplicate code. Spec 001 fixes it in the game.
- The floating alias `~typesafe/jev-latest` or `jev-router`: the model could change under the
  thresholds (R2, R5).

## Contracts

### Game -> agent (stdout, one JSON object per line)

First line, once. The map holds the terrain only: the game turns spaces into walls, pads
short rows with walls, and turns the player's start cell into floor (`set_player_at`), so
the example below has `0` where the file has `N`. The first observation says where the
player starts:
```json
{"type":"init","map":["1111","1001","1111"],"width":4,"height":3,"seed":42}
```
Then every frame. Angles and positions are raw here, and the Python side turns them into
words. `frame` counts from 1. **`t` is the game's own clock**, `anim_clock`: the sum of the
frames' `dt`, each at most 0.05 s. It is the clock the simulation runs on (the player and the
zombies move by the same `dt`), and it lags real time only when a frame takes over 50 ms:
```json
{"type":"obs","frame":812,"t":10.84,"dt":0.013,"state":0,"wave":1,"hp":90,
 "weapon_ready":1,"player":{"x":26.5,"y":11.5,"dx":0.0,"dy":-1.0},
 "drops":0,"enemies":[{"x":24.3,"y":9.8,"type":0,"hp":2,"ai":1,"los":1}]}
```
`state` is `G_PLAY`/`G_OVER`/`G_WIN` (0/1/2). `hp` is `player_hp`. `weapon_ready` is 1
when `weapon.state == W_IDLE`. `type` and `ai` use the header's enemy constants. `los` is
the game's own `has_los()`, so line of sight is not reimplemented in Python. `drops` counts
the lines dropped so far.

### Agent -> game (stdin, one line per change)

```
C <forward> <back> <strafe_left> <strafe_right> <turn_left> <turn_right> <fire>
Q
```
Each field is `0` or `1`. The last `C` line stays in force until the next one. `Q` exits
cleanly through `exit_game`. There is no JSON in C, and no `ft_split`: a move line has a fixed
shape (`C`, then seven flags, each after one space: 15 characters), checked character by
character, so a line with 8 flags, a `2`, a lowercase `c` or a double space is rejected
whole, and nothing is allocated.

**EOF on stdin also exits**, so a run "with no input" must keep stdin open without writing
to it: the bridge, or `sleep <s> | ./agent/cub3D_agent ...`, which also ends the run cleanly
after `<s>` seconds. A terminal on stdin or stdout is left alone (no `O_NONBLOCK`, and stdin
is not read: the read would wait for a key and freeze the game), so `./agent/cub3D_agent
<map> <seed>` typed in a terminal just runs without commands.

### Semantic state sent to Jev (built in Python; target < 1,500 characters)
```json
{"player":{"health":"high","weapon":"ready","being_hit":false},
 "threats":{"remaining":3,"in_view":2,
   "nearest":{"direction":"ahead-left","distance":"close","kind":"grunt","wounded":false},
   "close_count":1},
 "space":{"open_directions":["back","right"],"cornered":false},
 "progress":{"wave":"1 of 3","boss_present":false},
 "current_tactic":"ENGAGE"}
```
Bands are defined in code: distance `touching` (< 1.0), `close` (< 2.5), `medium` (< 6),
`far`. Direction comes from the angle relative to the heading, in 8 sectors. Health `high`
(>= 60), `medium` (>= 30), `low`.

### The question (one Choice; drafted here, tuned in T8 on development seeds only)
```json
{"tactic":{"type":"choice",
  "instructions":"Pick the tactic for the next half second of a zombie-survival shooter. Read `threats`, `player` and `space` in the state. The code aims and fires by itself; you only pick what the body does.",
  "criteria":{
   "ENGAGE":{"what":"Stand and shoot the nearest threat.","when":"a threat is in view and not touching, and health is not low","not_for":"several threats close at once"},
   "KITE":{"what":"Step straight back from the nearest threat while facing and shooting it.","when":"threats are close and there is open space behind","not_for":"being cornered"},
   "RETREAT":{"what":"Move along a path to the open area farthest from every threat, still facing and shooting the nearest one.","when":"health is low, or you are being hit by more than one threat","not_for":"a single wounded threat you can finish"},
   "SEARCH":{"what":"Move toward the remaining threats that are out of view.","when":"no threat is in view but some remain","not_for":"any threat in view"}}}}
```

The descriptions say what the controller really does with each tactic, because Jev reads
them literally. KITE and RETREAT both keep facing the nearest threat: walking backwards is as
fast as walking forwards (`player.c`), and only a player who faces a threat can shoot it.

### Controller (code, every observation)
- **Aim:** turn toward the chosen target, with a dead zone measured like the hitscan, in
  cells off the aim line (`perp`, R4), not in degrees. **Fire** when the target is in front,
  `perp < 0.5`, within 10 cells, `los=1` and the weapon is ready. This mirrors `combat.c`.
- **Move:**
  - ENGAGE: hold still.
  - KITE: back, plus strafe to avoid walls.
  - RETREAT: follow a Python BFS over the `init` map toward the reachable cell that maximizes
    distance from the threats.
  - SEARCH: BFS toward the nearest remaining enemy.
- **Scripted policy (baseline):** fixed rules over the same semantic state.
  - RETREAT if health is low and something is close.
  - KITE if something is close.
  - ENGAGE if something is in view.
  - Otherwise SEARCH.
  - It decides on Jev's schedule (every 0.5 s and on the same events), so the comparison
    differs only in who chooses, not in how often.
- **Idle policy:** sends nothing.
- **Initial tactic:** ENGAGE, until the policy's first choice is applied. Wave-1 zombies
  spawn with line of sight to the player whenever such a cell exists (`utils.c`).

### Jev policy
- Decide every 0.5 s, or at once when a new wave starts or health drops a band, with at most
  one request in flight.
- Apply the answer only if `confidence >= θ`; θ starts at 0.6 and is tuned in T8. For a Choice
  with n options TypeSafe publishes the formula (docs, read 2026-10-03):
  `confidence = (p_max - 1/n) / (1 - 1/n)`. With our four tactics, θ = 0.6 means the chosen
  tactic has `p_max >= 0.70` [calc]. Check against the docs' own example: 0.85 over 3 options
  gives 0.775, and the docs print 0.78. `probabilities` is also returned, so a threshold on
  `p_max` is an equivalent alternative if it reads better in the logs.
- Retries: the SDK's `RetryPolicy`, plus one attempt timeout of 1.5 s. When every retry
  fails, the row records the error, the tactic stays, and the next decision goes out on
  schedule.
- **Stale answers:** with one request in flight, answers cannot overtake each other. An
  answer is stale when an event (new wave, health band drop) happened after its state was
  sent. It is logged with `applied: false`, and a new request goes out at once.
- Budget: cumulative `usage.cost` per run; stop calling at the cap and fall back to the
  scripted rules. An answer that arrives after that switch is discarded.

### Logs (JSONL, one folder per episode, under `agent/runs/`, **committed**; FR15)

The owner keeps every run, to study how the game gets beaten (which tactics, where, in what
order) and to decide later where obstacles would make it harder. Runs are committed with the
task that made them, and after each Linux checkpoint. Git therefore also carries the spend
ledger between the Mac and Linux. **Never delete a run:** its cost would leave the ledger.

- **Folder name:** `<UTC date-time>-<policy>-s<seed>-<darwin|linux>`, for example
  `20261005T170312Z-jev-s1-darwin`, so runs from the two machines never clash. The other paid
  commands follow the same pattern:
  - an evaluation is `eval-<UTC date-time>-<machine>/`, with one sub-folder per episode and
    `report.md`;
  - the probes are `latency-<UTC date-time>-<machine>/` and
    `order-check-<UTC date-time>-<machine>/`, each with its `decisions.jsonl`.
- `result.json`:
  - what was run: map path and the map file's sha256, seed, policy, machine and config sha256;
  - how it went: outcome, survival seconds, wave reached, kills, damage taken and drops;
  - `stalls`: gaps above 100 ms between observations handled by the controller, timed with
    the host's monotonic clock (AC8);
  - how the game was played: `tactic_seconds` (seconds spent in each tactic) and `switches`
    (tactic changes).
- `episode.jsonl`: one row every 0.5 s with `t`, the player's `x` and `y` (2 decimals), `hp`,
  `wave`, enemies left and the current tactic. It is the player's path, for a map of where
  episodes are won or lost.
- `decisions.jsonl`: one row per decision, for **every policy**, with `t`, the state sent, the
  tactic chosen and `applied`. Jev rows add `answers` (the probabilities), `confidence`,
  `model`, `input_tokens`, `cost`, `latency_ms` and `error` (null unless every retry failed).
- `run` ends by printing one line: outcome, survival, decisions made and applied, and the run's
  spend.
- **Size** [calc]: about 1 KB per decision row and 2 decisions per second, so about 360 KB per
  180 s episode. 60-80 Jev episodes come to about 20-30 MB in git. If that ever matters,
  compress old runs with `gzip`; never delete them.

## Implementation decisions (v0.5, verified 2026-09-29; corrected and extended 2026-10-05)

Every fact below was checked in the code or with a command on 2026-09-29, and re-read against
the code on 2026-10-05. Where a detail is left open, the tasks say how to verify it before
relying on it.

### Layout (only these paths may change: `agent/`, `sources/jev/`, `specs/` and the root `CLAUDE.md`; AC1)

```
agent/
  Makefile            builds agent/cub3D_agent (see "Build")
  .gitignore          cub3D_agent, obj/, .venv/, __pycache__/, .pytest_cache/ (not runs/: FR15)
  check_isolation.sh  AC1 guard (T2); --local runs it without the container, on Linux
  check_bridge.py     the C bridge's checks (T3b-T3d); Python standard library only, so it runs
                      in the container (Python 3.10) and on native Linux alike
  frozen.json         config_sha256 and date, written at the freeze (T8)
  pyproject.toml      uv project "kube-agent", requires-python >=3.12,
                      deps: typesafe-sdk==0.7.2; dev: pytest; script: kube-agent = kube_agent.cli:main
  .python-version     3.12 (uv python pin 3.12), so every machine uses the same interpreter
  uv.lock             committed: pins every dependency, pytest included
  src/kube_agent/
    config.py         constants, the question, config_sha256()
    bridge.py         start the game (docker | local), read init/obs lines, send C/Q lines
    features.py       obs -> semantic state (pure functions)
    controller.py     tactic + obs + map -> C line (aim, fire, movement, BFS)
    policies.py       idle, scripted, jev
    jev_client.py     SDK wrapper: pinned model, cost, request id, budget, decision rows
    episode.py        one episode: the loop, the logs, result.json
    evaluate.py       many episodes, statistics, report.md
    cli.py            kube-agent run | eval | spend | latency | order-check;
                      run and eval take --map (default maps/bonus/subject_map.cub)
  tests/              pytest; no X, no network; tests/fixtures/ holds obs recorded in T3
  runs/               every run's logs, committed (see "Logs")
sources/jev/
  agent.h             prototypes of the bridge (includes cub3d.h)
  agent_main.c        replaces sources/main.c
  agent_loop.c        replaces sources/mlx_loop_and_hook/mlx.c
  agent_frame.c       replaces sources/render/game_loop.c
  agent_io.c          the init line, the non-blocking setup of stdout and stdin, agent_fail
  agent_obs.c         the obs line (a separate file because of the norm's 5 functions per file)
  agent_cmd.c         reads stdin and applies the commands (the norm's 5 functions per file)
```

**Never edit** the top-level `Makefile`, `.gitignore`, `dev/`, `tests/`, `includes/`, `libft/`,
`maps/`, `textures/`, `files/` or any `sources/` file outside `sources/jev/`.

- **The C folder is `sources/jev/`** (owner's decision 5), so `agent/` is the only folder named
  agent. The files inside keep the `agent_` prefix, because they build `cub3D_agent`.
- **Harder maps**, if the owner adds them after v1, go in `agent/maps/`, created with its first
  map, never in `maps/`. They need `F`/`C` colours and textures that exist under `files/`, the
  bonus charset (`012DNSEW`) and fewer than 64 rows and columns (flow-field guard). They load
  through `--map`.

### Build (`agent/Makefile`, run with `make -C agent` from the repo root)

- The first step is `$(MAKE) -s -C .. bonus`, which guarantees `../libft/libft.a` and the
  pinned `../minilibx-linux/libmlx.a`.
- The sources:

  ```
  SRCS = $(filter-out ../sources/main.c ../sources/mlx_loop_and_hook/mlx.c ../sources/render/game_loop.c, $(wildcard ../sources/*.c ../sources/*/*.c ../sources/*/*/*.c))
  ```

  - A wildcard is fine here: this is not the 42 Makefile.
  - It picks up `sources/jev/*.c` by itself.
  - It cannot drift from the deliverable's list, because the bonus build compiles every `.c`
    under `sources/` (checked on 2026-09-28, and again on 2026-10-05: all 46 files are in the
    Makefile's two lists).
- Flags: `-Wall -Wextra -Werror -D BONUS -I../includes -I../libft -I../minilibx-linux`. No
  `-D AGENT`: no file reads it, and the deliverable must never test for it.
- Objects go to `obj/`; the link line is `../libft/libft.a ../minilibx-linux/libmlx.a -lXext
  -lX11 -lm`, producing `cub3D_agent`.
- **Run it from the repo root.** The maps name textures relative to the working directory
  (`./files/...`), and the code loads `textures/...` the same way:

  ```
  ./agent/cub3D_agent maps/bonus/subject_map.cub 7
  ```

- In the dev container: `dev/dev.sh sync && docker exec kube-dev make -s -C agent`.
  `sync` wipes everything but `minilibx-linux/`, so build again after every sync.

### C bridge

- **`agent_main.c`**:
  - with `argc != 3`, print `Error` and `Usage: ./cub3D_agent <map.cub> <seed>`, then return 1;
  - a seed that is not 1 to 9 digits also prints `Error` and returns 1, before the map is
    opened: `ft_atoi` reads `abc` as 0 silently and does not detect overflow;
  - then `check_file`, `parsing` and `init_game`, exactly as in `sources/main.c:15-33`;
  - **then** `data.seed = (unsigned int)ft_atoi(argv[2])`. `init_mod_state` has just seeded
    from the clock. Enemies spawn at the first `update_sim`, after this override, so the same
    seed gives the same wave-1 spawns (AC5):
    - the spawn depends only on the seed, the map and the player's position, and an idle
      player has not moved yet;
    - on its first update an enemy only switches from IDLE to CHASE (`enemy_ai.c`), so the
      first obs with enemies prints the exact spawn positions;
    - later positions depend on `dt`, and later waves on where the player is, so neither is
      bit-exact;
  - then `agent_init_io(&data)`, which prints the init line and then sets stdout to
    `O_NONBLOCK` with `fcntl`. The line goes out first, while stdout still blocks, so a long
    map is never cut. stdin gets the same flag in T3c, when it is first read. A terminal is
    left alone (`isatty`): the flag would stay on it after the game exits;
  - then `loop(&data)`.
- **`agent_loop.c`**: `loop()` is `sources/mlx_loop_and_hook/mlx.c:17-27` without the key and
  mouse hooks. It keeps hook 17 (`close_window`), `gettimeofday(&data->last_time, NULL)`,
  `mlx_loop_hook(..., game_loop, ...)` and `mlx_loop`.
- **`agent_frame.c`**:
  - a static `tick_clock`, copied from `sources/render/game_loop.c:15-28`;
  - `game_loop`, copied from `game_loop.c:32-54`, with `agent_read_commands(data)` as its
    first statement and `agent_print_obs(data)` right after `mlx_put_image_to_window`;
  - a header comment naming the file and the base commit it mirrors.
- **Commands:**
  - A `C a b c d e f g` line sets `player.key_up`, `key_down`, `key_left`, `key_right`,
    `rotate_left` and `rotate_right` from `a..f`.
  - While `g == 1`, every frame does `data->fire = 1; fire_shotgun(data);`. That is what the Up
    key does in `sources/movement/input_bonus.c` (`key_press_bonus`). `try_fire` enforces the
    0.6 s cooldown.
  - So a held fire refires as soon as the weapon is ready. `update_sim` runs `tick_weapon`
    and then `try_fire` in the same frame, before the obs line is printed, so `weapon_ready`
    reads 0 for as long as fire is held. To see it come back to 1, release fire.
  - `Q`, or EOF on stdin, calls `exit_game(data)`: a clean exit that frees everything
    (valgrind: 0 bytes in use at exit, 0 errors, for both ways out). EOF matters, because a
    killed Python side must not leave the game running.
  - A malformed line is ignored whole and leaves `Error`, the line and `ignored: not a
    command` on stderr, so a bug on the writer's side is seen and nothing is half-applied.
- **Reading stdin:** `agent_read_commands` runs first in every frame. One `read` of at most
  `CMD_READ` (1024) bytes per frame (`EAGAIN` or `EINTR` means nothing new), fed byte by byte
  into a line buffer of `CMD_MAX` (256). The line ends at `\n` and is applied; a longer line
  keeps only its start and is dropped whole at its end. A line cut between two reads is put
  back together. The reader's memory (the line, whether fire is held) is a `static
  t_cmd_reader` inside `agent_read_commands`.
- **Writing obs:**
  - `snprintf` the whole line into a buffer, then one `write(STDOUT_FILENO, ...)`;
  - keep every line under 4096 bytes. On Linux a pipe write of at most `PIPE_BUF` (4096)
    bytes is atomic: all of it or `EAGAIN`. So a full pipe drops the frame's line (`drops++`)
    and never writes half a line;
  - floats use `%.3f`, and fields come in the contract's order;
  - an error other than `EAGAIN`, a half-written line, or a line that would not fit ends the
    run with `Error`, the operation and the reason, exit 1 (`agent_fail`): nothing is cut
    silently;
  - the counters (`frame`, `drops`) live in a `static t_obs_counts` inside
    `agent_print_obs`: norminette accepts a `static` variable in a function, and notes a
    file-scope one (`GLOBAL_VAR_DETECTED`).
- **Norm:** every file in `sources/jev/` passes `norminette`. Run it; do not guess the rules
  (25 lines per function, 5 functions per file, 4 parameters, 5 variables, 80 columns, ...).
- **State that `t_data` cannot hold** (the frame counter, the start time, `drops`, the stdin
  buffer): `includes/` may not change, so these are `static` variables in `sources/jev/`.
- **Names to avoid:** `tests/check.sh` (`check_dead_code`) fails if `BREAK`, `CONTINUE`,
  `DEATH_TIME`, `E_DEAD`, `render_weapon`, `anim_timer` or `frame_idx` appears as a word
  anywhere under `sources/`, `sources/jev/` included.

### Conventions (verified in the code; write the worked example as a unit test)

- `data->map[row][col]`: x is the column and y is the row. **y grows downward** (screen space).
- `dir` is a unit vector: it starts axis-aligned and rotation keeps its length. `plane` is
  `dir` rotated +90°, length 0.66, and points to the player's **right**: facing N, `dir = (0,-1)`
  and `plane = (0.66, 0)`, i.e. east (`set_ns` in `check_map.c`). The unit right vector is
  `(-dy, dx)`.
- **Strafing was slower than walking, and was fixed on the base.** Until 2026-10-05,
  `move_player` moved forward and back along `dir` (length 1) but strafed along `plane`
  (length 0.66, it sets the field of view), so strafing ran at 1.2 × 0.66 = **0.792 cells/s**
  [calc]; measured through the bridge: 1.20 and 0.79. The owner had it fixed in the game itself,
  on `feature/jev-agent` (`ad4244a`): strafing now goes along the unit vector `(-dy, dx)`, and
  the bridge measures 1.20 for forward, back and both strafes. This branch carries it by a
  merge. A diagonal step is still the vector sum of the two, 1.7 cells/s [calc], not normalised: the
  controller replans every observation, so its direction not being exactly the wanted vector
  `w` does not matter.
- A positive angle, which is what the right-arrow key produces through `rotate_right`, turns
  **right**, clockwise on screen: east `(1,0)` becomes `(cos a, sin a)`, toward south.
- For `v = target - player`:
  - `dot = dx*vx + dy*vy` is the distance ahead;
  - `cross = dx*vy - dy*vx`: `cross > 0` means the target is on the **right**, `cross < 0` on
    the **left**;
  - `bearing = atan2(cross, dot)` is 0 straight ahead and +pi/2 to the right.

  **Worked example:** the player is at (5.5, 5.5) facing east (1, 0) and the enemy is at
  (5.5, 4.5), one row up. `cross = 1*(-1) - 0*0 = -1`, so the enemy is on the LEFT: facing
  east, north is on the left.
- The hitscan (`combat.c` `hitscan_hit`) hits when `dot > 0`, `perp = |cross| < 0.5`,
  `dot < 10` and `has_los`.
- FOV half-angle: `atan(0.66) = 0.583 rad` (33.4°).
- A cell is walkable if its character is not in `"1D"`: `is_wall` treats `1` and closed doors
  `D` as walls, while sprites `2` and open doors `O` are walkable.

### Semantic features (exact values)

- **Distance band:** `touching` below 1.0, `close` below 2.5, `medium` below 6.0, `far`
  otherwise.
- **Direction:** 8 sectors of 45°, centred ahead:
  - `ahead`: |b| < 22.5°;
  - `ahead-right`: 22.5-67.5°;
  - `right`: 67.5-112.5°;
  - `behind-right`: 112.5-157.5°;
  - `behind`: |b| >= 157.5°;
  - the mirror images to the left for negative b.
- **`in_view`:** `los == 1` and |bearing| <= 0.583.
- **Health:** `high` from 60, `medium` from 30, `low` below 30. The HUD bar changes colour at
  the same values (`hud.c`).
- **`being_hit`:** hp is lower than it was 1.0 s ago.
- **`kind`:** type 0 `grunt`, 1 `runner`, 2 `boss`. **`wounded`:** hp below its spawn hp
  (grunt 2, runner 1, boss 8; `waves.c`).
- **`open_directions`:** ahead, back, right or left is open when the cell at
  `player + 1.0 * (dir | -dir | right_u | -right_u)` is walkable. **`cornered`:** at most one
  is open.
- **`remaining`** is the number of enemies; **`in_view`** counts the enemies in view;
  **`close_count`** counts enemies nearer than 2.5. **`nearest`** is `null` when no enemy
  remains.
- **`wave`:** `"<w> of 3"`. **`boss_present`:** there is a type 2.
- **No numbers with decimals anywhere in the state** (AC6).

### Controller (exact)

- **Target:** the nearest enemy with `los`, or the nearest enemy if none has it.
- **Turn** while the target is behind (`dot <= 0`) or off the aim line (`|cross| >= 0.25`):
  right when `cross > 0`, left otherwise (right when `cross == 0`). SEARCH aims at the next
  path cell instead of the enemy.
  - The dead zone is in cells, like the hitscan, so it narrows with distance. An angular dead
    zone (the 0.05 rad of v0.3) can stop the aim `10 · sin 0.05 = 0.50` cells off the line at
    10 cells. With the 0.45 fire margin, a target beyond about 9 cells could then never be shot
    [calc].
  - At 10 cells, 0.25 cells is about 0.025 rad each side. One frame of turning is
    `1.8 / fps` rad: 0.0225 at 80 fps and 0.04 at 45 fps [calc], under the 0.05 rad width of
    the zone, so the aim settles instead of swinging across it.
- **Fire** when the target has `los`, `0 < dot < 10`, `|cross| < 0.45` (a margin under the
  game's 0.5) and `weapon_ready == 1`.
- **Movement:** take the desired world vector `w` of the tactic. If it is not zero, normalise
  it to a unit vector, then:
  - forward if `w·dir > 0.3`, back if `< -0.3`;
  - strafe right if `w·right_u > 0.3`, strafe left if `< -0.3`.

  The vector `w` of each tactic:
  - **ENGAGE:** `w = 0`.
  - **KITE:** `w = -unit(target - player)`. If the cell 0.6 along `w` is not walkable, use
    RETREAT's `w` instead.
  - **RETREAT:** BFS (4 neighbours) from the player's cell over walkable cells, up to depth 8.
    Pick the cell that maximises the minimum euclidean distance to any enemy; on ties, the one
    with fewer steps. `w` = centre of the first step's cell - player position, or `0` when
    the best cell is the player's own.
  - **SEARCH:** BFS to the nearest enemy's cell. `w` = centre of the first step's cell - player
    position, or `0` when that enemy is in the player's cell.
- **Stuck:** if `w != 0` and the player moved less than 0.05 cells over the last 0.5 s, add a
  strafe toward an open side for 0.5 s.
- Send a `C` line only when it differs from the last one sent.

### SDK facts (`typesafe-sdk` 0.7.2, introspected 2026-09-29; 0.7.2 only added an http2 extra)

- The client and the call:

  ```
  AsyncTypeSafeClient(*, api_key, model, retry, timeout, headers, transport, http_client, base_url)
  await client.system_one(state, questions, *, model, retry, timeout, extra_headers,
                          extra_body, response_model)
  ```

  Use `base_url="https://openrouter.ai/api"` and `model="typesafe/jev-1.13"`.
- `Choice(instructions=..., criteria={name: str | dict | None})`.
  `r.answers["tactic"]` is a `ChoiceAnswer` with `type`, `choice`, `confidence` and
  `probabilities`.
- **Retries:** `RetryPolicy(max_retries=2, backoff_initial=0.5, backoff_max=5.0,
  backoff_jitter=0.25, http_statuses={408, 429, 500..599}, respect_retry_after=True,
  timeout=30.0, ...)`. The defaults already retry 429 and 529.
  - **Before relying on it, read `typesafe_sdk/_core/retry.py`** to learn whether
    `RetryPolicy.timeout` is the total across attempts.
  - Target: at most 1.5 s per attempt and a few seconds in total. A late answer is discarded
    anyway.
- `SystemOneResponse` has `model`, `usage` and `answers`. `usage` only keeps `input_tokens`
  and `output_tokens`, because the model ignores extra fields.
  - **The cost is only in the raw JSON:** `r.raw_http_response.json()["usage"].get("cost")`.
  - **The request id:** `r.raw_http_response.headers.get("x-typesafe-request-id")`. It is
    missing through OpenRouter, and `r.request_id` may raise (field notes; `libros`).
  - **The model that answered:** `r.model`, expected `typesafe/jev-1.13-20260917`.
- **The HTTP layer is `httpx2`, not `httpx`.** Tests pass `transport=httpx2.MockTransport(handler)`.
- Exceptions: `TypeSafeRateLimitError` (429), `TypeSafeAPITimeoutError`,
  `TypeSafeAPIConnectionError`, base `TypeSafeAPIError`, root `TypeSafeError`.

### Key

- The owner's key is in `~/jev/libros/.env`, one line: `OPENROUTER_API_KEY=sk-or-...`.
- Load it into the command that needs it, in the same shell call. Never echo it:

  ```
  set -a; . ~/jev/libros/.env; set +a; cd agent && uv run kube-agent run --policy jev --seed 1
  ```

- The agent reads `os.environ["OPENROUTER_API_KEY"]`. Its error names the variable, never the
  value. The key never goes to Docker or into a log.

### Budget ledger ($1 total, Decision 3)

- Every Jev call appends a row with its `cost` to `agent/runs/<run>/decisions.jsonl`.
- `kube-agent spend` sums every row under `agent/runs/` and prints the total and what is left
  of $1.00.
- **Every command that calls Jev refuses to start once the total reaches $1.00:** `run` and
  `eval` with the Jev policy, `latency` and `order-check`. They stop calling Jev when the
  run's cap is reached: `cap = min(--budget-usd, remaining)`. `run` and `eval` then fall back
  to the scripted rules. Defaults: `run` 0.05, `eval` 0.50.
- **The ledger travels with git,** because runs are committed (FR15). That only works if both
  machines keep in step:
  - before any paid run, on either machine, `git pull --ff-only`;
  - after it, commit the run, and push before switching machines (the owner asks for the
    push);
  - never delete a run.

  Then `spend` sums the paid calls of both machines.
- Estimate [calc]: at most 2 calls/s × 180 s × about 1,300 tokens × $0.042/M, so at most
  about $0.02 per episode. 40 Jev episodes cost at most about $0.80. `spend` is the real
  number.

### Runtime expectations

- One episode at a time: one Xvfb, 2 CPUs.
- Idle episodes end in about 10 s (death); the others last up to 180 s.
- The final evaluation (20 seeds × 3 policies) can take up to about 2 h in the worst case. Run
  it in the background and log progress per episode.

## Evaluation protocol (mirrors the `libros` dev/test discipline)
- Seeds 1-20 are **development**: tune the criteria and θ there only.
- Seeds 101-120 are **test**. Before running them, freeze the config (sha256 of the question,
  bands, θ and controller constants).
- Each policy runs once per test seed on `maps/bonus/subject_map.cub`, with a 180 s cap.
- Every Jev call of the spec counts against the $1 ledger (see "Budget ledger").
- Report per policy:
  - n and wins, with a Wilson 95% interval;
  - survival median and IQR;
  - waves cleared;
  - the share of time in each tactic, in wins and in losses (from `tactic_seconds`): the
    first answer to "how does the game get beaten";
  - for Jev: cost per episode and latency p50/p95.

## Risks & mitigations
- **Jev latency is unknown** (R2). If p95 > 500 ms, tactics lag behind the fight. Measure it
  in T6 before tuning. If it is too slow, decide on events only instead of every 0.5 s.
- **The scripted policy may beat Jev.** That is a valid result (R3). The report says so plainly.
- **A stall in the Python loop is invisible in the game's own clock.** The game never waits,
  and the pipe buffers what it writes meanwhile. A Linux pipe holds 64 KiB, about 2.7 s of
  obs lines of ~300 bytes at 80 per second [calc]. So AC8 times the observations the
  controller handles on the host, not the game's `t`.
- **Option order bias.** The `jev-1.13` jaggedness page (reviewed 2026-10-02) says a Choice
  leans toward its first option, and ENGAGE is listed first. If that bias is real here, Jev
  could look better or worse than it is because of a list order. T8 measures it on logged
  states before anything is frozen; the mitigation is described there.
- **aarch64 vs x86_64** (R1). The container is aarch64. The Linux checkpoints record
  `uname -m`; if the owner's Linux is x86_64, L5 is the final x86_64 check of AC1 and of an
  episode. If it is not, run L5 once more on an x86_64 machine (a 42 campus machine) before
  any submission-related step.
- **Mac and Linux drift apart** (owner's decision 6). Each phase is closed on the Mac first
  and then re-checked on Linux with the same commands. A failure seen only on Linux goes back
  to the Mac session with its output; it is not patched by hand on Linux.
- **The three replaced files drift from the deliverable's.** Each copy starts with a comment
  naming the source file and base commit it mirrors. AC1 catches edits to the originals, which
  would mean the copies need a look.
- **MiniLibX version.** Spec 001 pins it in the top-level Makefile. `agent/Makefile` reuses
  that same checkout (`minilibx-linux/libmlx.a`) rather than cloning its own.
- **Pipe back-pressure:** if Python stalls, stdout could block the game. The game writes
  observations with a non-blocking write and drops the frame's line on `EAGAIN`, counting the
  drops.
