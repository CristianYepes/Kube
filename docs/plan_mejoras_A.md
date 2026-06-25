# SPEC — Mejoras mod zombies: Persona A (lógica/simulación)

## Contexto

Tres mejoras al mod zombies DESPUÉS de que todo esté funcional:
1. **Pathfinding BFS flow field** — enemigos esquivan muros
2. **Restart del juego** — resetear estado sin relanzar el binario

Persona A se encarga de la LÓGICA: el algoritmo de pathfinding, el estado de restart,
y el hook de input. Persona B se encarga del RENDER (texto en pantalla, feedback visual).

> Norma 42: ≤25 líneas/func, ≤5 funcs/fichero, ≤4 params, ≤5 vars. Solo funciones
> permitidas (subject Cap. V). Sin `rand()`.

---

## Decisiones de diseño

- **D1 — Flow field estático:** Un `int flow[MAX_MAP][MAX_MAP]` con distancias BFS desde
  la celda del jugador. Se recalcula SOLO cuando el jugador cambia de celda o se
  abre/cierra una puerta. Los enemigos leen la celda vecina con menor distancia.
- **D2 — MAX_MAP = 64:** Cubre cualquier mapa del proyecto (< 50×50). Sin malloc por frame.
- **D3 — Restart in-place:** Guardar posición de spawn al parsear. En G_OVER/G_WIN,
  tecla R resetea todo el estado del mod sin recargar texturas ni re-parsear.
- **D4 — Spawn pos:** Almacenar `spawn_x`, `spawn_y`, `spawn_dir` en `t_data` al parsear
  (antes de sobreescribir la celda NSEW con '0').

---

## FASE A1 — BFS Flow Field (pathfinding)

### A1.1 Contrato en `cub3d.h`
```c
# define MAX_MAP 64

/* t_data: */
int    flow[MAX_MAP][MAX_MAP];
int    flow_px;
int    flow_py;
```

### A1.2 Nuevo fichero `sources/bonus/mod/flow_field.c`
```c
void    update_flow_field(t_data *data);  /* dirty check + llama bfs_init + bfs_loop */
/* static: */
static void    bfs_init(t_data *data, int *head, int *tail);  /* init -1, encola player */
static void    bfs_loop(t_data *data, int head, int tail);    /* expande cola 4-dir */
static int     cell_walkable(t_data *data, int x, int y);     /* bounds + !wall + !door */
```

Nuevo fichero `sources/bonus/mod/flow_query.c`:
```c
void    flow_dir(t_data *data, t_enemy *e, double *dx, double *dy);
                                                /* lee vecinos, devuelve vector normalizado */
```

> **Nota norma:** BFS se divide en `bfs_init` (init array + encolar origen, ~10 líneas,
> 4 vars) y `bfs_loop` (dequeue + expand 4 dirs, ~22 líneas, 5 vars: head, tail, x, y, i).
> La cola `int qx[MAX_MAP*MAX_MAP]` y `int qy[MAX_MAP*MAX_MAP]` se declaran como campos
> estáticos del fichero (file-scope `static`, no global — permitido por norma) para no
> gastar vars de función.

### A1.3 Algoritmo BFS
1. `bfs_init`: Inicializar `flow[][]` a `-1`. Encolar celda jugador con `flow[py][px] = 0`.
2. `bfs_loop`: Mientras `head < tail`, dequeue `(qx[head], qy[head])`. Para cada una de
   las 4 direcciones (dx=[1,-1,0,0], dy=[0,0,1,-1]): si `cell_walkable` y `flow == -1`,
   asignar `flow[ny][nx] = flow[cy][cx] + 1` y encolar.
3. Cola: arrays file-scope `static int g_qx[MAX_MAP * MAX_MAP]` (permitido en 42 norm
   como variable estática de fichero, no global exportado).
4. Resultado: toda celda alcanzable tiene su distancia en pasos al jugador.

> **Guard opcional (mapas > 64):** En `update_flow_field`, si `map_width >= MAX_MAP ||
> map_height >= MAX_MAP`, return sin calcular (fallback al chase directo).

### A1.4 Dirty check (cuándo recalcular)
```c
void    update_flow_field(t_data *data)
{
    int px = (int)data->player.pos_x;
    int py = (int)data->player.pos_y;
    if (px == data->flow_px && py == data->flow_py)
        return;
    data->flow_px = px;
    data->flow_py = py;
    bfs_fill(data);
}
```
Además: en `toggle_door()` forzar `data->flow_px = -1;` para invalidar.

