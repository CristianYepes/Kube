# LADO A — Cristian

**Parser · validación de args · controles · minimapa · puertas · TODA la lógica del mod zombi.**

> Regla mental: **A decide QUÉ pasa, B decide cómo se VE.** Tú no dibujas casi nada
> (solo el minimapa); tú validas la entrada, construyes el mapa en memoria, mueves al
> jugador y corres la simulación (oleadas, IA, combate, vida, estados, reinicio, pathfinding).

---

## Conceptos que debes dominar (para la defensa)
1. **Pipeline de parsing:** abrir `.cub` → leer líneas → separar identificadores (NO/SO/WE/EA/F/C) del mapa → validar todo → construir la rejilla `char **map`.
2. **Validación del mapa:** un solo jugador, chars válidos, mapa cerrado por muros.
3. **Movimiento con colisión:** `move_player` lee las teclas y avanza solo si `is_wall` no bloquea.
4. **Bucle de simulación del mod (`update_sim`):** oleadas → IA (FSM + pathfinding BFS) → combate (hitscan) → vida → estado de juego.
5. **Máquina de estados del enemigo (FSM):** IDLE → CHASE → ATTACK, con `else if` para no saltar varios estados en un frame.
6. **Pathfinding BFS (flow field):** una sola BFS desde el jugador rellena distancias; cada enemigo baja por el gradiente. Se recalcula solo al cambiar de celda o abrir/cerrar puerta.

---

## `sources/parsing/` — leer y validar el `.cub` (tu núcleo MANDATORY)

| Fichero | Funciones clave | Qué hace |
|---|---|---|
| `check_args.c` | `check_file`, `is_cub_file`, `is_readable_file` | Valida el argumento: que acabe en `.cub` y que se pueda abrir. |
| `parsing_data.c` | `parse_memory`, `parsing`, `count_lines`, `fill_lines`, `validate_map` | Orquesta el parseo: cuenta líneas, vuelca el fichero a `file_lines`, llama a todo y valida. |
| `get_file_data.c` | `get_file_data`, `line_type`, `extract_texture`, `process_line` | Clasifica cada línea (textura / color / mapa / vacía) y extrae los datos. |
| `fill_color_textures.c` | `fill_color_textures`, `parse_color`, `validate_colors`, `count_char` | Parsea los colores `F`/`C` (`R,G,B` 0-255) y guarda rutas de textura. |
| `check_textures.c` | `check_textures`, `validate_one_texture` | Comprueba que las 4 rutas de textura existan y sean `.xpm`. |
| `create_game_map.c` | `create_map`, `build_row`, `fill_grid`, `get_map_end`, `check_no_gaps` | Construye la rejilla `char **map` (rellena con muros, sin huecos verticales). |
| `check_map.c` | `check_map`, `set_player_spawn`, `set_player_at`, `set_ns`, `set_ew` | Cuenta jugadores (exactamente 1), fija pos/dirección inicial, guarda el spawn (para el restart). |
| `check_map_borders.c` | `check_map_borders`, `check_first_last_col` | Comprueba que el perímetro sean muros (mapa cerrado). |
| `parsing_utils.c` | `free_parsing`, `free_file_lines`, `skip_spaces`, `is_a_white_space`, `find_biggest_len` | Utilidades y **liberación de toda la memoria del parser**. |

---

## `sources/movement/` — controles y movimiento

| Fichero | Funciones clave | Qué hace | Lado |
|---|---|---|---|
| `input.c` | `key_press`, `key_release`, `handle_movement` | Teclas del **mandatory** (WASD + flechas + ESC). | A |
| `input_bonus.c` | `key_press_bonus`, `handle_movement` · `mouse_tracker`, `mouse_click` | Teclas bonus (M minimapa, E puerta, R restart, disparo). ⚠️ `mouse_*` es **de B** (rotación con ratón). | A + (ratón B) |
| `doors.c` | `toggle_door` | Abre/cierra la puerta de delante (`D`↔`O`) e invalida el flow field. | A (bonus puertas) |
| `player.c` | `move_player`, `try_move`, `rotate_player`, `is_wall`, `init_player` | Mueve y rota al jugador con **colisión** (`is_wall`). ⚠️ `is_wall` también lo usa el raycasting de B. | A |

