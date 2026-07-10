*This project has been created as part of the 42 curriculum by cyepes, rmonfort*

# cub3D

## Description

cub3D is a raycasting engine inspired by Wolfenstein 3D (1992), the first true first-person shooter. The program renders a 3D perspective view of a maze defined in a `.cub` scene file, using the DDA raycasting algorithm and the MiniLibX graphics library.

The player can navigate the maze in real time with textured walls (different textures per cardinal direction), configurable floor/ceiling colors, smooth movement with wall-sliding collisions, and keyboard/mouse controls.

## Instructions

### Requirements

- Linux (Ubuntu/Debian)
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
./cub3D maps/good/example.cub
./cub3D_bonus maps/good/example.cub
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
| R | Restart (bonus) |

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
- Debugging and fixing compilation errors
- Code review for norm compliance and memory leak detection
- Identifying and fixing edge-case bugs in the game simulation

All generated code was reviewed, tested, and validated by the team before integration.