### A1.5 Movimiento del enemigo desde el field
Reemplazar `chase_player()` en `enemy_ai.c`:
```c
/* Nuevo chase usando flow field */
static void chase_flow(t_data *data, t_enemy *e)
{
    double dx, dy, spd;

    flow_dir(data, e, &dx, &dy);
    spd = get_speed(e, data);
    dx *= spd;
    dy *= spd;
    if (!is_wall(data, e->pos_x + dx, e->pos_y))
        e->pos_x += dx;
    if (!is_wall(data, e->pos_x, e->pos_y + dy))
        e->pos_y += dy;
}
```

`flow_dir()` lee las 4 celdas vecinas a `(int)e->pos_x, (int)e->pos_y`, elige la de
menor `flow[][]` (ignorando -1), y devuelve un vector normalizado desde la posición
del enemigo hacia el centro de esa celda (`cell_x + 0.5, cell_y + 0.5`).

**Fallback:** Si todas las vecinas son -1 (enemigo en zona inalcanzable), usar el
chase directo actual como degradado.

### A1.6 Integración en game loop
En `update_sim()`, ANTES de `update_enemies()`:
```c
update_flow_field(data);
```

### Edge cases
- Enemigo en misma celda que jugador: `flow == 0`, vecinos tienen dist ≥ 1 → no se mueve
  (ya está en ATTACK por la FSM).
- Puerta abre/cierra: dirty flag fuerza recálculo.
- Cola no desborda: MAX_MAP² = 4096 entradas, mapa real < 2500 celdas.

**Gate A1:** Enemigos rodean muros para llegar al jugador en vez de atascarse. Sin crash.
Valgrind 0 fugas. Norminette 0.

---

## FASE A2 — Restart del juego

### A2.1 Guardar posición de spawn
En `cub3d.h`, añadir a `t_data`:
```c
double  spawn_x;
double  spawn_y;
char    spawn_dir;
```

En `check_map.c`, función `set_player_at()`, ANTES de sobreescribir con '0':
```c
data->spawn_x = j + 0.5;
data->spawn_y = i + 0.5;
data->spawn_dir = c;
```

### A2.2 Nuevo fichero `sources/bonus/mod/restart.c`
```c
void    restart_game(t_data *data);
/* static: */
static void    reset_player(t_data *data);    /* pos + dir + plane desde spawn_dir */
static void    reset_mod_state(t_data *data); /* wave, hp, enemies, weapon, fog */
static void    reset_map_doors(t_data *data); /* 'O' → 'D' en todo el mapa */
```

### A2.3 Qué resetea `restart_game`
| Campo | Valor |
|-------|-------|
| `player.pos_x/y` | `spawn_x/y` |
| `player.dir_x/y, plane_x/y` | Recalcular desde `spawn_dir` (reusar lógica `set_ns/set_ew`) |
| `player.key_*`, `rotate_*` | 0 |
| `wave` | 1 |
| `player_hp` | 100 |
| `game_state` | G_PLAY |
| `fog` | 0 |
| `weapon.state/timer` | W_IDLE / 0 |
| `fire` | 0 |
| `enemies` | `free()` + NULL |
| `enemy_count` | 0 |
| `last_spawn` | 0 |
| `spawn_relax` | 0 |
| `gun_frame/gun_firing/gun_timer` | 0 |
| `flow_px` | -1 (forzar recálculo) |
| Puertas en mapa | 'O' → 'D' |
| `seed` | re-seed con `gettimeofday` |

### A2.4 Hook de input
En `input_bonus.c`, función `key_press_bonus()`:
```c
# define KEY_R 114

if (keycode == KEY_R && data->game_state != G_PLAY)
    restart_game(data);
```

### A2.5 Prototipo en `cub3d.h`
```c
# define KEY_R 114
void    restart_game(t_data *data);
```

**Gate A2:** En G_OVER o G_WIN, pulsar R devuelve al jugador al spawn con hp=100,
wave 1, sin enemigos, puertas cerradas. El juego continúa normal. Sin crash/leaks.

---

## Ficheros tocados / nuevos

- **Fase A1:** `cub3d.h` (+3 campos + MAX_MAP), **+`sources/bonus/mod/flow_field.c`**,
  **+`sources/bonus/mod/flow_query.c`**, `sources/bonus/mod/enemy_ai.c` (reemplazar
  `chase_player`), `sources/bonus/mod/sim.c` (+llamada a `update_flow_field`),
  `sources/movement/doors.c` (+dirty flag), `Makefile`.
- **Fase A2:** `cub3d.h` (+3 campos spawn + KEY_R + proto), `sources/parsing/check_map.c`
  (+guardar spawn), **+`sources/bonus/mod/restart.c`**, `sources/movement/input_bonus.c`
  (+KEY_R handler), `Makefile`.

---

## Estado de avance
- [ ] Fase A1 — BFS flow field
- [ ] Fase A2 — Restart
