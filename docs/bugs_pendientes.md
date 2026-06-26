# Bugs pendientes — Stress test pre-merge `mejoras-B` → `dev` (2026-06-26)

Análisis adversarial estático (2 agentes, sin compilar — mac). Tracearon los 27
`maps/bad/*`, libft, init/exit y todo el mod/render. **Norminette 0 errores, 0 funciones
prohibidas, 0 crashes/leaks alcanzables.** El trabajo B reciente (font, B2, escopeta) salió
limpio. Lo de abajo es pre-existente del mod/parser. Marca `[x]` según arregles.

---

## 🔴 Arreglar ANTES de mergear

### [ ] 1. Enemigo hace daño a través de muros/puertas (E_ATTACK sin distancia/LOS)
- **Fichero:** `sources/bonus/mod/player_state.c:22-29` (`update_player_hp`).
- **Qué pasa:** el daño (-10 HP cada `ATTACK_RATE`) se aplica con solo `state == E_ATTACK`,
  sin mirar distancia ni línea de visión. Repro: atraes a un grunt por una puerta, la
  cierras (E) y te sigue drenando vida a través de ella a distancia ~1.3.
- **Cómo arreglar:** solo aplicar daño si el enemigo está de verdad en cuerpo a cuerpo Y
  hay LOS. Extrae un helper (`has_los` ya es pública en `cub3d.h`):
  ```c
  static int  enemy_can_hit(t_data *data, t_enemy *e)
  {
      double  dx;
      double  dy;

      dx = e->pos_x - data->player.pos_x;
      dy = e->pos_y - data->player.pos_y;
      if (dx * dx + dy * dy > 1.0)          /* fuera de melee */
          return (0);
      return (has_los(data, e->pos_x, e->pos_y));
  }
  ```
  y en `update_player_hp` cambia el guard a:
  `if (data->enemies[i].state == E_ATTACK && enemy_can_hit(data, &data->enemies[i]))`.
  - Norma: `player_state.c` pasa de 2 a 3 funcs (≤5 ✓), `enemy_can_hit` 2 vars ✓.

### [ ] 2. FSM: fall-through 1 tick + enemigo congelado en ATTACK a 1.0–1.4
- **Fichero:** `sources/bonus/mod/enemy_ai.c:66-78` (`enemy_fsm`).
- **Qué pasa:** los `if` sin `else` dejan saltar IDLE→CHASE→ATTACK en un mismo frame; y en
  `E_ATTACK` no se llama a `chase_player`, así que entre d=1.0 y d=1.4 el enemigo se queda
  quieto (solo vuelve a CHASE si `d > 2.0`).
- **Cómo arreglar:** encadena con `else if` para que cada transición gaste un frame:
  ```c
  if (e->state == E_IDLE)
      e->state = E_CHASE;
  else if (e->state == E_CHASE)
  { chase_player(data, e); if (d < 1.0) e->state = E_ATTACK; }
  else if (e->state == E_ATTACK)
  { if (d > 2.0) e->state = E_CHASE; }
  ```
  Con el fix #1 ya no hace daño en esa franja; si además quieres que siga acercándose,
  llama a `chase_player` también dentro del bloque ATTACK cuando `d > 1.0`.

---

## 🟡 Tu dominio B (render) — pulido opcional

### [ ] 3. `render_sprites` no ordena por profundidad + código muerto
- **Ficheros:** `sources/render/render_sprites.c:85-99`; `sources/render/sprites.c:72,88`
  (`sort_sprites` / `compute_sprite_distances` definidas pero **nunca llamadas**;
  prototipos en `cub3d.h:286-287`).
- **Qué pasa:** los sprites `2`/`3` se pintan en orden de mapa; dos solapados se tapan mal
  (el z-buffer solo ocluye sprite-vs-pared). Además quedan 2 funciones muertas (riesgo en
  defensa / YAGNI).
- **Cómo arreglar (elige una):**
  - (a) Llama `compute_sprite_distances(data); sort_sprites(data);` al inicio de
    `render_sprites` → reusa el código existente, arregla el orden, elimina el "muerto".
  - (b) Si no quieres ordenar, **borra** las 2 funciones + sus prototipos (cub3d.h:286-287).
  - Recomendado: (a).

### [ ] 4. `project_sprite` usa `transform_y > 0` (inconsistente con enemigos)
- **Fichero:** `sources/render/render_sprites.c:95`.
- **Qué pasa:** `enemy_render.c:116` usa `> 0.1`; aquí `> 0`. Si un sprite queda pegadísimo
  al plano de cámara, `size = (int)fabs(WIN_H/transform_y)` desborda al castear (UB; el OOB
  lo evita `put_pixel`, pero el guard es inconsistente).
- **Cómo arreglar:** cambia `> 0` por `> 0.1`.

---

## 🟢 Dominio A / pendiente (decidir en el merge)

### [ ] 5. Restart con `KEY_R` — LO IMPLEMENTO YO EN ESTA RAMA B
El HUD ya muestra `PRESS R TO RESTART` (B), falta la lógica. Como el visual ya es mío, lo
cierro aquí en vez de esperar a A. Plan (de `plan_mejoras_A.md` A2, adaptado, **sin BFS**):

**5.1 Guardar el spawn al parsear** — `sources/parsing/check_map.c`, en `set_player_at`
(l.47-59), ANTES de `data->map[i][j] = '0'` (l.58):
```c
data->spawn_x = j + 0.5;
data->spawn_y = i + 0.5;
data->spawn_dir = c;
```

