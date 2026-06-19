# Plan de integración → `dev` (lado A + motor vectorial B + texturas)

> **Objetivo:** dejar `dev` con parser (A) + motor vectorial (B) + spawn + texturas
> **funcionando**. Desde ahí: tú creas rama nueva y sigues en **S07A**; Rodrigo
> arranca su plan nuevo (sprites/ratón) partiendo **de dev**.
> **Fecha:** 2026-06-18. Se trabaja **directamente en `dev`**.

---

## Reglas de oro (no romper ninguna)

1. **Compilar / `valgrind` / ejecutar: SOLO en Linux** (MLX-linux + X11). En mac NO
   se compila y NO se mete la MLX de mac. `norminette` sí corre en ambos.
2. **Preservar el trabajo de Rodrigo:** `git merge raycasting2` REAL (sus commits
   `1e8f48d` y `d49f624` quedan en la historia con su autoría). Tus arreglos van
   ENCIMA, en commits tuyos. Nada de reescribir desde cero. Apéndice C = guion para
   contárselo.
3. **Checkpoint-gate:** no pases de cluster sin pasar su ✅ CHECKPOINT. Si falla, se
   arregla ahí, no se sigue.
4. **Push solo estados que corren:** C1 y C2 quedan LOCALES; se publica en C3, C4, C5.

---

## Estado de partida

| Rama | Hash | Contenido |
|---|---|---|
| `dev` | 1739b2f | parser ≤ S04A + `get_temp_map` (angular) |
| `fase1_error` | 6c8e297 | S05A + S06A T1-T3 (sin spawn) — +2 sobre dev |
| `raycasting2` | (+2 sobre 94f661e) | `1e8f48d` vectorial+suelo/techo · `d49f624` xpm loader |

## ⚠️ PENDIENTES ABIERTOS (retomar — no bloquean C4)
- **Flechas invertidas**: pulsar → gira la vista al lado contrario. Mapeo input OK
  (`KEY_LEFT→rotate_left`). Probadas varias combinaciones de signo plane×rotación, se
  sigue percibiendo invertido. RESOLVER CON CERTEZA (no adivinar más): printf temporal
  de `dir_x/dir_y` en `move_player` tras rotar → pulsar → una vez → leer el signo real
  → fijar rotación/plane en consecuencia.
- **Segfault al atravesar muro** (S/W constante contra pared): sin colisiones, el
  jugador sale del mapa y `wall_dist` puede dar `NaN` (el clamp `<0.0001` no atrapa
  NaN) → `(int)NaN` UB. FIX REAL = colisiones en `move_player` (**S08A**, lado A): no
  mover si la celda destino es muro. Parche: check `isnan`/bounds antes de usar.
- **Textura .cub de tamaño ≠ 64×64 → heap overread** (posible crash en defensa):
  `xpm_to_int` (`textures.c`, lado B) copia siempre TEX_SIZE×TEX_SIZE ignorando el
  w/h reales. Al cargar desde `tex_paths` (C4), un XPM de otro tamaño lee fuera. FIX:
  validar `w==TEX_SIZE && h==TEX_SIZE` tras `mlx_xpm_file_to_image` → NULL si no.
  Coordinar con Rodrigo (su fichero). Con los `.xpm` 64×64 actuales no se dispara.

## Inventario de hallazgos (del análisis del código REAL)

- **Conflictos del merge raycasting2:** `cub3d.h` (contenido) e `init_game.c`
  (contenido). `Makefile` auto-fusiona. (verificado con merge-tree).
- **Norminette de raycasting2 (8 errores):** `textures.c:55` (falta newline final);
  `cub3d.h:129` (`int​ *textures[4]` espacio/tab) y `cub3d.h:153`
  (`paint_floor_ceiling` espacios en vez de tabs).
- **`.xpm`:** NO están en fase1_error; SÍ en raycasting2 (`files/wall_cross.xpm`,
  `wall_pipes.xpm`, `floor_stone.xpm`). ⇒ los mapas `good/` deben apuntar a esas
  rutas reales o `check_textures` los rechaza. Llegan con el merge (C2).
- **Texturas de Rodrigo — estado real (mejor de lo que dice su commit):**
  - `xpm_to_int` (textures.c): ✅ carga XPM→int[] bien.
  - `init_textures`: ✅ pero con rutas **hardcodeadas** (`files/...`), NO usa
    `tex_paths` del parser. → hay que conectarlo (mandatory: textura desde el .cub).
  - render texturizado (`draw_wall_column`): ❌ sigue pintando blanco `0xFFFFFF`.
  - `exit_game`: ❌ no libera `data->textures` (leak).
