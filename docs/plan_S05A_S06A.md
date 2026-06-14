# S05A + S06A — Ruta de ejecucion (FINAL, verificada)

> S05A: `parsing/create_game_map.c` + `parsing/parsing_utils.c` — construir `data->map[][]` desde `file_lines`, dimensiones, espacios→muro.
> S06A: `check_map.c` + `check_map_borders.c` + `check_textures.c` — validacion completa + spawn del jugador + swap del mapa temporal (SYNC3).
> Prerequisito: PARTE 0 cerrada (S03A/S04A) + LOS DOS MERGES hechos. Sin eso NO se empieza S05A.

---

## ESTADO DE DEV — orden de merges y modelo VECTORIAL (leer primero)

Rodrigo (raycasting2) cambio el motor de ANGULAR a VECTORIAL. Este plan asume
que dev YA tiene los dos merges hechos. Orden:

1. **`fase1_error` → `dev`** (fast-forward, sin conflictos). Cierra tu lado A.
2. **`raycasting2` → `dev`**. UNICO conflicto real: cabecera de `cub3d.h`
   (`By:`/`Updated`, trivial). Lo demas auto-fusiona (Makefile, prototipos,
   structs — verificado con merge-tree).

Tras ambos, dev tiene el modelo nuevo (definido por Rodrigo en cub3d.h):
- `t_player`: `pos_x, pos_y, dir_x, dir_y, plane_x, plane_y` (double). FUERA `angle`.
- `t_ray`: campos `double`, sin `angle`.
- Defines: FUERA `BLOCK` y `FOV`; entran `MOVE_SPEED`, `ROT_SPEED`.
- Coordenadas en CELDAS (1 celda = 1.0), no pixeles: `map[(int)pos_y][(int)pos_x]`.
- Render nuevo: `paint_floor_ceiling` (suelo/techo planos ya pintados).

### Bugs del lado B — NO arreglar en fase1_error, SI tras el 2o merge
Estan en ficheros que Rodrigo REESCRIBE en raycasting2 (raycasting.c, player.c,
init_game.c). Tocarlos en tu rama ahora = trabajo perdido + conflicto de merge.
Se arreglan sobre la version vectorial ya integrada, idealmente con Rodrigo:
- **init_game.c**: no comprueba NULL de `mlx_init`/`mlx_new_window`/`mlx_new_image`
  → si MLX no arranca, segfault. Mandatory pide salida limpia.
- **raycasting (DDA bounds)**: indexa `map[y][x]` sin verificar que `x` este
  dentro de la fila → seguro solo con mapa rectangular (S05A) + cerrado (S06A).
- **raycasting (wall_dist→0)**: `linea = WIN_H / wall_dist`; un rayo axial puede
  dar `inf` y `(int)inf` es UB. `put_pixel` evita el crash, pero conviene guard.
- **core dump al atravesar muro** (sin colisiones) → S08A wall-sliding.

---

## PARTE 0 — Cierre de deuda S03A/S04A (gate bloqueante)

> ✅ **COMPLETADA** (commits c6c29ef + cc4bab5 + cierre de leaks/errores).
> A1-A4 cerrados, fixtures creados, S03A/S04A ✅ en tabla maestra.
> Auditoria completa pre-merge en docs/checklist_pre_merge.md.

Bugs A1-A4 de la revision 2026-06-12. S05A se construye LITERALMENTE encima de
A2: si line_type clasifica mal, create_map coge mal el inicio del mapa. Pagado
antes de construir.

### P0.1 — A1: comas malformadas en parse_color
- `ft_split` colapsa delimitadores (ft_split.c:24-25, :72-73): `"220,100,0,,"`,
  `",220,100,0"` y `"220,,100,0"` producen 3 tokens limpios → hoy se ACEPTAN.
- Fix: validar la cadena cruda ANTES de fiarse del split. Propiedad que la
  distingue: una linea RGB valida tiene EXACTAMENTE 2 comas. Cuenta de comas
  sobre `colors_str` (tras trim) == 2, ademas del check de 3 tokens existente.
- **Verify:** los 5 fixtures de colores de P0.5 rechazan; `F 220,100,0` pasa.