---

## `sources/render/minimap.c` + `minimap_2.c` — minimapa (BONUS tuyo)

| Fichero | Funciones clave | Qué hace |
|---|---|---|
| `minimap.c` | `display_minimap`, `draw_map`, `draw_player`, `draw_square`, `draw_frame` | Dibuja el minimapa (celdas, jugador, marco) en una esquina. |
| `minimap_2.c` | `draw_sprite`, `in_bounds` | Helpers del minimapa (pinta sprites/enemigos, chequea límites). |

> Aunque vivan en `render/`, el minimapa es **tu bonus** (lógica de qué pintar del mapa).

---

## `sources/bonus/mod/` — la simulación del mod (tu zombi-survival)

| Fichero | Funciones clave | Qué hace |
|---|---|---|
| `sim.c` | `update_sim`, `tick_weapon`, `check_wave_advance` | **Orquestador de la simulación**: cada frame corre oleadas→IA→combate→vida→estado. |
| `waves.c` | `spawn_wave`, `place_enemy`, `get_wave_params`, `set_spawn_mode`, `clear_spawn_marks` | Genera cada oleada (1: grunts, 2: runners, 3: boss) en celdas válidas. |
| `utils.c` | `count_spawn_cells`, `pick_spawn_cell`, `is_valid_spawn`, `has_los` | Elige dónde aparecen (con línea de visión) y calcula LOS (línea de visión). |
| `enemy_ai.c` | `update_enemies`, `enemy_fsm`, `chase_player`, `get_speed`, `dist_sq` | **IA**: FSM (IDLE/CHASE/ATTACK) + persecución (usa el flow field con fallback recto). |
| `flow_field.c` | `update_flow_field`, `bfs_init`, `bfs_loop`, `cell_walkable` | **Pathfinding BFS**: rellena distancias desde el jugador (recalcula al cambiar de celda/puerta). |
| `flow_query.c` | `flow_dir`, `best_neighbor`, `get_flow_val` | Da al enemigo la dirección hacia la celda vecina con menor distancia (baja el gradiente). |
| `combat.c` | `try_fire`, `hitscan`, `find_target`, `hitscan_hit`, `kill_enemy` | **Combate**: disparo hitscan (rayo recto + LOS), elige objetivo, mata y compacta el array. |
| `player_state.c` | `update_player_hp`, `enemy_can_hit`, `check_game_state` | Vida del jugador (daño solo en melee + LOS) y transición G_PLAY/G_OVER/G_WIN. |
| `restart.c` | `restart_game`, `reset_player`, `reset_mod_state`, `reset_doors` | **Reinicio** con tecla R: vuelve al spawn, oleada 1, vida 100, enemigos/puertas reseteados. |

---

## El flujo de A (cómo encaja, de principio a fin)
1. `main` → `check_file` (args) → `parsing` (lee + valida + `create_map`).  ← arranque mandatory
2. B inicializa MLX/texturas y arranca el bucle.
3. **Cada frame** (dentro del `game_loop` de B, que es quien llama):
   - `move_player` → mueve con `is_wall`.
   - `update_sim` → tu simulación entera (solo si `game_state == G_PLAY`).
   - (B dibuja todo después).
4. Tecla **E** → `toggle_door`; tecla **R** (en fin de partida) → `restart_game`; disparo → `try_fire`.

---

## Frontera con B (ficheros compartidos / glue)
- **`input_bonus.c`**: tus teclas conviven con el `mouse_*` de B.
- **`player.c` (`is_wall`)**: tú lo escribes, el raycasting de B lo consume.
- **`main.c`, `error.c`, `exit/`, `includes/cub3d.h`, `Makefile`, `libft/`**: compartidos (ver `LADO_B.md`).
- **`init_game.c` (`init_mod_state`)**: lo escribe B en su flujo de init, pero inicializa TUS campos del mod (vida, oleada, semilla…).

