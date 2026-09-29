# Plan 002 — Jev plays cub3D_bonus

> HOW. Every choice is argued on ../research-2026-09-28.md (R-numbers below).
> Starts from **the base**: the commit where spec 001 (game-ready) is complete.

## Tech context

- **Game side (C):** a third binary, `cub3D_agent`, built by its own `agent/Makefile` from the
  deliverable's sources plus `sources/agent/*.c`, with `-D BONUS -D AGENT`. It uses the same
  MiniLibX and libft. Norm-compliant, because it lives in the same tree.
- **Agent side (Python 3.12, uv):** `agent/` package with `typesafe-sdk==0.7.2` (MIT, R2) and
  pytest. It runs **on the Mac host**, so the key never enters the container (FR13). It talks
  to the game over a pipe: `docker exec -i kube-dev-run ./cub3D_agent ...` on the Mac, or
  `./cub3D_agent ...` on native Linux (FR14). The pipe costs 0.2 ms (R1).
- **Runtime for the game on the Mac:** Colima + Docker, Ubuntu 22.04 aarch64, Xvfb `:99`
  (R1). The image and helper script come from spec 001 (`dev/`).
- **Jev:** OpenRouter `typesafe/jev-1.13`, expected response model
  `typesafe/jev-1.13-20260917`, $0.042/Mtok input (R2). The client is adapted from
  `~/jev/libros/src/libros/jev.py`, which is the user's own code.

## Constraints check

| Constraint | Respected? | How / why |
|---|---|---|
| 42 deliverable unchanged | ✅ | No existing file is edited. `agent/Makefile` compiles the deliverable's sources except the three it replaces (see below) and adds `sources/agent/`. Top-level `Makefile`, `sources/**` (outside `sources/agent/`), `includes/` and `libft/` are untouched. Checked by AC1 (objects identical to the base) |
| Norminette | ✅ | `sources/agent/*.c` follow the norm too, and `norminette sources` still exits 0 |
| English everywhere | ✅ | code, logs, docs |
| YAGNI | ✅ | One Choice question; four tactics; no door tactics, no viewer, no database (JSONL logs) |
| No commit/push without asking | ✅ | Work stays uncommitted until NEEDS CLARIFICATION 1 is answered |
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
| `sources/main.c` | `sources/agent/agent_main.c` | accept `<map> <seed>`, override `data.seed` after `init_game` (FR5) |
| `sources/mlx_loop_and_hook/mlx.c` | `sources/agent/agent_loop.c` | no keyboard or mouse hooks; the loop hook reads commands (FR3) |
| `sources/render/game_loop.c` | `sources/agent/agent_frame.c` | same frame as the bonus, plus stdin poll and one obs line (FR2) |

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

First line, once:
```json
{"type":"init","map":["1111","1N01","1111"],"width":4,"height":3,"seed":42}
```
Then every frame (`t` = seconds since start; angles and positions are raw here, and the
Python side turns them into words):
```json
{"type":"obs","frame":812,"t":10.84,"dt":0.013,"state":0,"wave":1,"hp":90,
 "weapon_ready":1,"player":{"x":26.5,"y":11.5,"dx":0.0,"dy":-1.0},
 "enemies":[{"x":24.3,"y":9.8,"type":0,"hp":2,"ai":1,"los":1}]}
```
`state` is `G_PLAY`/`G_OVER`/`G_WIN` (0/1/2). `type` and `ai` use the header's enemy
constants. `los` is the game's own `has_los()`, so line of sight is not reimplemented in
Python.

### Agent -> game (stdin, one line per change)

```
C <forward> <back> <strafe_left> <strafe_right> <turn_left> <turn_right> <fire>
Q
```
Each field is `0` or `1`. The last `C` line stays in force until the next one. `Q` exits
cleanly through `exit_game`. Parsing uses `ft_split` and `ft_atoi`, with no JSON in C.

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
   "KITE":{"what":"Walk backwards while facing and shooting the nearest threat.","when":"threats are close and there is open space behind","not_for":"being cornered"},
   "RETREAT":{"what":"Turn away and run toward open space.","when":"health is low, or you are being hit by more than one threat","not_for":"a single wounded threat you can finish"},
   "SEARCH":{"what":"Move toward the remaining threats that are out of view.","when":"no threat is in view but some remain","not_for":"any threat in view"}}}}
```

### Controller (code, every observation)
- **Aim:** turn toward the chosen target's bearing, with a dead zone of about the hitscan
  half-width (`perp < 0.5`, R4). **Fire** when the target is in front, `perp < 0.5`, within
  10 cells, `los=1` and the weapon is ready. This mirrors `combat.c`.
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
- **Idle policy:** sends nothing.

### Jev policy
- Decide every 0.5 s, or at once when a new wave starts or health drops a band, with at most
  one request in flight.
- Apply the answer only if `confidence >= θ`; θ starts at 0.6 and is tuned in T8.
- Retries: the SDK's `RetryPolicy`, plus one attempt timeout of 1.5 s. A late answer is
  discarded if a newer one has already been applied.
- Budget: cumulative `usage.cost` per run; stop calling at the cap and fall back to the
  scripted rules.

### Logs (JSONL, one file per episode, under `agent/runs/`, gitignored)
- `episode.jsonl`: per-second summaries.
- `decisions.jsonl`: `t`, the state sent, `answers`, `confidence`, `model`, `input_tokens`,
  `cost`, `latency_ms`, `applied`.
- `result.json`: outcome, survival seconds, wave reached, kills, damage taken, and the config
  sha256.

## Evaluation protocol (mirrors the `libros` dev/test discipline)
- Seeds 1-20 are **development**: tune the criteria and θ there only.
- Seeds 101-120 are **test**. Before running them, freeze the config (sha256 of the question,
  bands, θ and controller constants).
- Each policy runs once per test seed on `subject_map`, with a 180 s cap.
- Report per policy:
  - n and wins, with a Wilson 95% interval;
  - survival median and IQR;
  - waves cleared;
  - for Jev: cost per episode and latency p50/p95.

## Risks & mitigations
- **Jev latency is unknown** (R2). If p95 > 500 ms, tactics lag behind the fight. Measure it
  in T6 before tuning. If it is too slow, decide on events only instead of every 0.5 s.
- **The scripted policy may beat Jev.** That is a valid result (R3). The report says so plainly.
- **aarch64 vs x86_64** (R1). Run the final AC1 and a smoke episode on x86_64 before any
  submission-related step.
- **The three replaced files drift from the deliverable's.** Each copy starts with a comment
  naming the source file and base commit it mirrors. AC1 catches edits to the originals, which
  would mean the copies need a look.
- **MiniLibX version.** Spec 001 pins it in the top-level Makefile. `agent/Makefile` reuses
  that same checkout (`minilibx-linux/libmlx.a`) rather than cloning its own.
- **Pipe back-pressure:** if Python stalls, stdout could block the game. The game writes
  observations with a non-blocking write and drops the frame's line on `EAGAIN`, counting the
  drops.