### P0.2 — A2: line_type segun contrato D3/D4 del plan anterior
- Nacen en `parsing/parsing_utils.c` (adelantado de S05A, uso inmediato):
  - `int is_a_white_space(char c)` — ' ', '\t', '\n', '\r'.
  - `char *skip_spaces(char *str)` — avanza ' ' y '\t' SOLO (no \n).
- Cambios en `get_file_data.c`:
  - `line_type`: clasificar sobre `skip_spaces(line)`. Linea cuyo resultado es
    `\0`/`\n` → TYPE_EMPTY (cubre solo-espacios). `"NO\n"` pelado: el token
    matchea pero `line[2]` es `\n` → tratar `\n`/`\0` tras token como
    TYPE_TEXTURE con path vacio (cae en ERR_EMPTY_PATH), no como mapa.
    Igual para F/C: `"F\n"` → TYPE_COLOR → error de formato.
  - TRAMPA: `extract_texture` lee `&line[2]` (get_file_data.c:48) y
    `fill_color_textures` lee `line[0]`/`&line[1]` (fill_color_textures.c:72-75,
    :46). Con espacios iniciales eso se rompe. `process_line` hace UN
    `skip_spaces(line)` y pasa el puntero saltado a ambos handlers. Cero
    cambios de firma.
- **Verify:** `"   \n"` → ignorada; `"  NO ./x"` → textura OK; `"NO\n"` →
  `Error\nEmpty path`; `"F\n"` → `Error\nInvalid color format`; mapa con
  lineas que empiezan por espacio sigue clasificando TYPE_MAP.

### P0.3 — A3: malloc-fail sin chequear (2 sitios)
- get_file_data.c:48: si `ft_strtrim` → NULL, la linea 49 hace `[0]` sobre NULL.
- fill_color_textures.c:46-48: `ft_strtrim` NULL → `ft_split(NULL)` → NULL
  (ft_split.c:96-97) → `!split[0]` peta.
- Fix: check NULL → `err_msg(NULL, strerror(errno), FAILURE)` o ERR_MALLOC.
- **Verify:** lectura de codigo (no testeable sin fault injection). 2 lineas.

### P0.4 — A4: tope en fill_lines (opcional, recomendado)
- parsing_data.c:49-54: si el fichero crece entre las dos pasadas, escribe
  fuera de `file_lines[count]`. Guard: `while (line != NULL && i < count)` +
  drenar GNL si se corta. 1-2 lineas. Decision: SI (barato, cierra UB).

### P0.5 — Liberacion en error + fixtures + valgrind (paga D5-leak3/4)
- `parsing/parsing_utils.c`:
  - `void free_file_lines(t_data *data)` — bucle filas + array + poner
    `file_lines = NULL` y `file_nb_lines = 0` (tolerante a doble llamada).
  - `void free_parsing(t_data *data)` — free_file_lines + `tex_paths[0..3]`
    (si != NULL, y a NULL) + `data->map` si existe (filas + array).
- main.c: toda rama `return (FAILURE)` tras `parse_memory` pasa por
  `free_parsing(&data)`. Exito (por ahora): `free_file_lines` tras
  `get_file_data` — cuando S05A exista, la llamada se mueve a despues de
  `create_map` (T6 de Parte 1).
- Fixtures que faltaban (T9/T6 del plan anterior):
  - `maps/bad/`: `dup_texture.cub`, `missing_id.cub`, `empty.cub`,
    `empty_path.cub` (linea `NO`), `rgb_256.cub`, `rgb_negative.cub`,
    `rgb_letters.cub`, `rgb_two_values.cub`, `rgb_four_values.cub`,
    `rgb_trailing_commas.cub` (A1), `rgb_leading_comma.cub` (A1),
    `rgb_double_comma.cub` (A1), `rgb_spaces.cub` (`F 220, 100, 0` — decision
    D6 anterior: estricto), `rgb_overflow.cub`, `rgb_zeropad.cub` (`0255`).
  - `maps/good/`: `valid_ids.cub` (6 identificadores + mini-mapa, CRLF no),
    `crlf.cub` (mismo contenido con `\r\n`).
  - Mover `maps/good/test_basic.cub` → `maps/bad/missing_id.cub` (es 1 sola
    linea NO: invalido; el plan S03A-T9 ya decia no reutilizarlo).
