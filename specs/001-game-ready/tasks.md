# Tasks 001 — Game ready

> Build order. 🔑 = needs the owner. Each task is closed by a check, not a vibe.
> Tests come first so that every fix is proven by something that could fail.

- [x] 🔑 **T0** — Answer the four open questions in `spec.md`. **Done 2026-09-29:**
  `spec.md` v0.2, section "Decisions". The work branch is renamed `feature/game-ready`.
- [x] **T1** — Dev container in the repo: `dev/Dockerfile` (R1 recipe, plus `python3-pip` and
  `norminette==3.3.60`) and `dev/dev.sh up|sync|build|check|down`.
  **Done when:** `dev/dev.sh up && dev/dev.sh build` builds both binaries, and `dev/dev.sh
  down` removes the container. The Colima VM is left to the owner.
  **Done 2026-09-29:**
  - `up` takes 43 s the first time and 0.2 s from the cache.
  - `build` builds `cub3D` and `cub3D_bonus`.
  - `sync` mirrors deletions: a probe file appears, and disappears after it is deleted.
    `minilibx-linux/` is kept.
  - `down` leaves no container.
  - macOS xattrs are dropped (`--no-xattrs --no-mac-metadata`), so the copy is silent.
- [ ] **T2** — `tests/check.sh` with every AC section, run against the **unchanged** code.
  Record `tests/baseline-main-34f4aff.txt` (the error message of every bad map).
  **Done when:** it runs end to end and **fails where the research says it should**:
  - the `'3'` map is rejected;
  - valgrind without suppressions shows still-reachable blocks;
  - the FPS-dependent movement differs across maps;
  - dead-code greps find hits.
  This proves each check can fail.
- [ ] **T3** — Maps: new `good/`, `bonus/` and `bad/` layout with `git mv`, the `'3'` fix
  (per T0), and `bad/invalid_char.cub`.
  **Done when:** the AC3 section passes, and adding a wrong map to `good/` makes it fail.
- [ ] **T4** — Makefile: pinned MiniLibX, an order-only prerequisite, libraries as
  prerequisites.
  **Done when:** the AC6 section passes (a second make is silent, the pinned commit is
  checked out, touching libft relinks, and `make fclean && make bonus` works).
- [ ] **T5** — Clean shutdown: `mlx_destroy_display` plus `free(mlx)` in `destroy_game`, and
  the `init_mlx` failure path.
  **Done when:** the AC2 section passes without `mlx.supp` for both binaries, with ESC and
  close-button exits. Then `mlx.supp` is deleted, or reduced to the documented exact stacks,
  and the decision is recorded in `research` as R9.
- [ ] **T6** — Movement by time: shared `tick_clock`, `last_time` in the mandatory `loop()`,
  per-second `MOVE_SPEED` and `ROT_SPEED`, `rotate_player` taking an angle, `MOUSE_SENS`.
  **Done when:** the AC1 section passes: the same distance within 10% on `minimal` and
  `test_map`, in both binaries, and the rotation and mouse checks.
- [ ] **T7** — Dead code and orphan assets (verified list, plus the full sweep).
  **Done when:** the AC5 section passes and the sweep report lists 0 unexplained findings.
- [ ] **T8** — README: paths, the Maps section, controls and the Tests line.
  **Done when:** the AC4 section passes.
- [ ] **T9** — Full regression: `dev/dev.sh check` from a clean container.
  **Done when:** every section passes. That includes AC7 (the messages equal the baseline,
  norminette 0, the 60 s bonus smoke run, FPS within 15%), and one screenshot of the bonus
  looks as before.
- [ ] 🔑 **T10** — x86_64 check on a campus machine: `make`, `make bonus`, the map matrix and
  valgrind.
  **Done when:** it passes there.
- [ ] **T11** — Merge `feature/game-ready` into `main` locally (decided on 2026-09-29).
  **Done when:** `main` contains every commit of the branch, and `dev/dev.sh check` passes on
  `main`.
- [ ] 🔑 **T12** — Push `main` to GitHub.
  **Done when:** the owner gives the explicit OK at that moment.
- [ ] **T13** — Create `feature/jev-agent` from the updated `main` for spec 002.
  **Done when:** the branch exists and `specs/002-jev-agent/tasks.md` T0 is the next step.
