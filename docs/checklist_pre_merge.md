# Checklist pre-merge `fase1_error` → `dev` (por clusters)

> Auditoria del codigo ENTERO (lado A + lado B integrado), no solo el diff.
> **Plan de 2 merges:** (1) `fase1_error → dev` = fast-forward limpio (dev=94f661e, +4, sin divergencia).
> (2) `raycasting2 → dev` = unico conflicto la cabecera de `cub3d.h` (trivial); pasa el motor a VECTORIAL.
> Leyenda: `[ ]` pendiente de correr en Linux · `✓` verificado estatico por revision · `⚠️` hallazgo/riesgo a discutir.
> TODO comando se ejecuta en LINUX (gcc + MiniLibX-X11 + valgrind). Aqui no se compila.

---

## C1 — Build & Norma

- [ ] `make re` → 0 warnings con `-Wall -Wextra -Werror`.
- [ ] `make` dos veces seguidas → la 2a no recompila (sin relinking).
- [ ] `make clean`, `fclean`, `re`, `bonus` funcionan.
- ✓ `norminette sources/ includes/` → 0 errores (verificado).
- [ ] `git ls-files | grep -E 'cub3D$|\.o$|\.a$|minilibx'` → vacio (sin binarios trackeados).
- [ ] `.gitignore` cubre `cub3D`, `obj/`, `*.o`, `*.a`, `minilibx-linux/`.

## C2 — Argumentos & lectura de fichero  (check_args.c · parsing_data.c)

- [ ] sin args / >2 args → `Error\nUsage...`, exit 1.
- [ ] `foo.txt` → `Not a .cub file`. `nope.cub` → strerror. `docs/` → `Is a directory`.
- [ ] fichero vacio (0 bytes) → `Empty file`.
- ✓ `count_lines` vs `fill_lines`: tope `i < file_nb_lines` + drenado del sobrante (A4).
- ✓ GNL drenado a NULL en ambas pasadas → sin fuga del buffer estatico.

## C3 — Dispatcher & texturas  (get_file_data.c)

- ✓ NO/SO/WE/EA seguidos de ` `/`\t`/`\n`/`\0` → textura; con espacios iniciales tambien (A2).
- ✓ linea solo-whitespace → ignorada; `NORTH`/`NOPE` → no matchea NO.
- ✓ `NO` duplicado → `Duplicate Texture`; `NO\n` sin path → `Empty path`.
- ✓ `index` siempre inicializado (`if/else if/else`).
- ✓ fallo de `ft_strtrim` → `err_msg(strerror)` (ya no `return FAILURE` mudo).
- [ ] valgrind sobre `maps/bad/dup_texture.cub` y `empty_path.cub` → 0 lost.

## C4 — Colores RGB  (fill_color_textures.c)

- ✓ `count_char(',')==2` ataja `220,,100,0`, `220,100,0,,`, `,220,100,0` (A1).
- [ ] 256 / 999 / overflow `99999999999` / `-1` / letras / 2 vals / 4 vals → error.
- [ ] `220, 100, 0` (espacios interiores) y `0255` (zero-pad) → error (decision estricta, defendible).
- [ ] `F` o `C` duplicado → `Duplicate color`.
- ✓ `parse_color` libera `colors_str`+`split` en TODOS los returns (helper `free_color`).

## C5 — Memoria & cleanup  (parsing_utils.c · exit_game.c · main.c)

- [ ] `for f in maps/bad/*.cub; do valgrind --leak-check=full ./cub3D "$f"; done` → 0 definitely lost (paths de error, no llegan a MLX → sin supresion).
- [ ] caso feliz: `valgrind ./cub3D maps/good/valid_ids.cub` + ESC → 0 definitely lost TUYOS.
- ✓ leaks de caso feliz cerrados: `exit_game` llama `free_parsing` (file_lines + tex_paths) + `free(map)`.
- ✓ `free_parsing` idempotente: `file_lines` y `tex_paths[i]` se ponen a NULL tras liberar.
- ✓ sin doble free: `free_parsing` solo en rama de error de main; `exit_game` solo en exito (mutuamente exclusivos).
- ⚠️ MLX deja "still reachable"/"possibly lost" propios suyos → crear `mlx.supp` y correr con `--suppressions=mlx.supp`. Documentar en README.
- [ ] ESC y X roja → cierre limpio (ambos pasan por `exit_game`).

