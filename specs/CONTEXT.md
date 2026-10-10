# CONTEXT — cub3D that plays itself, like Jev plays Doom

> **Read this first.** It is written for someone, human or AI, who was not in the
> conversation where this started. It says what we want, why, what already exists, the
> rules, and how to run things today.
>
> **Implementing spec 002?** Go to `002-jev-agent/START_HERE.md`: reading order, rules,
> environment, new-machine setup, workflow, and the checklist in `002-jev-agent/tasks.md`.
> On `feature/jev-agentv1`, the root `CLAUDE.md` imports it, so Claude Code loads it by
> itself.
>
> ```
> specs/
>   CONTEXT.md                 this file
>   research-2026-09-28.md     verified facts for both specs (wins on conflict)
>   001-game-ready/            FIRST: leave the game solid (spec, plan, tasks)
>   002-jev-agent/             THEN: the game plays itself with Jev (spec, plan, tasks)
> ```
>
> Written 2026-09-28 from `main@34f4aff`; the "Jev in two minutes" facts were re-verified on
> 2026-10-03 (still `jev-1.13`). Spec 002's tasks were re-checked against the code on
> 2026-10-05, and the owner added decisions 5-8 the same day (`tasks.md` v0.6).
> - Spec 001 was built on branch `feature/game-ready` and merged into the local `main`. On
>   GitHub it lives on `feature/jev-agent` (`0ac5649`), "the base", which gained one fix on
>   2026-10-05 (`ad4244a`, strafing speed; see the end of this file).
> - Spec 002 is implemented on `feature/jev-agentv1`, created from the base.
> - **2026-10-06: the game is no longer handed in at 42.** The work goes on
>   `feature/jev-agentv1` alone, the base is only history, and the hard rule below about not
>   changing the game is retired (`002-jev-agent/tasks.md`, "Decided 2026-10-06").
>
> Facts are dated. Re-verify anything external (model ids, prices, versions) before relying
> on it.

## The goal

**Make cub3D play itself.** In the bonus zombie-survival mode, a program controls the
player, and the tactical decisions come from **Jev**, TypeSafe AI's decision model. It is the
same idea as TypeSafe's Doom demo, but with our own game and done carefully:
- the game state goes in as words;
- code aims, fires and moves;
- Jev picks the tactic;
- everything is measured against a player who does nothing and a hand-written rule policy.

**Order matters: spec 001 first.** The owner wants the game ready before it starts playing
itself. 001 fixes the defects found while reading the code (below), including the one the
agent depends on: movement that depends on frame rate. 002 starts from the commit where 001
is complete ("the base").

The goal is to **find out and measure**, not to prove that Jev wins. TypeSafe's own blog admits
that a non-AI bot could play Doom better. If our rule policy beats Jev, the report says so.

## Where the idea comes from

