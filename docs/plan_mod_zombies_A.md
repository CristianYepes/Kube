# MOD Zombies — Plan A (simulación / lógica) — Persona A

> Cubre `update_sim`: oleadas, IA de zombies, combate (hitscan), vida del jugador y
> estados de juego. **El cerebro del mod.** Render-independiente (se prueba con `printf`).
> Pareja: `docs/plan_mod_zombies_B.md` (presentación / render — Rodrigo).
> **Prerequisitos:** (1) bonus oficial de A cerrado (minimapa S10A + puertas S11A);
> (2) **Cluster 0 (contrato) commiteado JUNTO con Rodrigo** antes de empezar A1.

---

## DÓNDE ENCAJA (leer primero)

- **No puntúa.** 42 evalúa mandatory + 5 bonus oficiales. Esto es portfolio/gusto y va
  DESPUÉS de cerrar el bonus oficial (tú: minimapa+puertas; Rodrigo: ratón+sprites).
- **Build:** compila bajo `make bonus` (`-DBONUS`), ficheros en `sources/bonus/`.
- **Método (`/plano`):** capa estable (Cluster 0) entera y por adelantado y JUNTOS; luego
  cada cluster crece cuando llegas a él. El detalle fino de A1–A5 se rellena al llegar;
  aquí van objetivo, tareas y **gate de verificación** de cada uno.
- **El mod = máquina de estados** (oleadas, IA, juego). Es justo el caso de `/plano`/UML.

---

## CONTRATO COMPARTIDO (Cluster 0) — IDÉNTICO EN AMBOS PLANES · FUENTE DE VERDAD

> Único punto de acoplamiento A↔B. Se define y **commitea PRIMERO y JUNTOS** (un commit
> coordinado: `cub3d.h` + esqueleto de `game_loop.c`). Idéntico en `plan_mod_zombies_A.md`
> y `plan_mod_zombies_B.md`; si cambia, se cambia **en los dos a la vez** (coordinar).
> Regla `/plano`: la capa estable se diseña entera por adelantado y solo se toca a propósito.

**Modelo de datos (en `cub3d.h`, SHARED → coordinar el commit):**
```c
/* tipos de enemigo */
# define ENEMY_GRUNT  0
# define ENEMY_RUNNER 1
# define ENEMY_BOSS   2
/* estados del enemigo (FSM) */
# define E_IDLE   0
# define E_CHASE  1
# define E_ATTACK 2
# define E_DEAD   3
/* estado del arma */
# define W_IDLE   0
# define W_FIRING 1
/* estado de juego */
# define G_PLAY 0
# define G_WIN  1
# define G_OVER 2
/* timings compartidos (segundos) — los usan A (lógica) y B (animación) */
# define FIRE_COOLDOWN 0.6
# define ATTACK_RATE   1.0
# define DEATH_TIME    0.4   /* dura la anim. de muerte antes de quitar al enemigo */

typedef struct s_enemy {
    double  x;       /* posición en CELDAS (igual que el jugador) */
    double  y;
    int     type;    /* ENEMY_* */
    int     state;   /* E_* */
    int     hp;
    double  timer;   /* cooldown de ataque / temporizador de muerte (lo lleva A) */
}   t_enemy;

typedef struct s_weapon {
    int     state;   /* W_* (lo escribe A) */
    double  timer;   /* cooldown de disparo (lo lleva A) */
}   t_weapon;

/* añadir a t_data: */
t_enemy  *enemies;      /* array de la oleada actual; A aloca/libera */
int       enemy_count;  /* nº de enemigos vivos en el array */
int       wave;         /* 1..3 */
int       player_hp;
int       game_state;   /* G_* */
int       fog;          /* 0/1 (A lo enciende en la oleada 3) */
t_weapon  weapon;
int      *enemy_tex[12];   /* frames de sprites (B fija el tamaño real); B carga/libera */
int      *weapon_tex[6];   /* frames del arma; B carga/libera */
```

**Orden del game loop (`game_loop.c`, SHARED → coordinar):**
```
1. update_player(data)        [movimiento, ya existe]
2. update_sim(data)           [A] IA + oleadas + combate + arma + vida + game_state + fog
3. paint_floor_ceiling(data)  [B]
4. cast_rays(data)            [B] muros + RELLENA z-buffer
5. render_enemies(data)       [B] sprites billboard, ordenados, con z-buffer
6. render_weapon(data)        [B] overlay + animación de disparo
7. render_hud(data)           [B] vida / oleada
8. put_image                  [B]
   (la niebla se aplica dentro de 4–6 cuando data->fog == 1)
```

