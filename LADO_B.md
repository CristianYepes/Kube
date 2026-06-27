# LADO B — Rodrigo

**Init/MLX · render · raycasting · texturas · ratón · sprites animados · TODO el render del mod.**

> Regla mental: **B decide cómo se VE, A decide QUÉ pasa.** Tú arrancas la ventana, cargas
> texturas, y dibujas cada frame: paredes (raycasting), suelo/techo, sprites, enemigos,
> escopeta, niebla, HUD y la pantalla de fin. Lees el estado que produce A y lo pintas.

---

## Conceptos que debes dominar (para la defensa)
1. **Raycasting DDA (Lodev):** por cada columna de pantalla lanzas un rayo y avanzas celda a celda (DDA) hasta chocar; la distancia perpendicular da la altura del muro.
2. **Proyección de pared:** altura de la columna = `WIN_H / dist`; coordenada de textura `tex_x/tex_y`.
3. **Z-buffer:** guardas la distancia de cada columna para que los sprites/enemigos se oculten tras los muros.
4. **Sprites tipo billboard:** transformas la posición del sprite al espacio cámara, lo proyectas y lo dibujas escalado, testeando contra el z-buffer.
5. **Doble buffer:** dibujas todo en `data->img` y lo vuelcas con `mlx_put_image_to_window` (sin parpadeo).
6. **El game loop:** el orden de dibujado es sagrado (suelo/techo → paredes → sprites → enemigos → escopeta → HUD → blit).
7. **Carga de texturas XPM:** `mlx_xpm_file_to_image` → array de `int` (colores) reescalado a tamaño fijo.

---

## `sources/init/` — arrancar MLX y cargar assets

| Fichero | Funciones clave | Qué hace |
|---|---|---|
| `init_game.c` | `init_game`, `init_mlx`, `init_textures`*, `init_bonus_assets`, `init_mod_state` | Crea ventana+imagen MLX, reserva z-buffer, carga texturas y assets bonus. (`init_mod_state` inicializa datos del mod de A). |
| `init_textures.c` | `init_textures`, `cleanup_textures` | Carga las 4 texturas de pared (N/S/W/E) y libera si una falla. |
| `init_sprites.c` | `init_sprites_data` | Carga las texturas de los sprites animados (mapa + enemigos). |

---

## `sources/render/` — el motor gráfico (tu núcleo)

