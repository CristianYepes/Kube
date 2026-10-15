*This project has been created as part of the 42 curriculum by cyepes, rmonfort*

# cub3D

## Description

cub3D is a raycasting engine inspired by Wolfenstein 3D (1992), the first true first-person shooter. The program renders a 3D perspective view of a maze defined in a `.cub` scene file, using the DDA raycasting algorithm and the MiniLibX graphics library.

The player can navigate the maze in real time with textured walls (different textures per cardinal direction), configurable floor/ceiling colors, smooth movement with wall-sliding collisions, and keyboard/mouse controls.

## Jev plays cub3D (this branch)

This branch adds an agent that plays the zombie mode of `cub3D_bonus`. Every half second [Jev](https://docs.typesafe.ai),
TypeSafe's decision model (`typesafe/jev-1.13` through OpenRouter), picks one of four tactics, and plain code aims, shoots
and moves:

| Tactic | What the code does |
|--------|--------------------|
| `ENGAGE` | Stand and shoot the nearest zombie |
| `KITE` | Back off while shooting |
| `RETREAT` | Run to the open area farthest from the zombies |
| `SEARCH` | Go after the zombies out of view |

The baseline picks from the same four with hand-written rules: low health and a zombie close, `RETREAT`; a zombie close,
`KITE`; one in view, `ENGAGE`; otherwise `SEARCH`.

**Result.** 20 held-out seeds on each of two maps, measured once with a frozen configuration: Jev and the rules both won
40 of 40 without taking damage, and their time to win could not be told apart (sign test, p = 0.82 on both maps). Jev cost
about $0.001 per game and picked the tactic the rules would have picked in 91% and 98% of its decisions. Report:
[`agent/runs/eval-20261010T122708Z-darwin/report.md`](agent/runs/eval-20261010T122708Z-darwin/report.md).

**Run it** on Linux (setup: [`specs/002-jev-agent/START_HERE.md`](specs/002-jev-agent/START_HERE.md), section 2b):

```bash
make -C agent        # builds agent/cub3D_agent
cd agent && uv sync
uv run kube-agent run --runner local --policy scripted --seed 3 --strip
```

`--policy jev` plays with Jev. It is paid and needs `OPENROUTER_API_KEY`: keep the key in a file outside the repo that only
you can read, and load it for that one command:

```bash
( set -a; . ~/.config/kube/.env; set +a; uv run kube-agent run --runner local --policy jev --seed 3 --strip )
```

`--strip` shows over the game window who is playing, the tactic and the keys being pressed (it needs
`sudo apt install python3-gi gir1.2-gtk-3.0`). Every run is logged in `agent/runs/`, and `uv run kube-agent spend` adds up
what Jev has cost. How it was built and measured: [`specs/`](specs/).

## Instructions

### Requirements

- Linux (Ubuntu/Debian). On macOS, use the Linux container described in [Tests](#tests).
- X11 development libraries (`libxext-dev`, `libx11-dev`)
- `cc` compiler with `-Wall -Wextra -Werror`
- `make`

### Compilation

```bash
make        # Builds the mandatory binary: cub3D
make bonus  # Builds the bonus binary: cub3D_bonus
make clean  # Removes object files
make fclean # Removes object files and executables
make re     # Full recompile
```

### Execution

```bash
./cub3D maps/good/minimal.cub
./cub3D_bonus maps/bonus/subject_map.cub
```

### Controls

| Key | Action |
|-----|--------|
| W/A/S/D | Move forward/left/backward/right |
| Left/Right arrows | Rotate camera |
| ESC | Exit |
| E | Open/close doors (bonus) |
| M | Toggle minimap (bonus) |
| Mouse | Rotate camera (bonus) |
| Up arrow | Shoot (bonus) |
| Left mouse click | Shoot (bonus) |
| R | Restart (bonus) |

### Maps

| Folder | Meaning |
|--------|---------|
| `maps/good/` | Valid for both binaries |
| `maps/bonus/` | Valid for `cub3D_bonus` only (doors `D`, sprites `2`); `cub3D` rejects them |
| `maps/bad/` | Invalid for both: each one exits with `Error` and a message |

### Tests

`tests/check.sh` builds both binaries and checks the Makefile (no relink, pinned MiniLibX),
norminette, every map, the error messages, valgrind without suppressions, the player's speed
across maps with different frame rates, dead code and this README. On Linux it needs Xvfb,
xdotool, valgrind and norminette:

```bash
Xvfb :99 & DISPLAY=:99 bash tests/check.sh
```

On macOS the same checks run in a Linux container (Docker, e.g. through Colima):

```bash
dev/dev.sh up      # build the image and start the container
dev/dev.sh check   # sync the tree, build, run tests/check.sh
dev/dev.sh down    # remove the container
```

## Development Phases

| Phase | Description |
|-------|-------------|
| 1 | Parser: `.cub` file reading, identifier extraction, map validation (flood fill for closed walls) |
| 2 | MLX initialization: window, image buffer, XPM texture loading |
| 3 | Raycasting engine: DDA algorithm, one ray per screen column |
| 4 | Textured walls: N/S/E/W texture mapping, floor/ceiling colors |
| 5 | Controls: WASD movement, arrow rotation, wall-sliding collision |
| 6 | Bonus — Minimap: top-left overlay, wall/player/sprite rendering |
| 7 | Bonus — Doors: 'D' char in map, toggle with E, DDA-aware rendering |
| 8 | Bonus — Mouse rotation and animated sprites (billboard projection, z-buffer) |
| 9 | Mod — Zombie survival: 3 waves, enemy AI with BFS pathfinding, hitscan combat |

## Resources

### Raycasting

- [Lode's Raycasting Tutorial](https://lodev.org/cgtutor/raycasting.html) — DDA algorithm, wall texturing, sprite projection
- [Wolfenstein 3D Black Book](https://fabiensanglard.net/gebbwolf3d/) — engine architecture and rendering pipeline

### MiniLibX

- [42 MiniLibX Documentation](https://harm-smits.github.io/42docs/libs/minilibx) — API reference, hooks, image manipulation

### Pathfinding (enemy AI)

- [Red Blob Games — BFS](https://www.redblobgames.com/pathfinding/a-star/introduction.html) — BFS and flow field fundamentals
- [Flow Field Pathfinding](https://howtorts.github.io/2014/01/04/basic-flow-fields.html) — single BFS from target, gradient descent for agents

### Sprite Rendering

- [Lode's Sprite Casting](https://lodev.org/cgtutor/raycasting3.html) — billboard projection, inverse camera matrix, z-buffer clipping

### AI Usage

AI tools (Claude) were used as an implementation partner for:
- Building the Jev agent of this branch (`agent/`) and its specs (`specs/002-jev-agent/`, `specs/003-visual-pass/`)
- Debugging and fixing compilation errors
- Code review for norm compliance and memory leak detection
- Identifying and fixing edge-case bugs in the game simulation

All generated code was reviewed, tested, and validated by the team before integration.