**Propiedad (quién hace qué — NADIE cruza la línea):**
| Dato | Aloca/libera | ESCRIBE | LEE |
|---|---|---|---|
| `enemies[]` (array) | **A** (init de oleada / exit) | **A** | B |
| `enemy.x/y/type/state/hp/timer` | — | **A** | B |
| `weapon.state/timer` | — | **A** | B |
| `player_hp, wave, game_state, fog` | — | **A** | B |
| `enemy_tex[], weapon_tex[]` | **B** (carga estilo init_textures / exit) | **B** | B |
| z-buffer (columna→dist) | **B** (en cast_rays) | **B** | B |

**Regla de oro:** A NUNCA toca píxeles/imágenes/texturas; B NUNCA muta
`enemies/weapon/player_hp/game_state/fog`. B solo LEE el estado y lo dibuja.

**Esqueleto andante (primer commit conjunto):** `game_loop.c` llama a `update_sim`,
`render_enemies`, `render_weapon`, `render_hud` como **stubs vacíos** que compilan y corren
(no hacen nada). Demuestra el contrato. Luego A y B rellenan sus stubs en paralelo.

---

## DECISIONES DE DISEÑO (lado A)

### DA1 — Spawn de enemigos (sin tocar el parser mandatory)
- **Recomendado v1:** spawn **procedural** — escanea `data->map` por celdas `'0'` y elige N
  alejadas del jugador (distancia² > umbral). No toca el parser ni el formato `.cub`.
