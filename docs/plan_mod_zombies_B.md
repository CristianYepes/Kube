# MOD Zombies — Plan B (presentación / render) — Persona B (Rodrigo)

> Cubre `render_enemies`, `render_weapon`, `render_hud` y la niebla. **Los ojos del mod.**
> Lee el estado que produce A; **nunca lo muta**. Se prueba con un stub de `enemies[]`.
> Pareja: `docs/plan_mod_zombies_A.md` (simulación / lógica — Cristian).
> **Prerequisitos:** (1) bonus oficial de B cerrado (ratón S10B + **sprites animados S12B**,
> cuya infra se REUSA aquí); (2) **Cluster 0 (contrato) commiteado JUNTO con A** antes de B1.

---

## DÓNDE ENCAJA (leer primero)

- **No puntúa.** 42 evalúa mandatory + 5 bonus oficiales. Esto es portfolio/gusto y va
  DESPUÉS del bonus oficial. El render de enemigos **reusa tu infra de sprites (S12B)**.
- **Build:** compila bajo `make bonus` (`-DBONUS`), ficheros en `sources/bonus/`.
- **Método (`/plano`):** capa estable (Cluster 0) entera y por adelantado y JUNTOS; luego
  cada cluster crece al llegar. Aquí van objetivo, tareas y **gate de verificación** de cada uno.
- **Eficiencia (lo tuyo):** frames precargados (como las texturas de muro) e índice por estado;
  sprites con z-buffer; disparo por animación + hitscan (lo hace A), no proyectiles.

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

## DECISIONES DE DISEÑO (lado B)

### DB1 — Sprites de enemigos (billboard + z-buffer)
- Reusa la infra de **S12B**: transformar la posición del enemigo con la inversa de la
  matriz `[plane | dir]`, proyectar a columna/altura, dibujar columna a columna **comparando
  con el z-buffer** (de `cast_rays`) para que el muro tape al sprite.
- **Ordenar enemigos por distancia² (descendente)** antes de dibujar (pintar lejanos primero).
- ⚠️ Requiere que `cast_rays` **guarde `wall_dist` por columna** en un z-buffer (si S12B ya lo
  hace, reusar; si no, añadirlo en B1).

### DB2 — Animación de enemigos
- Frames **precargados** (como las texturas de muro), índice elegido por `(type, state)` +
  un **timer propio de B** sincronizado con las constantes compartidas (`DEATH_TIME`…).
- Cero carga por frame (eficiente). `E_DEAD`: reproduce la anim. de muerte durante `DEATH_TIME`
  (A quita el enemigo al expirar ese mismo tiempo → quedan sincronizados por la constante).

### DB3 — Escopeta (overlay + disparo)
- Sprite del arma a **posición fija** en pantalla (overlay tras el render del mundo).
- `W_IDLE` → frame base; `W_FIRING` → reproduce frames de disparo según el tiempo transcurrido
  dentro de `FIRE_COOLDOWN`. **No mutar `weapon.state`** (lo hace A); B solo lee y dibuja.
- La textura del arma lleva el detalle **"-42"**.

### DB4 — Niebla + HUD
- **Niebla** (cuando `data->fog == 1`): oscurecer el color por distancia — muros con
  `wall_dist`, sprites con su distancia — mezclando hacia negro/techo (shift o lerp barato).
- **HUD mínimo:** barra/numero de vida + oleada, dibujados con `put_pixel` o un mini-bitmap
  propio (sin texto de libc; no está permitido).

### DB5 — Texturas y memoria (lado B)
- Cargar `enemy_tex[]`/`weapon_tex[]` estilo `init_textures` (reusar `xpm_to_int`, que **ya
  valida tamaño 64×64** tras el fix de hoy). Liberar en `exit_game` (coordinar: compartido).

### DB6 — Norma / ficheros
- `sources/bonus/render/`: `enemy_render.c`, `enemy_sprite.c` (proyección), `weapon.c`,
  `fog.c`, `hud.c`. ≤5 funcs/fichero, ≤25 líneas, ≤4 params.