---

## Walkthrough paso a paso (qué función llama a cuál)

### A) Arranque + parsing — de `main` a un mapa válido en memoria
```
main()                                [main.c]   comprueba argc == 2
└─ check_file(argv[1])                [check_args.c]  is_cub_file (.cub) + is_readable_file (open)
└─ parsing(path, data)                [parsing_data.c]
   ├─ parse_memory()                  cuenta y vuelca el fichero a memoria
   │  ├─ count_lines()                open + GNL contando + close
   │  └─ fill_lines()                 open + GNL → data->file_lines[] (NULL-terminado)
   ├─ get_file_data()                 [get_file_data.c]  clasifica cada línea
   │  ├─ line_type()                  EMPTY / TEXTURE(NO,SO,WE,EA) / COLOR(F,C) / MAP
   │  │                               marca map_start; error si textura/color APARECE tras el mapa
   │  └─ process_line()
   │     ├─ extract_texture()         índice N/S/W/E, dup check, ft_strtrim de la ruta
   │     └─ fill_color_textures()     [fill_color_textures.c] parse_color → validate_colors (0-255)
   ├─ create_map()                    [create_game_map.c]  construye char **map
   │  ├─ get_map_end()/check_no_gaps() límites del bloque, sin líneas vacías dentro
   │  └─ fill_grid() → build_row()    copia chars; ESPACIO→'1'; rellena a lo ancho con '1'
   ├─ validate_map()                  [parsing_data.c]
   │  ├─ (id_flags bits 4 y 5)        que existan F y C, si no ERR_MISSING_COLOR
   │  ├─ check_map() → set_player_at  cuenta 1 jugador, set_ns/set_ew dir, GUARDA spawn, pone '0'
   │  ├─ check_map_borders()          perímetro todo '1' (mapa cerrado)
   │  └─ check_textures()             las 4 rutas existen y son .xpm
   └─ free_file_lines()               ya no hacen falta las líneas crudas (el mapa ya está)
```
**Resultado:** `data->map` (rejilla), `tex_paths[4]`, colores F/C, pos/dir del jugador y spawn guardado.

### B) Un frame de simulación — `update_sim` (lo llama el game_loop de B)
```
update_sim(data)                      [sim.c]   (return inmediato si game_state != G_PLAY)
├─ if (!enemies) spawn_wave()         [waves.c] get_wave_params → place_enemy × N
│                                     (count_spawn_cells / pick_spawn_cell / is_valid_spawn + has_los)
├─ tick_weapon()                      cooldown mecánico del arma (weapon.timer)
├─ update_flow_field()                [flow_field.c] BFS desde el jugador (si cambió de celda)
│  └─ bfs_init() + bfs_loop()         flow[][] = distancias; cell_walkable bloquea '1'/'D'
├─ update_enemies() → enemy_fsm()     [enemy_ai.c]
│  ├─ IDLE  → CHASE
│  ├─ CHASE → chase_player()          flow_dir()→best_neighbor() (baja el gradiente); fallback recto
│  │          (d < 1.0 → ATTACK)
│  └─ ATTACK→ (d > 2.0 → CHASE)
├─ try_fire()                         [combat.c] si disparaste y el arma está lista
│  └─ hitscan()→find_target()→hitscan_hit() (dot>0, perp<0.5, has_los) → kill_enemy()
├─ update_player_hp()                 [player_state.c] enemy_can_hit (dist²≤1 + LOS) → -10 HP
├─ check_game_state()                 hp≤0 → G_OVER ; oleada 3 limpia → G_WIN
└─ check_wave_advance()               enemy_count==0 → siguiente oleada
```
**Eventos de input** (en `key_press_bonus`): **E** → `toggle_door` (e invalida el flow field), **R** (en pantalla de fin) → `restart_game`, **disparo** → pone `fire = 1` (lo consume `try_fire`).