> ⚠️ **C6–C8 describen el lado B que HOY esta en dev (ANGULAR).** Tras el 2o merge
> (raycasting2) `player.c` y `raycasting.c` quedan REESCRITOS a vectorial y aparece
> `floor_ceeling.c`. Los ⚠️ de aqui se arreglan sobre esa version, no ahora — ver
> `plan_S05A_S06A.md` → "Bugs del lado B".

## C6 — Lado B · Render / Raycasting  (raycasting.c · render_utils.c · game_loop.c)

- ✓ `put_pixel` con bounds (x/y dentro de WIN) → no escribe fuera del buffer.
- ⚠️ `perform_dda` (raycasting.c:72): chequea `map[map_y]` (fila NULL) pero NO que `map_x` este dentro de la longitud de la fila. Seguro SOLO con mapa rectangular (S05A) y cerrado (S06A). Hoy va con `get_temp_map` rectangular → OK; re-verificar tras S05A.
- ⚠️ `draw_wall_column` (raycasting.c:88): `line_h = WIN_H / wall_dist`. Si un rayo es perfectamente axial, `delta = fabs(1/dir)` puede ser `inf` y `wall_dist`→0 → `(int)inf` es UB. `put_pixel` evita el crash, pero conviene un guard. Discutir con Rodrigo.
- [ ] sin fish-eye (correccion `cos(angle-ray)` presente).
- [ ] FPS jugable; `clear_image` cada frame.

## C7 — Lado B · Movimiento & input  (player.c · input.c)

- [ ] WASD mueve, flechas rotan, release limpia flags.
- ✓ ESC en `key_press` → `exit_game`.
- ⚠️ `move_player` calcula `cos/sin` ANTES de `rotate_player` → el movimiento usa el angulo del frame anterior (lag 1 frame). Cosmetico; revisar en S08.
- ⚠️ sin colisiones: hoy se atraviesan muros y al salir del grid el DDA puede leer fuera → core dump conocido. Se cierra en S08A (wall-sliding). Documentado.

## C8 — Lado B · Init & MLX  (init_game.c)

- ⚠️ `init_game` NO comprueba `mlx_init()`/`mlx_new_window()`/`mlx_new_image()` == NULL → si MLX no arranca, segfault. Mandatory pide salida limpia. Coordinar con Rodrigo (encaja en S02B).
- ⚠️ `get_temp_map`: mapa hardcodeado TEMPORAL → se sustituye por el grid real en S05A.
- ⚠️ `init_player` fija pos/angulo hardcodeados → los pisara el spawn del parser en S06A.

## C9 — Integracion & deuda conocida (esperada, NO bloquea)

- Suelo/techo con color del `.cub` → S04B. · Texturas en muros → S07B.
- Validacion del mapa (cerrado, 1 jugador, chars) → S06A. · Grid real → S05A.
- `cub3d.h` es compartido: todo cambio aditivo se avisa a Rodrigo ANTES de commitear.
- Este cierre toca `exit_game.c` (lado B) para liberar memoria del lado A → avisado.

## C10 — Merge readiness (los 2 merges)

**Merge 1 — `fase1_error → dev`:**
- ✓ +4 sobre `dev` (94f661e) sin divergencia → **fast-forward, sin conflictos**.
- [ ] tras el merge: `make re` + `norminette` limpios en `dev`.

**Merge 2 — `raycasting2 → dev` (despues del 1):**
- ✓ unico conflicto = cabecera de `cub3d.h` (`By:`/`Updated`). Resolver dejando un
  autor (o ambos) y la fecha mas reciente. Lo demas auto-fusiona (verificado merge-tree).
- [ ] tras resolver: `make re` + `norminette` + abrir ventana (motor vectorial).
- ⚠️ `origin/raycasting` (legacy, header viejo) → confirmar con Rodrigo que NO re-pushea desde ahi.

**Despues de los 2 merges (antes de S05A):** ver `plan_S05A_S06A.md` →
"ESTADO DE DEV" y "Bugs del lado B" (NULL de MLX, DDA bounds, wall_dist→0, spawn vectorial).
- [ ] NUNCA merge directo a `main` (solo via `dev` + PR).