- **Verify (Linux):** `valgrind --leak-check=full ./cub3D maps/bad/X.cub` →
  0 definitely lost en TODOS los bad (ningun flujo de error llega a mlx_init →
  no hace falta supresion). `norminette` limpia.
- **Al cerrar P0:** marcar S03A y S04A ✅ en la tabla maestra (su DoD por fin
  se cumple entero). Commit sugerido:
  `fix(parsing): enforce dispatcher contract and strict RGB commas`.

---

## PARTE 0.5 — Decisiones de diseno (cerradas)

### D0 — Modelo de datos: NADA de t_mapinfo. Campos planos en t_data
- cronograma S05A/S06A habla de `t_mapinfo`/`t_texinfo` (cronograma.md:624,
  :692, :698). Ese modelo MURIO en el plan S03A/S04A (D0/D1): el header real
  tiene `char **map`, `tex_paths[4]`, `floor_color`/`ceiling_color`.
- El raycaster VECTORIAL de Rodrigo consume `data->map` como `char **`
  NULL-terminated y muro == '1' (indexa `map[(int)pos_y][(int)pos_x]`). Ese
  contrato NO se toca: tu grid es char** NULL-terminated con '1' = muro.
- Anadir a `t_data` (bloque /*Scene*/): `int map_height; int map_width;`
  y al bloque /*Parsing*/: `int map_start;` (transitorio, indice de la primera
  linea de mapa en file_lines).
- `cub3d.h` (ya fusionado con el vectorial tras el 2o merge): tu cambio es
  ADITIVO (3 ints + defines de error + prototipos), sin renombrar nada de
  Rodrigo. Avisarle igualmente del diff del header.
- `check_valid_rgb`/`convert_rgb_to_hex` del listado S06A (cronograma.md:696-697):
  YA HECHOS en S04A (fill_color_textures compone el int). No se reimplementan.

### D1 — Donde empieza y termina el mapa
- `get_file_data` gana 2 responsabilidades (sigue ≤25 lineas):
  - `type == TYPE_MAP && map_start == -1` → `map_start = i`.
  - `(TYPE_TEXTURE || TYPE_COLOR) && map_start != -1` → ERR_ID_AFTER_MAP
    (subject: el mapa SIEMPRE al final; decidido en D3 del plan anterior).
- TRAMPA: `(t_data){0}` pone map_start = 0, que es un indice VALIDO.
  `parse_memory` inicializa `map_start = -1` explicitamente.
- `create_map` delimita: `map_end` = ultima linea NO whitespace del fichero
  (escanea desde el final con is_a_white_space). Linea vacia/solo-whitespace
  DENTRO de [map_start, map_end] → ERR_EMPTY_LINE_IN_MAP. Vacias DESPUES del
  mapa → legales (quedan fuera del rango). Si map_start == -1 → ERR_MAP_MISSING.
- Reparto limpio: dispatcher = ORDEN de elementos; create_map = FORMA del mapa.

### D2 — Normalizacion del grid (corazon de S05A)
- `height = map_end - map_start + 1`. `width` = mayor longitud VISIBLE
  (`find_biggest_len`: longitud sin contar `\n`/`\r` finales) en el rango.
- Cada fila del grid: malloc(width + 1), copiar char a char convirtiendo
  `' '` → `'1'` durante la copia, rellenar el resto hasta width con `'1'`,
  terminar en `'\0'`. Array de height + 1 punteros, ultimo = NULL
  (el DDA vectorial de Rodrigo depende del NULL-terminated y de filas rectangulares).
- `change_space_into_wall` como funcion separada (cronograma.md:626) se
  DISUELVE en el bucle de copia: una sola pasada, un archivo de ≤5 funciones.
  Mismo efecto, justificacion para defensa: espacio == zona no jugable ==
  muro logico; el jugador nunca puede pisarlo ni verlo distinto.
