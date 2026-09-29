# Plan 001 — Game ready

> HOW. Every choice is argued on ../research-2026-09-28.md ("Observed defects" 1-8, R1, R4,
> R8).

## Tech context

- C, `cc -Wall -Wextra -Werror`, MiniLibX (minilibx-linux, BSD-2-Clause), libft, `-lm`,
  norminette 3.3.60 (MIT). Allowed externals per the subject (project memory): `open close
  read write printf malloc free perror strerror exit gettimeofday`, math, MiniLibX, libft.
- Dev and test runtime on this Mac: Colima 0.9.1, Docker 28.4.0, Ubuntu 22.04 aarch64, with
  Xvfb, xdotool, xwd, ImageMagick and valgrind (R1). Final x86_64 check on campus.

## Constraints check

| Constraint | Respected? | How / why |
|---|---|---|
| Subject's allowed functions | ✅ | Only `gettimeofday` (already used), `mlx_destroy_display` (MiniLibX) and `free` are added |
| Norminette 0 errors | ✅ | Every edited file is re-checked by `dev/dev.sh check` |
| Gameplay unchanged | ✅ | Speeds are derived from the existing per-frame values at the 60-fps reference the zombies already use (R4). Waves, damage and weapon constants are untouched |
| Parser answers unchanged | ✅ | Error messages are compared against a baseline recorded on `main@34f4aff` (AC7) |
| English everywhere | ✅ | code, comments, docs, commit messages |
| YAGNI | ✅ | No new features. Tests only prove the FRs. One helper script for the container |
| No push without the owner's OK | ✅ | Work on `feature/game-ready`; merged into `main` when done; push only on an explicit OK |

## Chosen approach, per requirement

**FR1 — Movement by time** (defect 3):
- The bonus already computes `data->dt`, capped at 0.05 s (`tick_clock` in
  `render/game_loop.c`). Move `tick_clock` out of the `#ifdef BONUS` block so both
  `game_loop` variants call it.
- Set `data->last_time` in the mandatory `loop()` too, as the bonus already does.
- In `cub3d.h`, `MOVE_SPEED` becomes cells per second and `ROT_SPEED` radians per second,
  both at the 60-fps reference: `0.02 * 60 = 1.2` and `0.03 * 60 = 1.8`. They are written as
  plain values, with a comment giving the reference.
- `move_player` scales each step by `data->dt`.
- `rotate_player(t_player *p, double angle)` takes a final angle:
  - the keyboard passes `±ROT_SPEED * dt`;
  - the mouse passes `delta_x * MOUSE_SENS`, where `MOUSE_SENS 0.0003` (rad/px) equals
    today's `0.03 * 0.01`, so mouse feel is unchanged.
- The 0.05 s `dt` cap stays. It bounds a single step to 0.06 cells, so the per-axis collision
  check cannot be tunneled through.
- Rejected:
  - a frame-rate cap: `test_map` runs at 44-56 fps, so no cap at 60 can hold (R1);
  - fixing it only in the agent build: that leaves the human game unfair (spec 002 plan).

**FR2 — Clean shutdown** (defect 7, R8):
- `destroy_game` ends with `mlx_destroy_display(data->mlx); free(data->mlx);`, guarded by
  `data->mlx`.
- `init_game` calls `destroy_game` when `init_mlx` fails after `mlx_init` succeeded. Today
  that path returns without freeing.
- Then measure without `mlx.supp`:
  - if everything is 0, **delete `mlx.supp`**, because it becomes dead;
  - if libX11 leaves internal blocks, keep only suppressions matching those exact stacks and
    document them (AC2).

**FR3 — Maps** (defects 1-2). New layout, one rule per folder:

| Folder | Rule | Contents |
|---|---|---|
| `maps/good/` | accepted by both binaries | `minimal`, `spaces_inside`, `valid_ids`, `jail_test`, `test_map` |
| `maps/bonus/` | accepted by the bonus; mandatory says `Invalid character in map` | `doors_test`, `subject_map`, `subject_map_sprites` (`'3'` -> `'2'`, Decision 1), `sprite_small` (today `maps/bad/forbidden.cub`) |
| `maps/bad/` | rejected by both, `Error` + exit 1 | the other 25 current bad maps, plus a new `invalid_char.cub` with an `X`, so an invalid-character case exists for the bonus too |

The files are moved with `git mv`, so their history follows them.

**FR4 — Checks:**
- `dev/Dockerfile` is the verified recipe from R1, plus `python3-pip` and
  `norminette==3.3.60`.
- `dev/dev.sh up|sync|build|check|down`:
  - `sync` pipes `git ls-files -co --exclude-standard` through `tar` into the container,
    because Colima does not share `/private/tmp` (R1);
  - `check` runs `tests/check.sh` inside it.
- `tests/check.sh` has one section per AC. It exits non-zero on the first failed section and
  prints a summary.
- The movement and FPS probes apply a **temporary** print to the **container's copy** of
  `game_loop.c`, rebuild there, measure, and restore. This is the same method used for the
  FPS numbers in R1, and it never touches the tree.
- `tests/baseline-main-34f4aff.txt` holds the error message of every bad map as it was on
  `main`, recorded once in T2.

**FR5 — README** (defect 4):
- Example commands point to `maps/good/minimal.cub` (mandatory) and
  `maps/bonus/subject_map.cub` (bonus).
- A short "Maps" section explains the three folders.
- Add the left mouse click (fire) to the controls, and a "Tests" line for `dev/dev.sh check`.

**FR6 — Dead code** (defect 5, verified list):
- Delete `bonus/render/weapon.c`, its Makefile entry, its prototype and its call in
  `game_loop`.
- Delete the `BREAK`, `CONTINUE` and `DEATH_TIME` defines.
- Delete the `E_DEAD` define and its two checks: dead enemies are removed from the array, so
  the state can never be observed.
- Delete `anim_timer`, `frame_idx` and `type` from `t_sprite`, and their writes in
  `set_sprite`.
- Delete the orphan assets (Decisions 1 and 4): `sprite_2.xpm`, `wall_cross.xpm`, `wall_pipes.xpm` and
  `shotgun_fire3.xpm`.
- Before closing the task, re-run a full sweep: every `#define`, every struct field and every
  non-static function has at least one reader. Report any new finding instead of silently
  deleting it.

**FR7 — Makefile** (defects 6 and 8):
- `MLX_COMMIT = f07d00f`. Clone, then `git -C $(MLX_PATH) checkout --quiet $(MLX_COMMIT)`,
  which needs a full clone: the repo is small.
- `$(MLX): | $(MLX_PATH)`, an order-only prerequisite, so the directory's mtime no longer
  forces a rebuild.
- `$(NAME)` and `$(NAME_BONUS)` also depend on `$(LIBFT)` and `$(MLX)`.
- Rejected: vendoring MiniLibX into the repo (a large diff, a separate license file to carry).

## Risks & mitigations

- **Movement feel changes on the owner's machine** if its usual FPS is far from 60. The
  reference is 60 (Decision 2), and the constants are one line each if it needs tuning.
- **`dt` spikes** (window dragged, machine busy): the existing 0.05 s cap bounds the step.
- **libX11 still reports some blocks** after `mlx_destroy_display`: documented, with the
  exact stack (AC2). That is not the same as hiding everything with a broad suppression.
- **aarch64 vs x86_64:** T10 re-runs the check on a campus machine before merging.
- **Shared repo:** it is merged into `main` locally when 001 is complete. The push waits for
  the owner's explicit OK (T11).