- **Spawn (T4) pendiente:** `check_map` cuenta el jugador pero no guarda su celda;
  `init_player` (de Rodrigo) hardcodea `pos=(2.5,2.5)`.
- **Bugs lado B a cerrar en la integración:** `init_game` no comprueba NULL de
  `mlx_init`/`mlx_new_window`/`mlx_new_image`. (DDA sin bounds y `wall_dist→0`:
  seguros con mapa validado; se anotan como defensivos, no bloquean.)
- `ft_bzero` (usado por init_textures): ✅ existe en libft.

---

## C0 — Red de seguridad (mac, sin compilar)

1. `git fetch origin`
2. Tags de rescate: `git tag rescate/dev-pre origin/dev` · `git tag rescate/fase1 fase1_error` · `git tag rescate/ray2 origin/raycasting2`
3. `git status` limpio.

✅ **CHECKPOINT C0:** `git tag | grep rescate` muestra los 3. Si algo se tuerce
luego: `git checkout dev && git reset --hard rescate/dev-pre`.

---

## C1 — Merge del parser (A) → dev   *(local)*

1. `git checkout dev`
2. `git merge --ff-only fase1_error`  (fast-forward; lleva S05A + S06A T1-T3)

✅ **CHECKPOINT C1 (Linux):**
```
make re          # 0 warnings
norminette sources/ includes/   # 0 errores
```
⚠️ **NO ejecutar todavía:** el segfault (jugador hardcodeado fuera del mapa real)
es esperado hasta C3. Es normal. **No push.**

---

## C2 — Merge del motor vectorial (B) + resolver + norminette   *(local)*

1. `git merge raycasting2`  → conflictos en `cub3d.h` e `init_game.c`.
2. Resolver `cub3d.h` → **Apéndice A**.
3. Resolver `init_game.c` → **Apéndice B**.
4. Arreglar norminette heredado: newline final en `textures.c`; tabs en `cub3d.h`
   (al resolver a mano ya cuidas L129/L153).
5. `git add -A && git commit` (mensaje: `merge: integrate raycasting2 (vectorial engine + floor/ceiling + xpm loader)`).

✅ **CHECKPOINT C2 (Linux):**
```
make re                          # 0 warnings
norminette sources/ includes/    # 0 errores
git log --oneline -6             # se ven los commits de Rodrigo intactos
```
⚠️ Aún no es "funcional": el spawn sigue hardcodeado (2.5,2.5). **No push.**

---

## C3 — Spawn vectorial (T4) → primer estado FUNCIONAL   *(push)*

1. `check_map`: al detectar `N/S/E/W`, guardar `fila/col/letra` y setear el jugador
   (ver `plan_S05A_S06A.md` → D5):
   - `pos_x = col + 0.5`, `pos_y = fila + 0.5`
   - `dir/plane` por letra (tabla N/S/E/W de D5)
   - `grid[fila][col] = '0'`
2. `init_player` (player.c): que **NO** toque `pos/dir/plane` (solo flags a 0). El
   spawn ya corrió en `parsing()`, antes de `init_game`.
3. Cerrar bug lado B: `init_game` comprueba NULL de mlx/ventana/imagen → `exit_game`
   limpio si fallan.
4. Actualizar `maps/good/valid_ids.cub` → apuntar a `./files/wall_cross.xpm` etc.
   (las reales, ya presentes tras C2) para que pase `check_textures`.

✅ **CHECKPOINT C3 (Linux):**
```
make re && ./cub3D maps/good/valid_ids.cub
```
→ ventana abierta, **apareces en la N mirando bien (no en espejo)**, WASD mueve,
flechas rotan, ESC y la X cierran. **SIN segfault.** ← primer hito visual.
Commit: `feat(parsing): vectorial player spawn from map (S06A T4)` + `git push origin dev`.
(Muros blancos todavía; textura en C4.)

---

## C4 — Completar texturas de Rodrigo (S07B)   *(push)*

1. `init_textures`: usar `data->tex_paths[NORTH..EAST]` en vez de las rutas fijas
   (así carga las texturas del `.cub`, mandatory).
2. `draw_wall_column`: render texturizado — `wall_x`, `tex_x`, `tex_y`, leer
   `data->textures[idx]`, shading caras N/E. Pseudocódigo en `plan_textures_b.md`
   (cluster 3) — es de Rodrigo, lo completas tú.
3. `exit_game`: liberar `data->textures[i]`.
4. (defensivo) guard `wall_dist <= 0` en `draw_wall_column`.