- Relleno con '1' (no '\0'): deja el mapa RECTANGULAR → el check de cierre de
  S06A es trivial y el DDA nunca lee mas alla de una fila corta.
- PROHIBIDO `ft_strtrim` sobre lineas de mapa: se comeria los espacios
  INICIALES, que son contenido (subject.md:135 "parsed as it looks"). El strip
  de `\n`/`\r` finales es manual por longitud. (En identificadores strtrim
  sigue OK — alli el espacio no es contenido.)
- Tab DENTRO del mapa: NO es espacio del subject (subject.md:120 solo bendice
  ' '). Se copia tal cual y caera como char invalido en S06A. Estricto,
  defendible, cero codigo extra.
- TRAMPA -Werror: `ft_strlen` devuelve `size_t`; comparar con `int j` dispara
  -Wsign-compare. Guardar longitudes en int desde el principio.
- TRAMPA GNL: la ultima linea puede venir SIN `\n` (get_next_line.c:get_before_newline)
  → el strip de cola es condicional, no `len - 1` a ciegas.

### D3 — Propiedad de memoria del grid
| Que | Quien aloca | Quien libera | Cuando |
|---|---|---|---|
| `file_lines` | parse_memory/fill_lines | free_file_lines | tras create_map OK (exito) o free_parsing (error) |
| filas + array `map` | create_map | exit_game (vida normal) / free_parsing (error de parsing) | ESC, X roja, o fallo |
| `tex_paths[4]` | extract_texture | exit_game / free_parsing | idem |
- create_map en fallo interno libera SUS filas parciales + array y deja
  `data->map = NULL` antes de devolver FAILURE (cada alocador limpia lo suyo).
- exit_game YA llama `free_parsing` (file_lines + tex_paths) — hecho en P0.
  TRAMPA pendiente: hoy `free(data->map)` libera el ARRAY de filas LITERALES
  (get_temp_map). Cuando S06A traiga filas malloc'd hay que liberar fila a fila
  ANTES del array → ese cambio va EN EL MISMO COMMIT que el swap (T-S06A.5).
  Liberar filas literales = segfault; no liberar las malloc'd = leak.

### D4 — Validacion S06A: bordes en vez de flood fill (bendecido por roadmap)
- Con espacios ya convertidos a '1' y grid rectangular, "mapa cerrado" ⇔
  "ninguna celda pisable (0/N/S/E/W) en el borde del rectangulo".
  Justificacion defensa: para escapar, el jugador tendria que pisar una celda
  del borde; si todas son '1', imposible. roadmap.md:768 lista exactamente
  esta alternativa al flood fill. Cero recursion, cero copia del mapa.
- `check_map.c`: chars validos {0,1,N,S,E,W} (post-conversion ya no hay ' ')
  → ERR_INVALID_CHAR; contador de N/S/E/W != 1 → ERR_PLAYER_COUNT; guarda
  fila/col/letra del jugador.
- `check_map_borders.c`: fila 0 y fila height-1 todas '1'; col 0 y col
  width-1 de cada fila '1' → si no, ERR_MAP_NOT_CLOSED.
- `check_textures.c`: los 4 `tex_paths` != NULL y flags F/C seteados
  (id_flags bits 4-5) → ERR_MISSING_ID; extension `.xpm` (espejo de
  is_cub_file de S02A: len>=4 ANTES de mirar la cola); existencia + legible +
  no-directorio con el truco open/read/EISDIR de S02A (check_args.c:29-48).
  Se DUPLICA esa logica como static local: 2 call sites totales < 3 → no se
  generaliza todavia (regla del proyecto).
- `mapa demasiado pequeno` (fixture del cronograma): NO hay check especifico.
  Un mapa 2xN no puede tener jugador en celda cerrada → cae en
  ERR_PLAYER_COUNT o ERR_MAP_NOT_CLOSED. Mensaje generico pero correcto. YAGNI.