| Fichero | Funciones clave | Qué hace |
|---|---|---|
| `raycasting.c` | `cast_rays`, `perform_dda`, `init_ray`, `init_step` | **El raycaster**: lanza un rayo por columna, DDA hasta el muro, rellena el z-buffer. |
| `draw_wall.c` | `draw_wall_column`, `paint_column`, `get_tex_color`, `get_tex_x`, `get_tex_index` | Pinta cada columna de pared con su textura (elige cara N/S/E/W, aplica niebla). |
| `floor_ceeling.c` | `paint_floor_ceiling`, `fog_row` | Pinta suelo y techo (con degradado de niebla cuando está activa). |
| `fog.c` | `apply_fog` | Atenúa un color según la distancia (niebla de la ronda 3). |
| `textures.c` | `xpm_to_int`, `xpm_to_int_size`, `copy_texture_pixels` | Convierte un `.xpm` en un array de colores (reescalado a tamaño fijo). |
| `render_utils.c` | `put_pixel` | Escribe un píxel en el buffer (con chequeo de límites). **Base de todo el dibujo.** |
| `render_sprites.c` | `render_sprites`, `project_sprite`, `draw_sprite_col` | Dibuja los sprites decorativos del mapa (`2`/`3`) tipo billboard con z-buffer. |
| `sprites.c` | `init_sprites`, `sprites_counter`, `set_sprite`, `sort_sprites`, `compute_sprite_distances` | Localiza los sprites en el mapa y los ordena por distancia (painter's). |
| `game_loop.c` | `game_loop`, `tick_clock` | **El bucle por frame**: calcula `dt`, llama a la simulación de A y dibuja TODO en orden. |
| `shotgun.c` | `init_shotgun`, `fire_shotgun`, `tick_shotgun` | Carga la escopeta y avanza su **animación** de disparo (lo mecánico del disparo es de A). |
| `shotgun_draw.c` | `draw_shotgun`, `draw_gun_layer`, `draw_crosshair` | Dibuja la escopeta (a la derecha) y la cruz en pantalla. |

> El **minimapa** (`minimap.c`/`minimap_2.c`) también vive aquí pero es **bonus de A** — ver `LADO_A.md`.

---

## `sources/bonus/render/` — render del mod (zombis, HUD, texto)

| Fichero | Funciones clave | Qué hace |
|---|---|---|
| `enemy_render.c` | `render_enemies`, `project_enemy`, `draw_enemy`, `sort_enemies_by_dist` | Dibuja los zombis (billboard animado, ordenados de lejos a cerca, con niebla). |
| `hud.c` | `render_hud`, `draw_hp_bar`, `draw_wave_dots`, `draw_game_over` | HUD: barra de vida, puntos de oleada, panel de fin de partida. |
| `font.c` | `draw_text`, `draw_glyph`, `fill_block`, (`font_table`) | **Bitmap font retro propia** para `YOU WIN`/`YOU LOSE`/`PRESS R` (dibuja a píxel, no usa la fuente fea de X11). |
| `weapon.c` | `render_weapon` | Stub reservado para overlay extra del arma (hoy vacío). |

---

## `sources/mlx_loop_and_hook/` — el latido de MLX

| Fichero | Funciones clave | Qué hace |
|---|---|---|
| `mlx.c` | `loop` | Engancha los hooks (teclado de A, ratón B, cierre) y arranca `mlx_loop` con `game_loop` como render hook. |

---

## El flujo de B (un frame, en orden)
`tick_clock` (dt) → `move_player`+`update_sim` (lógica de A) → `paint_floor_ceiling` → `cast_rays`
(paredes + z-buffer) → `render_sprites` → `render_enemies` → escopeta/cruz → `render_hud`
→ minimapa → `mlx_put_image_to_window` (blit) → en fin de partida, el panel + texto.

---

## Mandatory vs Bonus (la flag `-DBONUS`)
Varios ficheros tienen **dos versiones** con `#ifdef BONUS` (`init_game.c`, `game_loop.c`, `mlx.c`):
- `make` → binario `cub3D` (mandatory puro: solo paredes/suelo/techo + movimiento).
- `make bonus` → binario `cub3D_bonus` con `-D BONUS` (minimapa, puertas, ratón, sprites, mod…).

---

## Frontera con A (ficheros compartidos / glue)
- **`main.c`**: entry point — valida args + parsea (arranque de A) y luego llama a tu `init_game` + `loop`.
- **`exit/exit_game.c`** (`destroy_game`, `exit_game`) y **`exit/free_bonus.c`** (`free_sprites`, `free_shotgun`): liberan recursos de AMBOS lados (texturas/MLX tuyos + enemigos/mod de A).
- **`error.c`** (`err_msg`): modelo de error compartido (lo usa sobre todo el parser de A).
- **`mlx.c`**: tú montas los hooks, pero enganchan los handlers de teclado de A.
- **`includes/cub3d.h`**: contrato compartido (structs + defines). **Coordinar antes de tocar.**
- **`libft/`, `Makefile`**: compartidos.

---

## Walkthrough paso a paso (qué función llama a cuál)

### A) Arranque — de `main` a la ventana corriendo
```
main()                          [main.c]   (tras el parsing de A)
└─ init_game(data)              [init_game.c]
   ├─ init_mlx()                mlx_init + ventana 1280×720 + imagen + malloc z_buffer[WIN_W]
   ├─ init_textures()           [init_textures.c] carga las 4 texturas de pared (xpm_to_int)
   └─ init_bonus_assets()       init_sprites_data + init_shotgun + door_tex  (+ init_mod_state)
└─ loop(data)                   [mlx.c]   engancha hooks (teclado A, ratón B, cierre)
   └─ mlx_loop_hook(game_loop)  + mlx_loop()  → game_loop se ejecuta CADA frame
```

### B) Un frame — `game_loop` (el orden de dibujado es sagrado)
```
game_loop(data)                 [game_loop.c]
├─ tick_clock()                 dt = ahora - last_time ; anim_clock += dt
├─ if G_PLAY: move_player() + update_sim()        ← lógica de A
├─ paint_floor_ceiling()        [floor_ceeling.c] techo (mitad sup) + suelo (mitad inf); fog_row→apply_fog
├─ cast_rays()                  [raycasting.c]  POR CADA COLUMNA x (0..WIN_W):
│  ├─ init_ray()                camera_x, dirección del rayo, delta_x/y
│  ├─ init_step()               step_x/y + side_x/y (distancia a la 1ª línea de rejilla)
│  ├─ perform_dda()             avanza celda a celda hasta '1'/'D' (o fuera de mapa → sin muro)
│  └─ draw_wall_column()        [draw_wall.c] wall_dist (perp), z_buffer[x]=dist, line_h=WIN_H/dist
│     ├─ get_tex_index()        cara N/S/E/W según side + dirección del rayo
│     ├─ get_tex_x()            columna de la textura (fracción del impacto en la celda)
│     └─ paint_column()→get_tex_color()→put_pixel()   textura + oscurece N/E + niebla
├─ render_sprites()             [render_sprites.c] compute_sprite_distances→sort_sprites→project+draw (z-test)
├─ render_enemies()             [enemy_render.c] sort_enemies_by_dist→project_enemy→draw_enemy (z-test+fog)
├─ if G_PLAY: tick_shotgun() + draw_shotgun() (+ draw_crosshair) + render_weapon()
├─ render_hud()                 [hud.c] vida + oleadas  (o en fin: draw_game_over + draw_text YOU WIN/LOSE)
├─ if minimap: display_minimap()
└─ mlx_put_image_to_window()    VUELCA el buffer a la ventana (doble buffer → sin parpadeo)
```

### El raycasting al detalle (tu concepto estrella para la defensa)
1. **Un rayo por columna:** `camera_x = 2·x/WIN_W − 1` (−1 izquierda … +1 derecha); `rayDir = dir + plane · camera_x`.
2. **DDA:** `delta = |1/rayDir|` (cuánto avanzar para cruzar una celda). `perform_dda` salta siempre a la línea de rejilla más cercana (x ó y), cambia de celda y repite hasta tocar `'1'`/`'D'`.
3. **Distancia PERPENDICULAR** (no euclídea) → evita el "ojo de pez": `wall_dist = side − delta` del eje que tocó.
4. **Proyección:** `line_h = WIN_H / wall_dist`; la columna se centra en pantalla; `tex_x` sale de dónde golpeó el rayo dentro de la celda, `tex_y` se interpola píxel a píxel.
5. **z-buffer:** `z_buffer[x] = wall_dist`; luego sprites/enemigos solo se pintan si están MÁS CERCA que el muro de esa columna (oclusión correcta).