- **TypeSafe's launch blog**, section "Fun Demos: Doom"
  (https://typesafe.ai/blog/introducing-system-one-models-and-jev):
    - Jev plays Doom in real time from **structured text state, not images**;
    - about **10 queries per second, about $7/hour**;
    - "A non-AI doom bot could play better".
- **[lukaske/jev-doom-agent](https://github.com/lukaske/jev-doom-agent)**: a third-party
  experiment. Chocolate Doom in WebAssembly, plus a C bridge that serializes the game state and
  injects keys.
    - **It has no license: do not copy its code.** We reuse the pattern only.
    - What it gets wrong, and we must not repeat:
        - it does not pin the model version;
        - it computes `confidence` and ignores it;
        - its state is about 14,000 characters, mostly raw coordinates Jev cannot use;
        - its four independent questions can contradict each other;
        - it has no retries;
        - it was never shown playing a real game with Jev.
    - Detail in research R3.

## Jev in two minutes (everything you need; no outside notes required)

- **What it is.** A "System One" model that **decides and does not write**. You send a
  `state` (text or JSON) and typed questions. It returns typed answers with probabilities.
  Every question is evaluated independently and in parallel, in one call.
- **The three question types:**
    - **Choice**: pick one option from a map `option -> description`; returns `choice`,
      `probabilities` and `confidence`.
    - **Score**: position on 2-10 described levels; returns `score`, `probabilities` and
      `confidence`.
    - **Noul**: probability of "yes", from 0 to 1, with no `confidence`.
- **Rules that matter here:**
    - It **cannot count or do arithmetic**, and does not compare numbers reliably, so
      directions and distances go in as words computed by code.
    - It **reads literally**: instructions must name the state paths, for example
      `` `threats.nearest.distance` ``.
    - The question id is **not** seen by the model; the whole question goes in `instructions`.
    - **Answers to different questions are not mutually coherent**, so use one tactical
      Choice, not several axes.
    - A threshold tuned for a Noul does not transfer to a Choice.
    - **A Choice leans toward its first option** (docs, 2026-10-03), so the order of the
      tactics is not neutral. T8 of spec 002 measures it.
    - `confidence` measures how concentrated the distribution is. It is **not** the
      probability of being right.
    - It is trained mostly on English, so all instructions and state keys are in English.
- **Access we use:** OpenRouter, model **`typesafe/jev-1.13`**, which answers as
  `typesafe/jev-1.13-20260917`. **$0.042 per million input tokens; output is free.** Verified
  on 2026-09-28 and 2026-09-23.
    - Pin this id. The floating alias moves without notice, and `typesafe/jev-router` is a
      different product.
    - Python SDK: `typesafe-sdk` 0.7.2 (MIT, Python >= 3.10).
- **Traps already paid for** in a previous project (`~/jev/libros`, 419 real calls):
    - Through OpenRouter, the `x-typesafe-request-id` header is missing and
      `SystemOneResponse.request_id` **raises**. Read `raw_http_response.headers.get(...)`.
    - `models.list()` fails through OpenRouter.
    - Responses include `usage.cost`.
    - Log the `model` of every answer.
- **Unknown:** Jev's latency from here. The docs say about 100 ms and the blog 70-500 ms. It
  is the first thing to measure (spec 002, task T6b).
- Limits: 64k tokens per request (32k for state plus the longest question), 100K tokens/s
  and 80 requests/s (read 2026-10-03; they were 250K tokens/s and 1,200 requests/min on
  2026-09-22). These can change without notice.

## The game the agent plays (cub3D_bonus, read from the code)

- **Waves:**
    1. 3 grunts with 2 hp.
    2. 4 runners with 1 hp.
    3. 1 boss with 8 hp, and fog turns on.
    - Clearing wave 3 wins. Player hp 0 loses. `R` restarts.
- **Zombies** chase the player along a BFS flow field and bite for 10 hp per second when
  adjacent.
- **The player's gun** is hitscan: it hits the nearest enemy in front, within half a cell of
  the aim line, within 10 cells and with line of sight. Each shot does -1 hp, with a 0.6 s
  cooldown. Ammo is unlimited, and there are no pickups.
- **Doors** (`D`, toggled with `E`) block zombies and line of sight. Door tactics are out of
  scope for v1.
- **Randomness** is an LCG seeded from the clock, so runs are not reproducible yet (the agent
  build adds a seed). Only wave spawns draw from it (`waves.c`).
- **Fixed by spec 001:** the player used to move and turn **per frame**, while zombies move
  per real time. The frame rate was measured at 44-105 fps depending on the map, so player
  speed varied up to 2.4x. Spec 001 made player movement time-based (1.2 cells/s,
  1.8 rad/s), and spec 002 relies on it.
- Full table with file references: research R4.

## The design in one picture (detail in 002-jev-agent/plan.md)

```
 Mac host: Python agent (key stays here)          Linux (container on the Mac, or native)
  reader <── one JSON observation per frame ───── cub3D_agent (Xvfb)
  features -> state in words                        polls stdin, never waits
  controller: aim, fire, move ── command line ───►  applies last command each frame
  policy every 0.5 s: idle | scripted | Jev (async, confidence-gated, budget-capped)
```

- `cub3D_agent` is a **third binary with its own `agent/Makefile`**. It compiles the
  deliverable's sources, replacing three files (`main.c`, `mlx.c`, `game_loop.c`) with copies
  in `sources/jev/`. **Spec 002 edits no existing file.**
- Jev chooses one of **ENGAGE, KITE, RETREAT, SEARCH**. Code does everything numeric.
- Evaluation mirrors the `libros` discipline:
    - tune on development seeds (1-20);
    - freeze the config with a sha256;
    - measure once on test seeds (101-120);
    - compare three policies (idle, scripted, Jev) on the same seeds.

## Hard rules (do not break)

1. **RETIRED 2026-10-06: the game is no longer handed in at 42,** so it is no longer
   protected. It may change on `feature/jev-agentv1` when a task needs it, keeping
   `tests/check.sh` passing. Until then: **the 42 deliverable changes only in spec 001, on
   purpose, and under guards.** Norminette stays at 0 (it is 0 errors on `main`, verified). The parser's answers and messages match a
   baseline recorded on `main@34f4aff`. There is no relink, valgrind is clean, and gameplay
   rules are unchanged. **Spec 002 does not change it at all:** `make` and `make bonus` must
   produce byte-identical objects to the base.
2. **All files, code, comments and commit messages in English.** Chat with the owner (Cristian)
   is in Spanish.
3. **Aggressive YAGNI.** Nothing speculative: no placeholder headers, no constants before use,
   no directories before their first file.
4. **Do not push, and do not commit beyond what the owner asked.** The repo is shared with
   Rodrigo (pair project).
5. **The API key is never printed, logged, committed, or put in the container or its image.**
   The agent runs on the Mac and reads `OPENROUTER_API_KEY` from its environment.
6. **Verify, don't recall.** Every number in a report comes from a run, and computed numbers
   are labeled as calculations.

## How to run things today (verified 2026-09-28 on this Mac)

The Mac cannot link this MiniLibX (X11) natively, so a Linux VM is used:
- Colima 0.9.1;
- Docker server 28.4.0;
- Ubuntu 22.04, aarch64.

**Use `dev/dev.sh`** (`up | sync | build | check | down`, added by spec 001). The manual recipe
below is what it automates, kept for reference:

```dockerfile
FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential git ca-certificates \
      libx11-dev libxext-dev libbsd-dev zlib1g-dev \
      xvfb x11-apps imagemagick xdotool valgrind \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /kube
```

```bash
colima start --cpu 2 --memory 4 --disk 20          # Linux VM (stop: colima stop; remove: colima delete)
docker build -t kube-dev <dir-with-the-Dockerfile>
docker run -d --name kube-test kube-dev sleep infinity
git archive HEAD | docker exec -i kube-test tar -x -C /kube   # copy the tree in (see gotcha)
docker exec kube-test bash -c 'make && make bonus'
docker exec kube-test bash -c 'Xvfb :99 -screen 0 1280x720x24 >/dev/null 2>&1 &
  sleep 1; DISPLAY=:99 ./cub3D_bonus maps/bonus/subject_map.cub'
# input:       DISPLAY=:99 xdotool keydown w; sleep 1; xdotool keyup w; xdotool key Up
# screenshot:  DISPLAY=:99 xwd -root -silent | convert xwd:- /tmp/shot.png ; docker cp kube-test:/tmp/shot.png .
```

What those commands showed:
- both binaries build with `-Wall -Wextra -Werror`;
- every map in `maps/bad/` exits 1 with `Error` in both binaries (the layout since spec 001);
- the bonus runs headless and takes xdotool keys;
- a player who does nothing died in about 10 s (one run);
- a pipe from Python on the Mac through `docker exec -i` costs 0.2 ms per line.

Gotchas:
- Colima shares only `$HOME` with the VM, so a bind mount from `/private/tmp` shows up
  **empty**. Copy the tree with `git archive`.
- The VM is **aarch64**, and 42 machines are x86_64. Do a final check on x86_64 (spec 001
  T10).
- The Makefile clones MiniLibX **unpinned** from master. Today that is `f07d00f`; spec 001
  pins it.

On native Linux (Ubuntu/Debian): `sudo apt install libx11-dev libxext-dev libbsd-dev xvfb
xdotool`, then the same `make`, `make bonus` and Xvfb commands without `docker exec`.

## Status and next step

- **Spec 001 (game-ready): done on 2026-09-29.** Every task is closed in
  `001-game-ready/tasks.md`, each with its evidence.
    - `dev/dev.sh check` passes all 10 sections from a fresh container.
    - The x86_64 build was checked under emulation. One clean `make re` on a campus machine
      remains a good idea.
    - It is merged into the local `main`. On GitHub it lives on `feature/jev-agent`, pushed
      on 2026-09-29. `origin/main` stays at `34f4aff` until the owner decides.
- **Spec 002 (Jev agent): in progress.** On 2026-10-06 phases 1 and 2 are done (T0 to T3e: the
  C bridge and its 24 checks) and L1 and L2 passed on the owner's Linux. phase 3 is built (T4a to T5c: the Python package, the bridge, the semantic state, the
  controller, the policies and the episode runner, with the first ten runs in `agent/runs/`).
  The checkpoint **L3 passed on the owner's Linux** (234 tests, the `local` runner, and the game
  seen on the real display). **T6, T6b and T7 are done**: the Jev client, the spend ledger, the
  first 50 paid calls (p50 309 ms, p95 514 ms, $0.00156; R12) and the Jev policy in the game loop,
  whose first real episode won in 13.6 s with 26 of 28 answers applied (R13). The owner decided
  to keep the 0.5 s cadence plus events and to start the confidence threshold θ at 0.3.
  **L4 passed on the owner's Linux on 2026-10-08**: 4 paid Jev episodes, all won, and Jev's
  latency there was higher (p50 553 ms against 318 ms on the Mac; R14). **T8 and T8b are done: the Jev config is frozen** (R15, R16) after one
  tuning of the wording, and no map makes the rule bot lose. **T9 is done (2026-10-10): the final evaluation on the test seeds 101-120** (R17). On
  `subject_map` and on `pillars`, Jev and the rule bot tie: 20 of 20 wins each, no damage, no difference in the time to win; idle lost 40 of 40; Jev cost
  about $0.001 an episode. **T10 is done (2026-10-10): the regression passes on the Mac** (`dev/dev.sh check` `ALL PASSED`, `check_bridge.py` 24 of 24,
  547 tests). **Next: L5**, the last Linux checkpoint, run by the owner.
    - **The base** was `feature/jev-agent`: 001 complete, plus the strafing fix.
    - **Implementation branch:** `feature/jev-agentv1`, created from the base, and since
      2026-10-06 the only working branch.
    - T0 answered (`spec.md`, "Decisions"): `subject_map`, dev seeds 1-20 and test seeds
      101-120, 180 s per episode, $1 total, the key from `~/jev/libros/.env`.
    - Decisions 5-8 (2026-10-05):
      - the C bridge lives in `sources/jev/`;
      - development runs on the Mac through Colima, and each phase is re-checked on the
        owner's Linux (L1-L5);
      - every run's logs are committed, to study how the game gets beaten;
      - harder maps with obstacles may follow v1, in `agent/maps/`.
    - Decision 9 (2026-10-06): the game is no longer handed in at 42, so the rules that
      protected it are retired (`002-jev-agent/tasks.md`, "Decided 2026-10-06").
    - To resume: `002-jev-agent/START_HERE.md`, then `tasks.md` from L5.