### D5 — Spawn del jugador (VECTORIAL) + swap del mapa temporal (commit SYNC3)
- Modelo de Rodrigo (raycasting2, estilo Lodev). El spawn setea posicion +
  vectores, NO angulo. Coordenadas en CELDAS (sin BLOCK):
  - `player.pos_x = col + 0.5`, `player.pos_y = fila + 0.5` (centro de celda).
  - dir/plane por letra (plane = dir girado 90o, modulo 0.66 → FOV ~66o):
    | Letra | dir_x | dir_y | plane_x | plane_y |
    |---|---|---|---|---|
    | N |  0 | -1 |  0.66 |  0    |
    | S |  0 |  1 | -0.66 |  0    |
    | E |  1 |  0 |  0    |  0.66 |
    | W | -1 |  0 |  0    | -0.66 |
  - El SIGNO del plane evita la imagen en espejo. Si al probar el mundo sale
    invertido izquierda/derecha, invertir el signo del plane (defensa: el plane
    define el sentido del barrido de columnas).
  - Tras el spawn: `grid[fila][col] = '0'` (la letra ya no es contenido; DDA y
    colisiones ven suelo).
  - S07A queda REDUCIDO: hooks ya integrados (input.c), ESC/X ya funcionan,
    dir/plane iniciales los da este spawn. Al llegar, revisar S07A contra la
    realidad y recortar el cronograma (anotarlo, no hacerlo ahora).
- Swap en init_game.c: eliminar `get_temp_map` y su asignacion; el mapa real ya
  viene en `data->map`. TRAMPA: `init_player` (player.c, version vectorial de
  Rodrigo) inicializa pos/dir/plane → si corre DESPUES del spawn lo PISA. Orden
  correcto: el spawn (en check_map, S06A) escribe player ANTES de init_game, e
  init_player NO debe re-tocar pos/dir/plane (dejar solo flags de teclas a 0).
- init_game.c y player.c son del lado B (ya vectorial tras el 2o merge) →
  cambios pequenos, avisar a Rodrigo. exit_game.c ya quedo listo en P0.
- Hasta S08A (colisiones) sigue vivo el bug: atravesar un muro deja el origen
  del rayo fuera de zona cerrada y el DDA puede salirse. Con mapa validado y
  spawn legal el render es seguro MIENTRAS no atravieses muros. S08A lo cierra.

### D6 — Errores nuevos (aditivos en cub3d.h, junto a los existentes)
`ERR_MAP_MISSING`, `ERR_EMPTY_LINE_IN_MAP`, `ERR_ID_AFTER_MAP`,
`ERR_INVALID_CHAR`, `ERR_PLAYER_COUNT`, `ERR_MAP_NOT_CLOSED`,
`ERR_MISSING_ID`, `ERR_TEX_NOT_XPM`, `ERR_MALLOC` (P0.3). Texto libre pero
explicito (subject.md:205). Para fallos de open de texturas: `strerror(errno)`
con el path como detail — ya lo da err_msg, sin define nuevo.

### D7 — Orquestador: main NO crece
- main.c esta a ~20 lineas utiles; anadir 4-5 llamadas lo revienta (norma 25).
- `int parsing(char *path, t_data *data)` en parsing_data.c (queda en 4/5
  funciones): encadena parse_memory → get_file_data → create_map →
  free_file_lines → check_map → check_map_borders → check_textures.
  El spawn vive DENTRO de check_map (tras validar count==1): la celda/letra
  son variables locales suyas → ningun campo nuevo en t_data. Corre antes de
  borders y es inofensivo: borders solo mira '1' y la letra ya es '0'.
  Devuelve int; main queda: check_file → parsing → init_game → hooks → loop,
  con UN `free_parsing` en la rama de fallo de parsing.
  (Si parsing() supera 25 lineas con los ifs: patron ya usado en main —
  un if por llamada devolviendo FAILURE; 7 llamadas x 2 lineas + firma cabe.
  Si no cabe, partir en parsing() + validate_scene() static. Decidir al teclear.)

---

## Trampas confirmadas (resumen rapido, todas referenciadas arriba)

