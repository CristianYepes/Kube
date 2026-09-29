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
- [x] **T2** — `tests/check.sh` with every AC section, run against the **unchanged** code.
  Record `tests/baseline-main-34f4aff.txt` (the error message of every bad map).
  **Done when:** it runs end to end and **fails where the research says it should**:
  - the `'3'` map is rejected;
  - valgrind without suppressions shows still-reachable blocks;
  - the FPS-dependent movement differs across maps;
  - dead-code greps find hits.
  This proves each check can fail.
  **Done 2026-09-29.** The full run took 2 min 24 s on unchanged code. 6 sections failed,
  exactly the expected ones:
  - build: no pinned MiniLibX; a changed libft does not relink; configure re-runs;
  - map matrix: the `'3'` map; bonus maps in `good/`; `forbidden.cub`; no `bonus/`;
  - valgrind: 87,941 bytes still reachable, and 136 bytes definitely lost on `tex_wrong_size`;
  - movement: W for 2 s gives 3.0-4.7 cells against 2.4; Left for 1 s gives 2.4-2.8 rad
    against 1.8;
  - dead code: 7 symbols and 2 orphan assets;
  - README: `example.cub`, and no "click".

  4 passed, as they should: norminette; messages against the baseline; FPS (92 against 90);
  the 60 s smoke run. The mouse probe already reads 0.0300 rad, which must stay that way.

  Instrument fixes made during the task:
  - The probe's `sed` inserted a literal `&` instead of the matched call. That gave 0 fps, an
    impossible result, so it was fixed.
  - The configure check was timing-dependent (missed 1 time in 3). It now bumps the
    directory's mtime and catches it 3 times in 3.
  - Baseline FPS on `subject_map`: 90, 91, 90, so 90 was recorded.
- [x] **T3** — Maps: new `good/`, `bonus/` and `bad/` layout with `git mv`, the `'3'` fix
  (per T0), and `bad/invalid_char.cub`.
  **Done when:** the AC3 section passes, and adding a wrong map to `good/` makes it fail.
  **Done 2026-09-29.** `good/` holds 5 maps, `bonus/` 4 (`forbidden.cub` became
  `sprite_small.cub`) and `bad/` 26 (with the new `invalid_char.cub`). Both `'3'`s became
  `'2'`. The map matrix and the messages against the baseline pass. A bad map copied into
  `good/` makes the section fail for both binaries.
- [x] **T4** — Makefile: pinned MiniLibX, an order-only prerequisite, libraries as
  prerequisites.
  **Done when:** the AC6 section passes (a second make is silent, the pinned commit is
  checked out, touching libft relinks, and `make fclean && make bonus` works).
  **Done 2026-09-29.**
  - `MLX_COMMIT` holds the full SHA of `f07d00f`, checked out after a full clone.
  - `$(MLX): | $(MLX_PATH)`, so the directory no longer triggers MiniLibX.
  - `$(LIBFT): FORCE` calls libft's own make, which prints nothing when up to date.
  - `$(NAME)` and `$(NAME_BONUS)` depend on both libraries.
  - A fresh clone lands on `f07d00f`, a second `make` and `make bonus` print nothing, and the
    build section passes.
  - Also, `.gitignore` gained the build outputs (research defect 9).
- [x] **T5** — Clean shutdown: `mlx_destroy_display` plus `free(mlx)` in `destroy_game`, and
  the `init_mlx` failure path.
  **Done when:** the AC2 section passes without `mlx.supp` for both binaries, with ESC and
  close-button exits. Then `mlx.supp` is deleted, or reduced to the documented exact stacks,
  and the decision is recorded in `research` as R9.
  **Done 2026-09-29:** see research R9. 0 bytes in use in every case, with no suppressions
  file. `mlx.supp` was deleted. Both edited functions stay within the norm (19, 23 and 18
  lines), and norminette reports OK.
- [x] **T6** — Movement by time: shared `tick_clock`, `last_time` in the mandatory `loop()`,
  per-second `MOVE_SPEED` and `ROT_SPEED`, `rotate_player` taking an angle, `MOUSE_SENS`.
  **Done when:** the AC1 section passes: the same distance within 10% on `minimal` and
  `test_map`, in both binaries, and the rotation and mouse checks.
  **Done 2026-09-29.** W for 2 s gives 2.42 and 2.43 cells (mandatory) and 2.30 and 2.39
  (bonus), against 2.4 expected; before, 3.0-4.7. Left for 1 s gives 1.82 rad in both, against
  1.8; before, 2.4-2.8. The mouse is unchanged at 0.0300 rad. Norminette passes on the five
  edited files. Performance cost: none. An A/B of the original code and this one gives 75-76
  against 76-77 fps on `minimal`; see research R10.