- Opción (más curro): marcador en el `.cub` (p. ej. `'Z'`) aceptado **solo bajo `-DBONUS`**
  en `check_map`. El subject lo permite (Cap. VII: "add symbols on the map… modify the
  scene format"). Bifurca parser mandatory/bonus → dejar para v2.
- **⚠️ `rand()` NO está permitido** (no está en subject Cap. V). Para variar spawns: LCG
  propio sembrado con `gettimeofday` (permitido), o patrón determinista. Documentarlo.

### DA2 — IA = FSM por enemigo + chase directo
- Por enemigo: `E_IDLE → E_CHASE → E_ATTACK → E_DEAD` (ver diagrama en CLAUDE/charla).
- **Movimiento = chase directo reusando `is_wall`/`try_move`** (ya existen en `player.c`):
  vector hacia el jugador, normalizar, paso por `try_move` (desliza en muros). Cero pathfinding.
- Rangos con **distancia²** (sin `sqrt`). Por tipo: grunt lento; runner rápido; boss lento +
  mucha hp (ataque a distancia = otro hitscan, opcional v2).
- Opcional: línea de visión (rayo enemigo→jugador, si no hay muro → `E_CHASE`). Reusa el DDA.

### DA3 — Oleadas (FSM de juego)
- `wave 1` (grunts) → `wave 2` (runners) → `wave 3` (boss + `fog=1`). Avanza cuando
  `enemy_count == 0`. Boss muerto en wave 3 → `game_state = G_WIN`.
- A **realoca** `enemies[]` al entrar en cada oleada (libera la anterior).

### DA4 — Combate (disparo + hitscan)
- Tecla de disparo en `input.c` (input = dominio A): pone un flag `fire` (A-interno, NO va al
  contrato). `update_sim` lo lee.
- Si `weapon.timer` (cooldown) está a 0: **hitscan** — recorre un rayo desde el jugador en
  `dir`; si pega muro antes → fallo; si pega un enemigo dentro de rango/cono → daño; baja hp;
  `hp<=0` → `E_DEAD` (timer `DEATH_TIME`) y al expirar se quita del array (`enemy_count--`).
- Pone `weapon.state = W_FIRING` + arranca cooldown `FIRE_COOLDOWN`; al expirar → `W_IDLE`.

### DA5 — Vida del jugador + estados
- Enemigo en `E_ATTACK` resta `player_hp` cada `ATTACK_RATE`. `player_hp<=0` → `G_OVER`.
- En `G_WIN`/`G_OVER`: congelar simulación; tecla para salir/reiniciar.

### DA6 — Tiempo (delta time)
- El mandatory usa paso fijo por frame. Animaciones/cooldowns piden tiempo real:
  `gettimeofday` (**permitido**) para `dt` en segundos. Todos los timers en segundos.

### DA7 — Propiedad de memoria (lado A)
- `enemies[]`: A aloca al iniciar cada oleada, libera al cambiar de oleada **y** en
  `exit_game` (coordinar: `exit_game` es compartido → añadir `free(enemies)` con Rodrigo).

### DA8 — Norma / ficheros
- `sources/bonus/mod/`: `sim.c` (update_sim + dt), `waves.c`, `enemy_ai.c`, `combat.c`,
  `player_state.c`. ≤5 funcs/fichero, ≤25 líneas, ≤4 params. Estado en `t_data` (sin globals).

---

## TAREAS (cada una con su gate; detalle fino al llegar — `/plano`)

### A1 — Modelo + oleadas
Alloc/free `enemies[]`; spawn (DA1); FSM de oleadas (DA3).
**Verify (printf):** "wave 1: N enemigos"; al matar todos → "wave 2"… → tras boss "G_WIN".

### A2 — IA FSM + movimiento
FSM por enemigo + chase con `try_move` + rangos dist² (DA2).
**Verify (printf):** posiciones convergen al jugador, **paran en muros**, pasan a `E_ATTACK` a rango.

### A3 — Combate + arma
Tecla de disparo, cooldown, hitscan, daño/kill, `weapon.state` (DA4).
**Verify (printf):** "hit enemy k (hp→…)", "blocked by wall", enemigo eliminado, cooldown respetado.

### A4 — Vida del jugador + estados de juego
`player_hp`, daño por contacto, `G_OVER`/`G_WIN`, `fog` en wave 3 (DA5).
**Verify (printf):** hp baja con zombie pegado; a 0 → `G_OVER`; boss muerto → `G_WIN`; `fog=1` en wave 3.

### A5 — Integración + cierre
Cablear `update_sim` en `game_loop` (quitar stub), `free(enemies)` en `exit_game`, norminette, valgrind.
**🔄 Coordinar con Rodrigo** (toca `game_loop.c`, `exit_game.c`, `cub3d.h`). Commit.
**Verify (Linux):** `make bonus` 0 warnings; norminette limpia; `valgrind` sin fugas de `enemies[]`.

---

## FUNCIONES PERMITIDAS (verificar contra subject Cap. V / tu libft)
- `gettimeofday` (timing) — **permitido** (subject). `malloc`/`free` (enemies[]).
- **`rand()` NO permitido** → LCG propio sembrado con `gettimeofday`, o spawn determinista.
- Evitar `sqrt`: comparar **distancia²**. `cos`/`sin` solo si hace falta (ya enlazado `-lm`).
- Reusa `is_wall`/`try_move` (código propio del mandatory). Nada de `stat`/`rand`/libs externas.

## DoD (Linux, antes de marcar nada)
```bash
make bonus                                 # 0 warnings
norminette sources/ includes/              # 0 errores
# pruebas printf de A1–A4 (sim sin render) dan las transiciones esperadas
valgrind --leak-check=full --suppressions=mlx.supp ./cub3D maps/good/subject_map.cub  # enemies[] sin fugas
```

## RIESGO RESIDUAL (A)
1. **Contrato compartido** (`cub3d.h`/`game_loop.c`/`exit_game.c`): commit conjunto PRIMERO; avisar de cada toque.
2. **Sin `rand()`**: documentar el PRNG/determinismo para defensa.
3. **Regla de oro**: `update_sim` no debe tocar render. Si necesitas algo de pantalla, va por el contrato.
4. **Frame-rate**: decidir `dt` real (gettimeofday) vs paso fijo; anotarlo.

---

## ORDEN DE TRABAJO CONJUNTO (handoff verificado) — igual en ambos planes
0. **(JUNTOS)** Cerrar **Cluster 0**: commit del contrato — `cub3d.h` (structs/#defines) +
   `game_loop.c` con los 4 stubs que **compilan y corren** (esqueleto andante).
1. **(PARALELO)** A hace A1–A4 con `printf`; B hace B1–B4 con un **stub de `enemies[]`**
   (2–3 enemigos a mano) + `weapon`/`fog` falsos. Ninguno bloquea al otro.
2. **(JUNTOS)** Integración: quitar stubs, A5 + B5, probar el mod entero, valgrind, commit.

**Verificación del handoff:** el Cluster 0 es byte-idéntico en los dos planes; A valida su
mitad sin render; B valida la suya sin la lógica de A; solo se tocan a la vez en el paso 0 y el 2.