1. strtrim sobre filas de mapa destruye espacios iniciales → strip manual de cola.
2. file_lines llevan `\n` (y la ultima quiza no) → find_biggest_len sin cola.
3. `(t_data){0}` ≠ map_start=-1 → init explicito en parse_memory.
4. size_t vs int con -Werror → longitudes en int.
5. skip_spaces del dispatcher debe propagarse a los handlers (leen line[0..2]).
6. exit_game: free_parsing YA hecho; queda free(map) array→filas en el commit del swap (S06A).
7. init_player (vectorial) pisa pos/dir/plane del spawn → adelgazarlo en el mismo commit.
8. DDA sin bounds: seguro solo con mapa validado + origen dentro (hasta S08A).
9. parsing_utils.c nace con 5 funciones JUSTAS (is_a_white_space, skip_spaces,
   find_biggest_len, free_file_lines, free_parsing) — la sexta utilidad que
   aparezca va a otro fichero, no "se hace hueco".
10. Norminette 25 lineas: el bucle copia+pad de filas se parte en build_row.

---

## PARTE 1 — S05A (tareas)

### T1 — parsing_utils.c completo
P0 ya creo is_a_white_space + skip_spaces (+ frees en P0.5). Anadir
`find_biggest_len(t_data *data, int start, int end)` (o firma equivalente ≤4
params) que ignora `\n`/`\r` de cola.
**Verify:** con lineas `"111\n"`, `"11111\r\n"`, `"1"` devuelve 5.

### T2 — Estado del mapa en el dispatcher (D1)
map_start en t_data + init -1 en parse_memory + las 2 reglas en get_file_data.
**Verify:** id tras mapa → ERR_ID_AFTER_MAP; fichero sin lineas de mapa deja
map_start = -1.

### T3 — create_game_map.c: esqueleto y limites
`int create_map(t_data *data)` + static `get_map_end` + `check_no_gaps`
(ERR_EMPTY_LINE_IN_MAP / ERR_MAP_MISSING segun D1).
**Verify:** mapa con linea en blanco interior → error; vacias tras el mapa → OK.

### T4 — build_row + fill_grid (D2)
Copia con conversion ' '→'1', pad '1', NULL-terminated, height/width en t_data.
Fallo de malloc a mitad → liberar filas previas + array, map = NULL, FAILURE.
**Verify:** mapa jagged del subject (subject.md:189-203) produce grid
rectangular; `map[height] == NULL`; printf-debug temporal del grid coincide
linea a linea (espacios → '1').

### T5 — Cableado
Llamada en el orquestador (D7), prototipos publicos en cub3d.h, Makefile:
`parsing/parsing_utils.c`, `parsing/create_game_map.c`.
**Verify:** make sin warnings en Linux.

### T6 — Mover free_file_lines
De su posicion P0 (tras get_file_data) a tras create_map OK.
**Verify:** valgrind happy-path (con get_temp_map aun activo) sin
definitely lost de file_lines.

### T7 — Commit S05A
`feat(parsing): build map grid with dimensions and space-to-wall fill`
Marcar S05A ✅ en tabla maestra. DoD cronograma.md:629-635 entero antes.

---

## PARTE 2 — S06A (tareas)

### T1 — check_map.c
valid_char + scan (chars, contador jugador, celda/letra) + ERR_INVALID_CHAR /
ERR_PLAYER_COUNT.
**Verify:** forbidden.cub ('2'), player_none.cub, player_multiple.cub,
tab_in_map.cub → cada uno su error.

### T2 — check_map_borders.c
Filas 0/h-1 y columnas 0/w-1 (D4).
**Verify:** wall_hole_north.cub, open_side.cub, player_on_border.cub → error;
subject_map.cub pasa.

### T3 — check_textures.c
Missing ids + .xpm + open/read/EISDIR (D4).
**Verify:** textures_missing.cub, tex_not_xpm.cub, tex_is_dir.cub,
tex_nonexistent.cub → error con detail del path.

### T4 — Spawn VECTORIAL (D5)
set_player_spawn en check_map.c (≤5 funcs/fichero) o fichero propio si no cabe:
`pos = celda + 0.5`, tabla dir/plane por letra (N/S/E/W), letra→'0'.
**Verify:** printf-debug temporal: N→dir(0,-1) plane(0.66,0); E→dir(1,0)
plane(0,0.66); celda del jugador contiene '0' tras spawn.