- Tooling now in the repo:
    - `dev/dev.sh up|sync|build|check|down`, the Linux container;
    - `tests/check.sh`, with one section per acceptance criterion of 001;
    - `tests/baseline-main-34f4aff.txt`.

## Defects that spec 001 fixed (kept for history)

1. `maps/good/subject_map_sprites.cub` contains `'3'`, which no build accepts.
2. Three "good" maps are bonus-only, and `maps/bad/forbidden.cub` is only bad for the
   mandatory binary.
3. The player moves per frame while zombies move per real time (see above).
4. `README.md` runs `maps/good/example.cub`, which does not exist.
5. There are unused assets.
6. MiniLibX is unpinned.
7. The display is never closed: 87,941 bytes are still reachable at exit, hidden by
   `mlx.supp` (R8).
8. The Makefile re-runs MiniLibX's configure on every `make`, and the libraries are not
   prerequisites of the binaries (no relink happens, R8).
9. There is dead code (verified list in the research).

All of them are fixed, except the part of item 5 that was wrong: `wall_cross.xpm` and
`wall_pipes.xpm` are used by the bad maps, so they stay. Two more were found and fixed along
the way:
- 136 bytes definitely lost on the texture-failure path;
- build outputs that were not in `.gitignore`.

One more was found later, by spec 002's bridge checks, and fixed on the base on 2026-10-05
(`ad4244a`): strafing went along `plane`, which is 0.66 long, so A and D were a third slower
than W and S (0.79 against 1.2 cells/s). Details: research, "Observed defects", item 11.

Details: research, "Observed defects", R8-R10, and `001-game-ready/tasks.md`. Spec 002 must
not touch the deliverable; a defect it finds in it is fixed on the base branch, as above.
