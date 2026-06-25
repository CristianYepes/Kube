# SPEC — Terminar cub3D entero (fixes + puertas + mod zombies completo)

## Contexto

Rodrigo, en la rama `bonus` (= `dev` + 2 commits suyos), se adelantó: hizo el **minimapa**
(que era tarea A), **ratón**, **sprites animados** y metió una **escopeta cosmética** —
pero **sin** el contrato pactado, tocando `cub3d.h` en solitario, rompiendo la norma (6
ficheros) y reintroduciendo **fugas de memoria (~13 MB)**. Del **mod de zombies de los dos
MD no hay nada**: cero contrato, cero lógica (oleadas/IA/hitscan/vida/estados/niebla/HUD),
y del render solo fragmentos sueltos. **El mod render reutilizará el código de Rodrigo.**

Cristian (Persona A) asume **todo** el trabajo restante (roles A y B). Objetivo: dejar el
proyecto **entregable y completo** = mandatory + 5 bonus oficiales **+ el mod entero**, sin
fugas, norma limpia, sin crashes. Regla: **arreglar el código de Rodrigo sin reescribirlo**,
preservando su trabajo; el render del mod **reutiliza** su infra de sprites/escopeta.

> Regla 42 en todo el spec: ≤25 líneas/func, ≤5 funcs/fichero, ≤4 params, ≤5 vars, sin
> globals, sin `rand`/`sprintf`/`stat`. Solo se dan **prototipos + pasos**, no cuerpos.

---

## Decisiones de diseño (asumidas; confírmalas en la revisión)

- **D1 — Separación mandatory/bonus con `-DBONUS` (dos binarios).** `make`→`cub3D` PURO
  mandatory; `make bonus`→`cub3D_bonus` con todo (mismo árbol, `+ -D BONUS`). Lo bonus va bajo
  `#ifdef BONUS`. Cumple el subject §41 (evaluación separada). NO reescribe el código de
  Rodrigo, solo lo guarda en 5 puntos. Detalle en **Fase 0-BIS**.
- **D2 — Textura de puerta:** `int *door_tex` cargado de un asset fijo `textures/door.xpm`
  (64×64), estilo escopeta/sprites. Si no tienes asset, fallback temporal = reusar una
  textura de muro. Sin tocar el formato `.cub`.
- **D3 — Render del mod reutiliza lo de Rodrigo:** `render_enemies` reusa la proyección
  billboard de `render_sprites.c`; `render_weapon` adapta `shotgun.c` (lo conduce
  `weapon.state` en vez del flag local). No se reescribe, se generaliza.
- **D4 — Spawn de zombies sin `rand()`:** LCG propio sembrado con `gettimeofday`.
- **D5 — `dt` real:** se añade `double dt;` a `t_data`, lo calcula `game_loop` (ya lo hace) y
  lo leen `update_sim` y las animaciones. Todos los timers en segundos.

---

## FASE 0 — Estabilizar la rama (sin esto, nada más cuenta)

Devuelve la rama al estándar entregable: **0 fugas, norma limpia, sin desperdicio**.

### 0.1 Fugas en salida (bug confirmado #1)
Nuevo fichero `sources/exit/free_bonus.c`:
```c
void	free_sprites(t_data *data);   /* free sprite_tex[0..1], sprite_tex2[0..1], sprites */
void	free_shotgun(t_data *data);   /* free gun_tex[0..3] */
```
`exit_game()` (en `exit/exit_game.c`) llama a ambas antes de `free_parsing`/`exit`. Cada
`free` con guard `if (ptr)`.

### 0.2 Cleanup unificado en errores de init (bug confirmado #2)
Centralizar la liberación para que valga en cualquier punto de fallo (todos los punteros son
NULL al arrancar por `(t_data){0}`, así que liberar con guard siempre es seguro):
```c
void	destroy_game(t_data *data);   /* en exit_game.c: libera textures, sprites, shotgun,
                                         z_buffer, img, win — TODO con guard, sin exit() ni
                                         free_parsing */
```
- `exit_game()` = `destroy_game(data)` + `free_parsing(data)` + `exit(SUCCESS)`.
- En `init_game.c`, **cada** ruta de fallo: `destroy_game(data); return (err_msg(...));`.
- `main.c` (l.26-30) ya hace `free_parsing` tras fallo de init → queda consistente.