**5.2 `cub3d.h`:**
- En `t_data`: `double spawn_x; double spawn_y; char spawn_dir;`
- `# define KEY_R 114`
- Prototipo `void restart_game(t_data *data);`
- Quitar `static` a `set_ns`/`set_ew` (check_map.c) + prototiparlas, para reusarlas al
  recolocar la dirección (o duplica su lógica en restart.c si prefieres no tocarlas).

**5.3 Nuevo `sources/bonus/mod/restart.c`** (4 funcs ≤5 ✓):
```c
void        restart_game(t_data *data);
static void reset_player(t_data *data);     /* pos=spawn_x/y; dir=set_ns/set_ew(spawn_dir); keys=0 */
static void reset_mod_state(t_data *data);  /* wave/hp/estado/niebla/arma/enemies */
static void reset_doors(t_data *data);      /* recorre map: 'O' -> 'D' */
```
Tabla de reset:
| Campo | Valor |
|---|---|
| `player.pos_x/y` | `spawn_x/y` |
| `player.dir_*/plane_*` | `set_ns`/`set_ew` segun `spawn_dir` |
| `player.key_*`, `rotate_*` | 0 |
| `wave` | 1 |
| `player_hp` | 100 |
| `game_state` | `G_PLAY` |
| `fog` | 0 |
| `weapon.state/timer`, `fire` | `W_IDLE` / 0 / 0 |
| `gun_frame/gun_firing/gun_timer` | 0 |
| `enemies` | `free()` + `NULL` |
| `enemy_count/last_spawn/spawn_relax` | 0 |
| Puertas en `map` | `'O'` -> `'D'` |
| `seed` | (opcional) re-seed con `gettimeofday` para variar oleadas |

> No hay flujo BFS que resetear en esta rama. `update_sim` re-spawnea la oleada 1 solo al
> ver `enemy_count == 0`, asi que tras el reset arranca sola.

**5.4 Hook** — `sources/movement/input_bonus.c`, en `key_press_bonus` (tras el `KEY_ESC`, l.43):
```c
if (keycode == KEY_R && data->game_state != G_PLAY)
    restart_game(data);
```
Gateado a `!= G_PLAY` para que R solo reinicie en pantalla de fin.

**5.5 `Makefile`:** `+ bonus/mod/restart.c` en `BONUS_SRC`.

**Gate:** en G_OVER/G_WIN pulsas R -> vuelves al spawn con hp 100, oleada 1, sin enemigos,
puertas cerradas, niebla off, y el juego sigue normal. Sin leaks (el `free(enemies)` evita
acumular). Norminette 0.

### [ ] 6. Cierre de mapa: sella espacios en vez de rechazar (sin flood-fill)
- **Ficheros:** `sources/parsing/check_map_borders.c` (solo perímetro),
  `sources/parsing/create_game_map.c:68` (`' '` → `'1'`).
- **Qué pasa:** los espacios interiores se convierten en muro, así que un `0` junto a un
  espacio se **acepta** (sellado) en vez de **rechazarse**. Es zona gris de cub3D: tratar
  espacio como muro es válido para muchos correctores, pero algunos estrictos exigen error.
  No es crash. Dominio A (parser, mandatory).
- **Cómo arreglar (solo si tu corrector es estricto):** flood-fill desde la posición del
  jugador sobre la rejilla; si la inundación alcanza un `' '` o el borde del array → error
  `ERR_MAP_NOT_CLOSED`. Hacerlo ANTES de convertir espacios a `'1'`.

---

## ⚪ Extremos / baja prioridad

### [ ] 7. Leak de `file_lines` si falla el 2.º `open()` (TOCTOU)
- **Fichero:** `sources/parsing/parsing_data.c` (`parsing()` hace `return (FAILURE)` sin
  `free_parsing` cuando `fill_lines` falla tras alocar el array).
- **Trigger:** el fichero deja de ser legible entre contar y rellenar. Casi inalcanzable.
- **Cómo arreglar:** llamar `free_parsing(data)` antes de ese `return (FAILURE)`.

### [ ] 8. G_WIN espurio / soft-lock en casos degenerados
- **Fichero:** `sources/bonus/mod/waves.c:97-109` + `sim.c`.
- **Qué pasa:** (a) si `malloc` de `enemies` falla, `last_spawn` no se resetea y
  `check_wave_advance` podría cascadear hasta G_WIN (solo bajo OOM). (b) si una oleada no
  tiene celdas spawneables ni en modo relax, `placed=0` y la partida se congela sin
  enemigos (mapas diminutos/degenerados). No es crash.
- **Cómo arreglar:** en el fallo de malloc, `data->last_spawn = 0` antes del return; y si
  `placed == 0`, saltar la oleada o terminar la partida en vez de quedar colgado.

---

## ✅ Verificado limpio (no tocar)
- `norminette sources/ includes/` → 0 errores. 0 funciones prohibidas (incl. `abs`).
  Solo math `-lm` (`sin/cos/sqrt/fabs/floor`). Sin `for/switch/goto`/globales no-const.
- Memoria: todos los `malloc` con NULL-check; `destroy_game`+`free_parsing` liberan todo
  sin doble free; `spawn_wave` deja `enemies/enemy_count` consistentes si falla.
- Los 27 `maps/bad/*` se rechazan correctamente.
- `has_los` div/0 (`utils.c:29-31`): **NO es bug** — si d==0 el `while (d>0.1)` no entra y
  el NaN nunca se usa. (Si quieres defensivo: `if (d < 0.01) return (1);` al principio.)
- Trabajo B reciente (`font.c`, `game_loop.c` B2, `shotgun_draw.c`): sin defectos.
