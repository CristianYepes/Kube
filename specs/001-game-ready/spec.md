# Spec 001 — Game ready (v0.2)

> WHAT and WHY only. HOW lives in plan.md; facts in ../research-2026-09-28.md (wins on
> conflict: see "Observed defects" and R8).
>
> Comes **before** spec 002 (the Jev agent). The owner's words: leave the game ready before
> it starts playing itself.

## Problem & goal

The game works, but several things make it less solid than it looks:
- the player's speed depends on the machine's frame rate;
- the X11 connection is never closed, which a suppressions file hides;
- one "good" map is rejected by every build, and the map folders mix mandatory-only and
  bonus-only cases;
- the README runs a map that does not exist;
- there is dead code, and there are unused assets;
- MiniLibX is unpinned.

We want the game fair on any machine, clean under valgrind without excuses, and proven by
tests, **without changing how it plays or what the parser answers**. The agent in spec 002
will also rest on this.

**Success signal:** one command (`dev/dev.sh check`) runs the whole suite in the Linux
container and passes, covering:
- build and no relink;
- norminette;
- the map matrix for both binaries;
- valgrind without suppressions;
- the movement check across maps with different frame rates.

## Scenarios / user stories

- As a player, I want the same speed on a slow map and a fast one, so that the game feels the
  same everywhere.
- As an evaluator, I want `valgrind` without any suppressions file to show a clean exit, so
  that there is nothing to argue about.
- As a developer, I want one command that tells me whether I broke the parser, the build or
  memory, so that I can change code without fear.
- As a new reader, I want the README's commands to work as written.

## Functional requirements

- **FR1 — Frame-rate independent movement.** WHEN a movement or rotation key is held, THE
  SYSTEM SHALL move and turn the player by an amount proportional to elapsed time, in both
  binaries.
  - Speeds match the game's existing 60-fps reference: the one the zombies already use
    (Decision 2).
  - Mouse rotation keeps its current sensitivity per pixel.
- **FR2 — Clean shutdown.** WHEN the game exits normally (ESC or the window's close button) or
  through an error after the display was opened, THE SYSTEM SHALL release the display
  connection and all its own memory.
- **FR3 — Map fixtures that mean what they say.**
  - Maps valid for both binaries, maps valid only for the bonus, and maps invalid for both
    SHALL live in separate folders.
  - Every map SHALL behave as its folder says.
  - The `'3'` map SHALL be fixed (Decision 1).
- **FR4 — Automated checks.** One command SHALL build everything and run all checks in the
  Linux container, failing on any mismatch.
- **FR5 — Accurate README.** Every command and path in the README SHALL exist and work. The
  controls table SHALL list every control the game has.
- **FR6 — No dead code or orphan assets.** Code that can never run, constants and fields that
  are never read, and asset files nothing loads SHALL be removed. The exceptions are the ones
  the owner decides to keep.
- **FR7 — Reproducible build.**
  - MiniLibX SHALL be built from a pinned commit.
  - A second `make` or `make bonus` SHALL do nothing.
  - A changed library SHALL relink the binary that uses it.
- **FR8 — No regressions.**
  - The parser's accept/reject decisions and error messages stay the same, except the fixed
    map.
  - Norminette stays at 0 errors.
  - `-Wall -Wextra -Werror` still builds.
  - Gameplay rules are unchanged: waves, damage, weapon, enemy speed.

## Acceptance criteria (verifiable)

- **AC1 (FR1)** — The movement probe holds W for 2 s. The distance is the same within 10% on
  `minimal` (measured 74-78 fps) and `test_map` (44-56 fps), in both binaries, and it is
  2.4 cells ± 10%.
  - Holding the left arrow for 1 s turns 1.8 rad ± 10%.
  - A 100-pixel mouse move still turns 0.03 rad ± 10% (bonus).
- **AC2 (FR2)** — `valgrind --leak-check=full --show-leak-kinds=all` with **no** suppressions
  file, for both binaries, with an ESC exit and a close-button exit, reports definitely 0,
  indirectly 0 and still reachable 0 bytes, and 0 errors.
  - If libX11 keeps internal blocks that the program cannot free, the exact remainder and its
    stack are documented. The owner then accepts it, or not, in T5.
  - Error paths still report 0 bytes in use at exit.
- **AC3 (FR3, FR4)** — `dev/dev.sh check` reports 0 mismatches over every map:
  - `maps/good/*` accepted by both binaries;
  - `maps/bonus/*` accepted by the bonus and rejected by the mandatory binary with
    `Invalid character in map`;
  - `maps/bad/*` rejected by both, printing `Error` first and exiting 1.
  - Adding a deliberately wrong map makes the check fail. That proves it can fail.
- **AC4 (FR5)** — A check extracts every `maps/...` path from `README.md` and each exists.
  Every key handled in `input.c` and `input_bonus.c`, plus the mouse, appears in the controls
  table.
- **AC5 (FR6)** — `grep` over `sources/` and `includes/` finds 0 occurrences of `BREAK`,
  `CONTINUE`, `DEATH_TIME`, `E_DEAD`, `render_weapon`, `anim_timer` and `frame_idx`. A check
  lists every `.xpm` in the repo and finds each one referenced by a map or a source file, so
  there are 0 orphans.
- **AC6 (FR7)**
  - After `make && make bonus`, a second `make && make bonus` prints nothing from MiniLibX and
    changes no mtime.
  - `git -C minilibx-linux rev-parse --short HEAD` equals the pinned commit.
  - Touching a libft source and running `make` relinks `cub3D`.
  - `make fclean && make bonus` builds from scratch.
- **AC7 (FR8)**
  - The rejection message for every bad map equals the message recorded on `main@34f4aff`
    (baseline file in `tests/`).
  - `norminette sources includes libft` exits 0.
  - A 60 s headless bonus run with xdotool input does not crash.
  - The FPS on `subject_map` stays within 15% of the baseline (75-105).

## Out of scope

- New gameplay: new enemies, door tactics, a second sprite type.
- Feel changes that were not asked for: diagonal speed normalization, a collision radius, new
  visuals.
- Anything of the agent (spec 002).
- Pushing to GitHub without the owner's explicit OK at that moment.

## Decisions (answered by the owner on 2026-09-29)

1. **The `'3'` map:** replace every `'3'` with `'2'` and delete `textures/sprites/sprite_2.xpm`.
2. **Speed reference:** the 60-fps reference the zombies already use (1.2 cells/s, 1.8 rad/s).
3. **Deliverable status:** the project has already been delivered. The owner decides to polish
   it on `feature/game-ready` and merge that into `main`. Pushing is confirmed separately.
4. **Unused textures:** delete `files/wall_cross.xpm`, `files/wall_pipes.xpm` and
   `textures/shotgun/shotgun_fire3.xpm`.