### 0.3 Norma de `init_game.c` (>25 líneas)
Extraer el setup MLX:
```c
static int	init_mlx(t_data *data);   /* mlx_init + new_window + new_image + get_data_addr */
```
`init_game` queda: `init_player` → `init_mlx` (check) → `z_buffer` (check) → `init_textures`
(check) → `init_sprites_data` (check) → `init_shotgun` (check). ~12 líneas.

### 0.4 Resto de norma (5 errores)
- `game_loop.c:33` → línea en blanco entre `tick_sprite_anim` y `game_loop`.
- `render_sprites.c:33,36` → quitar tabs sobrantes en las líneas de continuación.
- `shotgun.c` (>5 funcs) → mover `draw_gun_layer` + `draw_crosshair` a nuevo fichero
  `sources/render/shotgun_draw.c`. `shotgun.c` queda con init/fire/tick/draw_shotgun (4).
- `cub3d.h:172` → alinear `struct timeval last_time;` con el ancho del tipo (norminette
  `MISALIGNED_VAR_DECL`).

### 0.5 Escopeta fuera de pantalla + descentrada (bug confirmado #3)
En `shotgun_draw.c`:
- Reposicionar: `start_x = WIN_W / 2 - GUN_SIZE / 2;` (quitar el `+500` → centrada).
  `start_y = WIN_H - GUN_SIZE;` (la parte baja del arma ocupa la pantalla, estilo FPS).
- **Recortar el bucle** a la intersección con la pantalla (no iterar 900×900 a ciegas):
  acotar `x` a `[max(0,-sx), min(GUN_SIZE, WIN_W-sx))` y `y` análogo. Elimina el desperdicio.

### 0.6 Minimap a esquina inferior-izquierda (sospechoso #3, DoD S10A)
Añadir offset a `t_data`: `int mini_x; int mini_y;`. En `display_minimap` fijar `mini_x = 0`
y `mini_y = WIN_H - alto_minimap` (alto = `map_height*20` o 190). Sumar `data->mini_x/mini_y`
**dentro** de las 4 primitivas (`draw_square`, `draw_player`, `draw_sprite`, `draw_frame`) en
sus llamadas a `put_pixel`. `draw_map`/`draw_map2` no cambian (usan las primitivas). No añade
params (offset viaja por `data`).