### T5 — Swap + init_player (commit de integracion, 🔄 avisar a Rodrigo)
Eliminar get_temp_map; cambiar `free(data->map)` de exit_game a liberar fila a
fila + array (ya no son literales); init_player (vectorial) deja de tocar
pos/dir/plane (lo pone el spawn). TODO en un commit (trampas 6-7).
**Verify:** `./cub3D maps/good/subject_map.cub` renderiza el mapa REAL del
subject y apareces donde esta la N mirando bien (no en espejo). ESC → valgrind
0 definitely lost (MLX aparte: si X11/MLX ensucia, crear mlx.supp y anotarlo).

### T6 — Bateria de fixtures S05A/S06A
`maps/bad/`: wall_hole_north.cub, open_side.cub, player_none.cub,
player_multiple.cub, forbidden.cub, tab_in_map.cub, map_too_small.cub,
empty_line_in_map.cub, id_after_map.cub, no_map.cub, player_on_border.cub,
textures_missing.cub, tex_not_xpm.cub, tex_is_dir.cub, tex_nonexistent.cub.
`maps/good/`: subject_map.cub (copia LITERAL del ejemplo subject.md:189-203),
minimal.cub (5x3 con un jugador), spaces_inside.cub (espacios interiores),
trailing_newlines.cub, crlf_map.cub.
**Verify:** bucle sobre maps/bad/: exit 1 + stderr empieza por "Error";
bucle sobre maps/good/: abre ventana. Todos bajo valgrind (los bad sin
supresion: nunca llegan a mlx_init — argumento de defensa).

### T7 — Commit S06A + sincronia
`feat(parsing): validate map, spawn player and render real maps`
Marcar S06A ✅ + SYNC3 + ⭐M3 con Rodrigo (anti-fisheye, dibujo de columnas y
suelo/techo planos YA integrados con el motor vectorial — M3 demostrable).

---

## Funciones permitidas (verificadas en TU libft / subject Ch.V)

Nuevas llamadas: `malloc`, `free`, `open`, `read`, `close`, `strerror` —
todas en subject.md:100. Libft: `ft_strlen`, `ft_strncmp`, `get_next_line`
(ya en uso). El spawn vectorial usa una TABLA fija dir/plane (sin cos/sin).
NADA de `stat`/`fstat` para texturas (forbidden): solo el truco open/read/EISDIR.
Utilidades nuevas (is_a_white_space, skip_spaces, find_biggest_len, frees,
build_row...) son codigo propio.

## DoD global (Linux, antes de marcar nada)

```bash
make re                                    # 0 warnings
norminette sources/ includes/              # 0 errores
for f in maps/bad/*.cub;  do ./cub3D "$f"; echo "$f -> $?"; done   # todos 1 + Error en stderr
for f in maps/good/*.cub; do valgrind --leak-check=full ./cub3D "$f"; done  # ESC manual, 0 definitely lost
git log --oneline -3 && git show HEAD --stat   # commits limpios, sin binarios
```

## Riesgo residual

1. **Header compartido**: tras el 2o merge cub3d.h ya tiene el vectorial; tu
   cambio (3 ints + error strings + prototipos) es aditivo. Aviso a Rodrigo
   antes del commit que lo toque (D0) y del commit de integracion (T5).
2. **Deriva del cronograma**: con el motor ya VECTORIAL, S07A (vector+plano)
   coincide con el modelo — el spawn dir/plane de S06A se lo adelanta. Lo que
   queda de S07A son los hooks (ya integrados en input.c): revisar y recortar
   al llegar (anotarlo, no hacerlo ahora).
3. **Decision espacios=muro**: defendible y bendecida por roadmap.md:768,
   pero en defensa pueden preguntar por flood fill. Tener la equivalencia de
   D4 ensayada (preguntas.md es buen sitio para apuntarla — tuyo).
4. **mlx.supp** aun no existe en el repo (CLAUDE.md lo menciona): nace en
   T5-S06A si valgrind lo pide. Si no hace falta, mejor.