---

## TAREAS (cada una con su gate; detalle fino al llegar — `/plano`)

### B1 — Render de sprites de enemigos
Billboard + z-buffer + orden por distancia² (DB1), leyendo `enemies[]`.
**Verify (visual, stub):** 2–3 enemigos del stub aparecen en su sitio y **quedan tapados** por los muros.

### B2 — Animación de enemigos
Frames por `(type, state)` + timer propio (DB2).
**Verify (visual):** animación de caminar visible; `E_DEAD` dura `DEATH_TIME`.

### B3 — Escopeta (overlay + disparo)
Overlay fijo; `W_FIRING` reproduce animación; textura con "-42" (DB3).
**Verify (visual):** arma siempre visible; con `weapon.state=W_FIRING` (stub) reproduce el disparo.

### B4 — Niebla + HUD
Oscurecido por distancia con `fog=1`; HUD de vida/oleada (DB4).
**Verify (visual):** con `fog=1` (stub) la escena oscurece con la distancia; el HUD muestra vida/oleada.

### B5 — Integración + cierre
Cablear `render_enemies/weapon/hud` en `game_loop` (quitar stubs), carga/free de texturas, norminette, valgrind.
**🔄 Coordinar con Cristian** (toca `game_loop.c`, `exit_game.c`, `cub3d.h`). Commit.
**Verify (Linux):** `make bonus` 0 warnings; norminette limpia; `valgrind` sin fugas de texturas (liberadas en exit).

---

## FUNCIONES PERMITIDAS (verificar contra subject Cap. V)
- MLX (`mlx_put_image_to_window`, `put_pixel`, `mlx_xpm_file_to_image`…) — permitido.
- `gettimeofday` (timer de animación) — permitido. Math (`-lm`) para la proyección si hace falta.
- Reusa el z-buffer y la infra de sprites de **S12B**. `xpm_to_int` ya valida 64×64.
- Nada de texto de libc para el HUD (dibujarlo a mano). Nada de libs externas.

## DoD (Linux, antes de marcar nada)
```bash
make bonus                                 # 0 warnings
norminette sources/ includes/              # 0 errores
# con el stub de enemies[]/weapon/fog: sprites, animación, arma, niebla y HUD se ven bien
valgrind --leak-check=full --suppressions=mlx.supp ./cub3D maps/good/subject_map.cub  # texturas liberadas
```

## RIESGO RESIDUAL (B)
1. **Depende de S12B** (infra de sprites + z-buffer). Si el z-buffer no existe aún, lo añade B1.
2. **Contrato compartido** (`cub3d.h`/`game_loop.c`/`exit_game.c`): commit conjunto PRIMERO; avisar de cada toque.
3. **Regla de oro**: B solo LEE el estado; nunca muta `enemies/weapon/...`.
4. **Rendimiento**: sprites + niebla a 1280×720 por software; medir y optimizar solo si hace falta.

---

## ORDEN DE TRABAJO CONJUNTO (handoff verificado) — igual en ambos planes
0. **(JUNTOS)** Cerrar **Cluster 0**: commit del contrato — `cub3d.h` (structs/#defines) +
   `game_loop.c` con los 4 stubs que **compilan y corren** (esqueleto andante).
1. **(PARALELO)** A hace A1–A4 con `printf`; B hace B1–B4 con un **stub de `enemies[]`**
   (2–3 enemigos a mano) + `weapon`/`fog` falsos. Ninguno bloquea al otro.
2. **(JUNTOS)** Integración: quitar stubs, A5 + B5, probar el mod entero, valgrind, commit.

**Verificación del handoff:** el Cluster 0 es byte-idéntico en los dos planes; B valida su
mitad con stubs sin la lógica de A; A valida la suya sin render; solo se tocan a la vez en el paso 0 y el 2.