- [x] **T7** — Dead code and orphan assets (verified list, plus the full sweep).
  **Done when:** the AC5 section passes and the sweep report lists 0 unexplained findings.
  **Done 2026-09-29.**
  - Removed from the verified list:
    - `weapon.c`, with its Makefile entry, prototype and call;
    - `BREAK`, `CONTINUE` and `DEATH_TIME`;
    - `E_DEAD` and its 2 checks;
    - `t_sprite.anim_timer`, `.frame_idx` and `.type`;
    - `sprite_2.xpm` and `shotgun_fire3.xpm`.
  - Automatic sweep of 67 defines, 77 functions and 46 files: 0 findings.
    - On the original code it finds 5 of the 8 known items, which proves it can find them.
    - Its blind spots were checked by hand: fields sharing a name across structs, states that
      are tested but never set, and empty functions (this search does find `render_weapon`
      on the original).
  - **New finding, removed:** `t_enemy.timer` is written once in `waves.c` and never read. It
    hid behind `t_weapon.timer`.
  - Norminette reports 0 errors (94 files). Dead code, maps, messages and the 60 s smoke run
    all pass.
- [x] **T8** — README: paths, the Maps section, controls and the Tests line.
  **Done when:** the AC4 section passes.
  **Done 2026-09-29.** The examples point to `maps/good/minimal.cub` and
  `maps/bonus/subject_map.cub`. Left mouse click was added to the controls. New "Maps" and
  "Tests" sections cover Linux, and macOS through `dev/dev.sh`. The AC4 section passes.
- [x] **T9** — Full regression: `dev/dev.sh check` from a clean container.
  **Done when:** every section passes. That includes AC7 (the messages equal the baseline,
  norminette 0, the 60 s bonus smoke run, FPS within 15%), and one screenshot of the bonus
  looks as before.
  **Done 2026-09-29.**
  - From a fresh container (with a fresh pinned MiniLibX clone), `dev/dev.sh check` passes
    all 10 sections in 2 min 30 s.
  - W for 2 s: 2.41-2.43 cells. Left for 1 s: 1.83 rad. Mouse: 0.0300 rad. FPS 76 against
    75.
  - Screenshots of the bonus, idle and firing, look as before (zombies, gun, minimap,
    health bar, muzzle flash).
- [x] **T10** — x86_64 check (done emulated; a campus machine remains the final word): `make`, `make bonus`, the map matrix and
  valgrind.
  **Done when:** it passes there.
  **Done 2026-09-29 on emulated x86_64** (QEMU through Colima's binfmt).
  - The binaries' ELF machine is x86-64. The map matrix, the messages against the baseline,
    and valgrind (all four cases) pass. norminette passes. The build passed without relinking,
    with the pinned commit, and relinked when libft changed.
  - Limit: under emulation `cc1` segfaults now and then, in a different file each time
    (`ft_memcmp.c`, `utils.c`). 2 of 3 full rebuilds succeed. That is QEMU, not the code, but
    one clean `make re` on a real campus machine is still worth doing.
  - Timing checks (movement, fps, smoke) are not meaningful under emulation; they were run
    natively.
  - Cleanup: the x86_64 container was removed and `ubuntu:22.04` restored to arm64. The pull
    used a temporary empty `DOCKER_CONFIG`, because `~/.docker/config.json` points to a
    `docker-credential-desktop` helper that is not installed. That file was not touched.
- [ ] **T11** — Merge `feature/game-ready` into `main` locally (decided on 2026-09-29).
  **Done when:** `main` contains every commit of the branch, and `dev/dev.sh check` passes on
  `main`.
- [ ] 🔑 **T12** — Push `main` to GitHub.
  **Done when:** the owner gives the explicit OK at that moment.
- [ ] **T13** — Create `feature/jev-agent` from the updated `main` for spec 002.
  **Done when:** the branch exists and `specs/002-jev-agent/tasks.md` T0 is the next step.