✅ **CHECKPOINT C4 (Linux):**
```
make re && ./cub3D maps/good/valid_ids.cub     # muros con textura, distinta por cara
valgrind --leak-check=full ./cub3D maps/good/valid_ids.cub   # ESC → 0 definitely lost tuyos
norminette sources/ includes/
```
Commit: `feat(render): texture mapping from .cub paths (complete S07B)` + push.

---

## C5 — Fixtures de mapa (T6) + DoD final   *(push)*

1. `maps/bad/` (los que faltan): `wall_hole.cub`, `open_side.cub`, `player_none.cub`,
   `player_multiple.cub`, `forbidden.cub` ('2'), `tab_in_map.cub`, `empty_line_in_map.cub`,
   `id_after_map.cub`, `no_map.cub`, `player_on_border.cub`, `tex_not_xpm.cub`,
   `tex_missing.cub`.
2. `maps/good/`: `subject_map.cub` (ejemplo del subject, rutas → `./files/*.xpm`),
   `minimal.cub`, `spaces_inside.cub`.

✅ **CHECKPOINT C5 (Linux):**
```
for f in maps/bad/*.cub;  do ./cub3D "$f"; echo "$f -> $?"; done   # todos exit 1 + "Error"
for f in maps/good/*.cub; do valgrind --leak-check=full ./cub3D "$f"; done  # corren, 0 leaks tuyos
norminette sources/ includes/
```
Commit: `test: map fixtures + close S05A/S06A` + push. Marcar **S05A y S06A ✅** en cronograma.

---

## C6 — Cierre y reparto

1. `dev` es el tope estable (parser + vectorial + texturas, corre y valgrind-limpio).
2. **Tú:** `git checkout dev && git pull && git checkout -b <tu-rama-S07A>` → sigues en
   **S07A** (input/dir ya vectorial; revisar qué queda real de S07A — gran parte ya está).
3. **Rodrigo:** se actualiza `plan_textures_b.md`→ hecho; se le pasa su **plan nuevo**
   (sprites animados S12B + ratón S10B) partiendo **de dev**, NO de raycasting2.
4. ⚠️ Coordinación: que Rodrigo **borre/abandone raycasting2** y parta de dev, o
   volveréis a divergir.

---

## Apéndice A — `cub3d.h` resuelto (qué debe quedar)

- **Defines:** WIN_W/H · **`MOVE_SPEED`, `ROT_SPEED`, `TEX_SIZE 64`** (de B) · keycodes ·
  return codes · line types · texture index. **QUITAR `BLOCK` y `FOV`** (el vectorial
  no los usa).
- **Error strings:** TODOS los tuyos (incluidos los de S06A). Rodrigo no aporta aquí.
- **`t_img`:** con `endian` (lo usa textures.c).
- **`t_player`:** versión **vectorial de Rodrigo** (`pos_x,pos_y,dir_x,dir_y,plane_x,plane_y` + flags). Fuera `x/y/angle`.
- **`t_ray`:** versión **vectorial** (`double`, sin `angle`).
- **`t_data`:** tus campos (`file_lines, file_nb_lines, map_start, id_flags, map_height,
  map_width, tex_paths[4], floor_color, ceiling_color, map, mlx, win, img, player`) **+
  `int *textures[4]`** de Rodrigo (alinear con tabs, sin el espacio del `int  *textures`).
- **Prototipos:** los tuyos (parsing + parsing utils) **+** `paint_floor_ceiling`,
  `xpm_to_int`, `init_textures` (de B, con tabs correctos).
- **Cabecera 42:** dejar un autor (o ambos) + fecha; es lo único "manual" del conflicto.

## Apéndice B — `init_game.c` resuelto

- `init_player` (flags solo; el spawn lo hizo el parser).
- `mlx_init` → si NULL, error limpio. Igual `mlx_new_window`, `mlx_new_image`.
- `mlx_get_data_addr`.
- `init_textures(data)` → si `ERR`, `exit_game`.
- **SIN `get_temp_map`** (tu versión) y **SIN hardcodear `floor/ceiling_color`** (los da
  el parser en S04A).

## Apéndice C — Qué es de Rodrigo y qué completaste tú (para hablar con él)

- **Suyo, intacto en la historia:** motor vectorial (raycasting.c, player.c),
  suelo/techo (floor_ceeling.c), cargador XPM (textures.c/init_textures.c).
- **Completado por ti al integrar:** resolución del header compartido, limpieza
  norminette, conectar texturas a las rutas del `.cub`, render texturizado, frees,
  spawn desde el mapa. Mensaje honesto: *"integré tu rama y completé el render y el
  cableado para que funcione con el parser"*, no *"lo rehice"*.