### 0.7 Hardening opcional (baratos, baja prioridad)
- `draw_wall_column`: `if (!ray->hit) { data->z_buffer[x] = 1e30; return; }` (mata la columna
  fantasma del sospechoso #1; inalcanzable en mapa cerrado pero defensivo).
- `project_sprite`: `if (data->sprites[i].transform_y <= 0) return;` al principio (evita el
  div por `transform_y` del sospechoso #2). El det del determinante NO se toca (≈±0,66 fijo).
- **NO** restaurar `has_moved` (bug #4): rompería las animaciones del bonus/mod. El
  redibujado continuo es correcto; el desperdicio ya se quita en 0.5.

### 0.8 `abs()` PROHIBIDO (bloqueante — subject §100) — hallazgo auditoría
`render_sprites.c:81` usa `abs()`, que NO está en las funciones permitidas (es de
`<stdlib.h>`, no de `man 3 math`). Una función no permitida = **0 en la evaluación**.
- Fix: `data->sprites[i].size = (int)fabs(WIN_H / data->sprites[i].transform_y);`
  (`fabs` SÍ está permitida, math `-lm`). Alternativa: negación manual.
- **Grep de control:** `grep -rn "\babs\b" sources/` debe dar 0 (no confundir con `fabs`).

### 0.9 Validación de F/C ausente (bug del parser mandatory) — hallazgo auditoría
`fill_color_textures.c` marca `id_flags |= (1<<4)` (F) / `(1<<5)` (C), pero **nadie comprueba
esos bits**: `validate_map` solo valida texturas. Un `.cub` **sin** `F` o `C` se acepta y
pinta negro (`floor/ceiling` = 0 por `(t_data){0}`). El subject exige ambos.
- Fix: en `validate_map` (`parsing_data.c`) o al final de `check_textures`, exigir
  `(data->id_flags & (1<<4)) && (data->id_flags & (1<<5))`; si falta uno → `err_msg`.
- Necesita string nuevo: `# define ERR_MISSING_COLOR "Missing floor/ceiling color"`.

### 0.10 Limpieza menor — hallazgo auditoría
- **Prototipo duplicado:** `cub3d.h:225` y `:238` declaran `mouse_tracker` dos veces → borrar
  uno.
- Opcionales: `init_sprites` ignora su parámetro `type` (`(void)type` en `sprites.c:55`,
  funciona por hardcodear `'2'||'3'`) · `mlx_get_data_addr` (init_game.c:27) sin null-check ·
  `mlx_destroy_display(data->mlx)+free` en `destroy_game` (más limpio; ya cubierto por
  `mlx.supp`, así que NO es bloqueante).

**Gate Fase 0 (Linux):** `make` 0 warnings · `norminette sources/ includes/` 0 errores ·
`grep -rn "\babs\b" sources/` → 0 · `.cub` sin `F`/sin `C` → **rechazado** con "Error\n" ·
`valgrind --suppressions=mlx.supp ./cub3D maps/good/subject_map.cub` → `definitely lost: 0`
abriendo y cerrando con ESC y con la cruz.

---

## FASE 0-BIS — Separación mandatory/bonus (`-DBONUS`, dos binarios) [subject §41]

Objetivo: `make`→`cub3D` mandatory PURO; `make bonus`→`cub3D_bonus` (mismo árbol, `+ -D BONUS`).
Sin reescribir lógica: un macro + guardas en **5 puntos** de acoplamiento + Makefile.

### Los 5 puntos de acoplamiento (lo único que se toca)
1. **Charset del parser** — en `cub3d.h`:
   ```c
   # ifdef BONUS
   #  define MAP_CHARS "0123DNSEW"
   # else
   #  define MAP_CHARS "01NSEW"
   # endif
   ```
   y en `check_map.c:96` usar `ft_strchr(MAP_CHARS, ...)`.
2. **`init_game.c`** — `#ifdef BONUS` alrededor de `init_sprites_data` + `init_shotgun`
   (+ carga de `door_tex` de Fase 1). El mandatory no carga esos assets.
3. **`game_loop.c`** — `#ifdef BONUS` alrededor del bloque bonus (sprites/escopeta/minimap +
   `update_sim`/render del mod). Loop mandatory = `move_player`→`paint_floor_ceiling`→
   `cast_rays`→`put_image`.
4. **`input.c`** — guardar los `if` de `M` (minimap), disparo y `E` (puertas). **WASD, flechas
   (rotación, ES mandatory) y ESC se quedan.**
5. **`mlx.c`** — guardar los 2 `mlx_hook` de ratón (eventos 4 y 6). El resto, mandatory.

### Makefile
- `SRC` (mandatory + compartidos): main, error, parsing/*, init_game, init_textures,
  render_utils, raycasting, game_loop, textures, floor_ceeling, draw_wall, player, input,
  exit/*, mlx.
- `BONUS_SRC` (solo bonus): minimap, minimap_2, sprites, render_sprites, shotgun, shotgun_draw,
  init_sprites, doors + ficheros del mod (`bonus/mod/*`, `bonus/render/*`).
- `all`: compila `SRC` SIN flag → `cub3D` (objetos en `obj/`).
- `bonus`: compila `SRC` + `BONUS_SRC` CON `-D BONUS` → `cub3D_bonus` (objetos en `obj_bonus/`
  — imprescindible: los compartidos se recompilan con el flag). Quitar `bonus: all`.

### Por qué el mandatory linka sin los .c de bonus
Las llamadas a funciones bonus (p.ej. `render_sprites`) están bajo `#ifdef BONUS`; en el build
mandatory no se referencian → no hay símbolo sin resolver aunque su `.c` no se compile.

### Notas
- Los campos bonus de `t_data` (sprites/gun/door/mod) se quedan SIEMPRE definidos (unos bytes
  sin usar en mandatory) → evita `#ifdef` dentro del struct. Simplicidad.
- `#ifdef` es válido en la Norma.
- Cumplimiento estricto extra (opcional): renombrar los `.c` bonus a `_bonus.c`.

**Hacerlo PRONTO** (justo tras Fase 0) para que puertas y mod se añadan ya bajo `#ifdef BONUS`.

**Gate Fase 0-BIS:** `make`→`cub3D` **rechaza** un `.cub` con `'2'/'3'/'D'` y no pinta extras;
`make bonus`→`cub3D_bonus` con todo; ambos norma 0 + valgrind 0.

---

## FASE 1 — Puertas (S11A, 5º bonus oficial)

### Contrato (en `cub3d.h`)
```c
# define KEY_E 101
# define DOOR_CLOSED 'D'
# define DOOR_OPEN   'O'
/* t_data: */ int *door_tex;
/* t_ray:  */ int is_door;
```

### 1.1 Parser (acepta 'D')
- `check_map.c:96`: charset `"0123DNSEW"` (añadir `'D'`). `'O'` NO se acepta del fichero (es
  estado en runtime). `build_row` ya preserva `'D'` (no es espacio). El borde sigue siendo
  todo `'1'` → las puertas quedan forzadas a ser **interiores** (correcto).

### 1.2 Textura de puerta (D2)
- Cargar `data->door_tex = xpm_to_int(data, "textures/door.xpm");` en `init_textures` (o un
  paso nuevo `init_door`), con su check. Liberar en `destroy_game`.

### 1.3 Colisión (puerta cerrada bloquea)
- `is_wall` (`player.c`): `return (c == '1' || c == DOOR_CLOSED);`. Esto hace que **jugador y
  zombies** choquen con puertas cerradas (zombies reusan `is_wall` en Fase 3).

### 1.4 Raycasting (pinta la puerta cerrada, deja pasar la abierta)
- `perform_dda`: golpe cuando `cell == '1' || cell == DOOR_CLOSED`; al golpear, marcar
  `ray->is_door = (cell == DOOR_CLOSED)`. `DOOR_OPEN` no es golpe → el rayo pasa.
- `get_tex_color` (`draw_wall.c`): si `ray->is_door` usar `data->door_tex` en vez de
  `data->textures[ray->tex_idx]`.

### 1.5 Toggle con 'E'
Nuevo `sources/movement/doors.c`:
```c
void	toggle_door(t_data *data);   /* celda de delante: cx=(int)(pos_x+dir_x),
                                        cy=(int)(pos_y+dir_y); con bounds-check:
                                        'D'->'O', 'O'->'D'. No cerrar si el jugador
                                        está sobre esa celda. */
```
- `input.c` `key_press`: `if (keycode == KEY_E) toggle_door(data);`.

**Gate Fase 1:** la puerta abre/cierra con E, **bloquea** cerrada, **se ve** (textura) cerrada
y deja ver detrás abierta; valgrind 0 fugas; norma limpia.

---

## FASE 2 — Mod Cluster 0 (el contrato + esqueleto andante)

Trae el contrato **byte-idéntico de los dos MD** a `cub3d.h` (defines `ENEMY_*`, `E_*`,
`W_*`, `G_*`, `FIRE_COOLDOWN 0.6`, `ATTACK_RATE 1.0`, `DEATH_TIME 0.4`; structs `t_enemy`,
`t_weapon`; campos en `t_data`: `enemies`, `enemy_count`, `wave`, `player_hp`, `game_state`,
`fog`, `weapon`, `enemy_tex[12]`, `weapon_tex[6]`). Añadir también `double dt;` (D5) y el flag
A-interno `int fire;`.

### 2.1 Stubs + orden del game loop (contrato MD)
```c
void	update_sim(t_data *data);      /* stub vacío */
void	render_enemies(t_data *data);  /* stub vacío */
void	render_weapon(t_data *data);   /* stub vacío (luego adapta shotgun) */
void	render_hud(t_data *data);      /* stub vacío */
```
`game_loop` en orden MD: `move_player` → `update_sim` → `paint_floor_ceiling` → `cast_rays`
→ `render_enemies` → `render_weapon` → `render_hud` → (minimap) → `put_image`.
`game_loop` escribe `data->dt`.

### 2.2 Init de estado de juego
En init: `wave=1`, `player_hp=100`, `game_state=G_PLAY`, `fog=0`, `weapon={W_IDLE,0}`,
`enemies=NULL`, `enemy_count=0`.

**Gate Fase 2:** compila y corre igual que antes (los stubs no hacen nada) = esqueleto andante.

---

## FASE 3 — Mod lógica (lado A). Ficheros en `sources/bonus/mod/`

Exponer `is_wall` (quitar `static` en `player.c` + prototipo en `cub3d.h`) para que la IA la
reuse. Todo se prueba con `printf` antes de tener render.

### 3.1 `waves.c` — modelo + oleadas (A1)
```c
unsigned int	lcg_next(unsigned int *seed);          /* PRNG sin rand() (D4) */
int				count_floor_cells(t_data *data);       /* celdas '0' */
void			spawn_wave(t_data *data, int wave);    /* aloca enemies[], coloca lejos
                                                          del jugador con lcg_next */
void			next_wave(t_data *data);               /* libera oleada, ++wave, respawn */
```
- wave 1 = grunts, wave 2 = runners, wave 3 = boss + `fog=1`. Avanza cuando `enemy_count==0`.

### 3.2 `enemy_ai.c` — FSM + chase (A2)
```c
void	update_enemies(t_data *data);                  /* recorre enemies[], aplica FSM */
/* helpers static: enemy_fsm(data,e), chase_player(data,e) reusando is_wall + slide;
   rangos con distancia² (sin sqrt). grunt lento, runner rápido, boss lento+mucha hp. */
```
- `E_IDLE → E_CHASE` (ve al jugador / en rango) → `E_ATTACK` (pegado) → `E_DEAD` (hp≤0,
  `timer=DEATH_TIME`; al expirar se compacta fuera del array, `enemy_count--`).

### 3.3 `combat.c` — disparo + hitscan (A3)
```c
void	try_fire(t_data *data);   /* si weapon.timer==0 y data->fire: hitscan + cooldown */
/* helpers: hitscan(data) marcha un rayo desde pos en dir; para en muro/puerta cerrada
   (reusa la lógica DDA); si pasa cerca de un enemigo en cono/rango → daño/kill.
   Pone weapon.state=W_FIRING + weapon.timer=FIRE_COOLDOWN. */
```
- El flag `data->fire` lo pone `input.c` (tecla disparo / clic, ya existen) y lo consume aquí.

### 3.4 `player_state.c` — vida + estados (A4)
```c
void	update_player_hp(t_data *data);   /* enemigo en E_ATTACK resta hp cada ATTACK_RATE */
void	check_game_state(t_data *data);   /* hp<=0 → G_OVER; boss muerto en wave3 → G_WIN */
```

### 3.5 `sim.c` — orquestador (A5)
```c
void	update_sim(t_data *data);   /* if game_state!=G_PLAY return; tick weapon.timer;
                                       update_enemies; try_fire; update_player_hp;
                                       check_game_state; progresión de oleadas */
```
- `enemies[]` se libera en `next_wave` y en `destroy_game` (añadir `free(enemies)` allí).

**Gate Fase 3 (printf, sin render):** "wave 1: N enemigos" → matar todos → "wave 2" → … →
boss muerto → "G_WIN"; posiciones convergen al jugador y **paran en muros/puertas**; "hit
enemy k", "blocked by wall", cooldown respetado; hp baja con zombie pegado → "G_OVER".

---

## FASE 4 — Mod render (lado B). Ficheros en `sources/bonus/render/`

Reutiliza la infra existente (D3). La **regla de oro**: aquí solo se LEE el estado, nunca se muta.

### 4.1 `enemy_render.c` — sprites de enemigos (B1+B2)
- Generalizar `project_sprite`/`draw_sprite_3d`/`draw_sprite_col` (de `render_sprites.c`)
  para que tomen una posición + un buffer de textura, y llamarlas desde:
```c
void	render_enemies(t_data *data);   /* ordena enemies por dist² desc; por cada uno
                                           proyecta (billboard + z-buffer) y dibuja el frame */
int		enemy_frame(t_enemy *e);        /* índice en enemy_tex[] según (type,state)+timer */
```
- Reusa el z-buffer que ya rellena `cast_rays` (muro tapa al enemigo). `E_DEAD` reproduce la
  anim de muerte durante `DEATH_TIME` (sincronizado con A por la constante).

### 4.2 `weapon.c` — escopeta conducida por estado (B3)
- Adaptar `draw_shotgun`/`tick_shotgun` para leer `weapon.state`/`weapon.timer` (en vez del
  `gun_firing` local): `W_IDLE` → frame base; `W_FIRING` → frames de disparo según el tiempo
  dentro de `FIRE_COOLDOWN`. Añadir el detalle **"-42"** (en la textura del arma o dibujado).

### 4.3 `fog.c` — niebla (B4)
```c
int	apply_fog(int color, double dist, int fog);   /* oscurece hacia negro/techo por dist */
```
- Llamar desde `get_tex_color` (muros, con `wall_dist`) y desde el draw de enemigos (con su
  dist) cuando `data->fog == 1`.

### 4.4 `hud.c` — HUD mínimo (B4)
```c
void	render_hud(t_data *data);   /* barra/numero de vida + oleada con put_pixel,
                                       SIN texto de libc (mini-bitmap a mano) */
```

**Gate Fase 4:** enemigos aparecen, animan y **los tapan los muros**; arma siempre visible y
reproduce disparo con `W_FIRING`; con `fog=1` la escena oscurece por distancia; HUD muestra
vida/oleada; pantallas de `G_WIN`/`G_OVER`.

---

## FASE 5 — Integración + cierre

- Cargar `enemy_tex[12]`/`weapon_tex[6]` estilo `init_textures` (reusar `xpm_to_int`, valida
  64×64); **liberar en `destroy_game`** (enemy_tex, weapon_tex, enemies).
- Quitar todos los stubs; `game_loop` completo en orden de contrato.
- `make bonus` 0 warnings · `norminette` 0 · `valgrind` 0 fugas jugando una partida entera
  (3 oleadas, disparar, abrir/cerrar puertas, morir/ganar, salir con ESC).

---

## Assets que tienes que crear (XPM, formato C, paleta `2` chars/pixel)

| Asset | Tamaño | Para |
|---|---|---|
| `textures/door.xpm` | 64×64 | puerta cerrada (Fase 1) |
| `enemy_tex[12]` (grunt/runner/boss × walk0/walk1/attack/death) | 64×64 | zombies (Fase 4) |
| `weapon_tex[6]` con "-42" | el actual ya va | escopeta del mod (Fase 4) |

> Si no tienes door.xpm a mano: fallback temporal reusando una textura de muro (D2).

---

## Ficheros tocados / nuevos (mapa rápido)

- **Fase 0:** `exit/exit_game.c`, **+`exit/free_bonus.c`**, `init/init_game.c`,
  `render/game_loop.c`, `render/render_sprites.c`, `shotgun.c` **+`render/shotgun_draw.c`**,
  `render/minimap.c`, `render/minimap_2.c`, `render/draw_wall.c`, `render/raycasting.c`,
  `includes/cub3d.h`, `Makefile`.
- **Fase 1:** `parsing/check_map.c`, `init/init_textures.c`, `movement/player.c`,
  `render/raycasting.c`, `render/draw_wall.c`, `movement/input.c`, **+`movement/doors.c`**,
  `includes/cub3d.h`, `Makefile`.
- **Fases 2-5:** `includes/cub3d.h`, `render/game_loop.c`, `init/init_game.c`,
  `exit/exit_game.c`, **+`sources/bonus/mod/{sim,waves,enemy_ai,combat,player_state}.c`**,
  **+`sources/bonus/render/{enemy_render,weapon,fog,hud}.c`**, `Makefile`.

---

## Verificación global (DoD)
```bash
make && make bonus                 # 0 warnings
norminette sources/ includes/      # 0 errores
valgrind --leak-check=full --suppressions=mlx.supp ./cub3D maps/good/subject_map.cub
# definitely lost: 0 en: abrir/cerrar, ESC, partida completa (3 oleadas, disparo, puertas,
# G_WIN y G_OVER). Sin segfault/bus error/double free.
```
*(Compilación/valgrind/ejecución las haces tú en Linux; en mac solo norminette + estático.)*

## Riesgos
1. **Separación mandatory/bonus (Fase 0-BIS):** riesgo de olvidar una guarda `#ifdef BONUS` y
   que el mandatory pinte extras o acepte `'2'/'3'/'D'` → verificar con el gate de Fase 0-BIS
   (compilar `make`, probar un `.cub` con `'2'` y confirmar que lo rechaza).
2. **Orden del game loop es compartido (contrato):** al ser solo tú, no hay handoff, pero
   respétalo para que el mod cuadre con los MD.
3. **`is_wall` pasa a no-static** (la usa la IA): comprobar que no rompe nada del mandatory.
4. **Rendimiento** (sprites+niebla+enemigos a 1280×720 por software): medir; optimizar solo
   si hace falta (ya se quitó el desperdicio de la escopeta en 0.5).
5. **`rand()` prohibido:** documentar el LCG para defensa (D4).

---

## Estado de avance (marca aquí según vayas cerrando)
- [x] Fase 0 — estabilizar (fugas, norma, escopeta, minimap, **abs()**, **F/C**, **dup proto**) → `9773b8c`
- [x] Fase 0-BIS — separación mandatory/bonus (`-DBONUS`, dos binarios) [subject §41] → `83ecd5b`
- [x] Fase 1 — puertas (S11A) → `0721951`
- [x] Fase 2 — contrato mod + esqueleto andante → `86dd190`
- [x] Fase 3 — lógica mod (A): spawn, IA, combate, vida → `3256a28` (+ fix spawn con línea de visión + fallback → `beb1a0c`)
- [x] Fase 4 — render mod (B): enemigos (billboard+z-buffer+**animación de frames**), HUD, **niebla `fog.c`**, arma con detalle **"-42"** (`render_weapon`)
- [ ] Fase 5 — integración + DoD final (cargar/free `enemy_tex`/`weapon_tex`, quitar stubs, valgrind/norma partida completa)

### Pendiente concreto (lo que queda)
- **Decisión abierta (polish, mod no puntúa):** ¿pathfinding (BFS flow-field) para que los zombies rodeen muros? El chase sigue siendo recto+slide. Con el spawn-LOS rara vez se nota.
- **Fase 5 — cierre:** verificar valgrind 0 fugas en partida completa (3 oleadas, disparo, puertas, G_WIN/G_OVER) + norminette global.
- **(Opcional) niebla en suelo/techo:** ahora solo afecta muros y enemigos; suelo/techo
  quedan brillantes. Mejora si quieres una niebla más envolvente.
