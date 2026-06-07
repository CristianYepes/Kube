# Plan: Integracion rama raycasting (Rodrigo) en el proyecto

> Fecha: 2026-06-07
> Objetivo: migrar el codigo funcional de Rodrigo a la estructura del proyecto,
> adaptandolo a norminette, cub3d.h, Makefile, y libft.

---

## Contexto

Rodrigo (Persona B) tiene raycasting funcional en rama `origin/raycasting` (commit 60257df).
Su codigo no compila por un path roto de MLX, no pasa norminette (~200 errores),
usa bool/stdbool.h, no usa libft, y tiene funciones de 70+ lineas.

La logica de DDA raycasting, movimiento, y renderizado es correcta y rescatable.

---

## Estrategia

Crear rama `refactor/rodrigo-integration` desde `fase1_error`.
Migrar pieza a pieza, adaptando a nuestra estructura.
Tu header, tu Makefile, tu struct `t_data` son la base.

---

## Cluster 1 — Preparar la base

| # | Tarea | Estado |
|---|---|---|
| 1.1 | Crear rama `refactor/rodrigo-integration` desde `fase1_error` | |
| 1.2 | Decidir structs: integrar `t_player` + campos render en `t_data` | |

---

## Cluster 2 — Migrar ficheros (mover + reformatear norminette)

| # | Tarea | Origen -> Destino | Estado |
|---|---|---|---|
| 2.1 | Render utils | `renderization.c` -> `sources/render/render_utils.c` | |
| 2.2 | Raycasting | `raycast.c` -> `sources/render/raycasting.c` | |
| 2.3 | Player/input | `player.c` -> `sources/movement/player.c` | |
| 2.4 | Game loop + init | `loop.c` -> `sources/init/init_game.c` + `sources/render/game_loop.c` | |

Cada fichero:
- Tabs en vez de espacios
- Max 25 lineas por funcion
- Max 4 parametros por funcion
- Max 5 variables por funcion
- Sin ternarios, sin for, sin bool
- Declaraciones separadas de asignaciones

---

## Cluster 3 — Integrar con nuestro codigo

| # | Tarea | Estado |
|---|---|---|
| 3.1 | Fusionar `t_cub3d` + `t_player` dentro de `t_data` en `cub3d.h` | |
| 3.2 | Cambiar `#include "cubed.h"` -> `#include "cub3d.h"` | |
| 3.3 | Cambiar `"mlx/mlx.h"` -> `"mlx.h"` (Makefile ya tiene -I) | |
| 3.4 | Sustituir `bool` -> `int` (0/1) | |
| 3.5 | Anadir .c nuevos al Makefile | |
| 3.6 | Compilar con -Wall -Wextra -Werror, arreglar warnings | |

---

## Cluster 4 — Verificar

| # | Tarea | Estado |
|---|---|---|
| 4.1 | `make re` sin warnings | |
| 4.2 | `norminette sources/ includes/` -> 0 errores | |
| 4.3 | Ventana se abre, raycasting funciona (mapa temporal hardcodeado) | |
| 4.4 | Parser sigue funcionando (tests de S03A) | |

---

## Cluster 5 — Merge

| # | Tarea | Estado |
|---|---|---|
| 5.1 | Merge `refactor/rodrigo-integration` -> `dev` | |
| 5.2 | Push `dev` | |

---

## Lo que NO se toca (queda para despues)

- Texturas en muros (S07B)
- Colisiones con muros (S08A)
- ESC para cerrar (S07A)
- Conectar parser real con mapa del render (S05A + SYNC3)
- Suelo/techo con color del .cub (S04B — depende de S04A)

---

## Relacion con cronograma (Persona B)

Segun cronograma, Rodrigo deberia haber hecho:
- S01B: Makefile profesional -> NO HECHO (su Makefile es minimo)
- S02B: init_data + init_mlx (ventana negra) -> PARCIALMENTE (tiene init pero no sigue estructura)
- S03B: init_textures (XPM -> buffer) -> NO HECHO
- S04B: draw_floor_ceil -> NO HECHO

Lo que SI tiene que no estaba en su cronograma aun:
- Raycasting DDA (era S05B-S06B)
- Input/movimiento (era S07A-S08A, y ademas es de Persona A)

Rodrigo se adelanto al raycasting sin hacer la base. Esta refactorizacion
nos pone al dia reusando su logica dentro de la estructura correcta.

---

## Estado actual (2026-06-07)

### Completado
- Cluster 1: rama creada, structs integradas (t_player, t_img, t_ray en cub3d.h)
- Cluster 2: todos los ficheros migrados y reformateados (norminette clean)
- Cluster 3: integrado con nuestro codigo (cub3d.h, Makefile, main.c)
- Cluster 4: compila, norminette OK, ventana se abre, raycasting funciona, parser OK

### Bugs conocidos (esperados, NO bloquean merge)
- Core dump al salir del mapa (sin colisiones) -> se arregla en S08A
- Movimiento "raro" (jugador puede atravesar muros) -> se arregla en S08A
- Posicion de inicio arbitraria (centro ventana) -> se arregla en S05A (parser da posicion del jugador)
- Mapa hardcodeado en init_game.c (get_temp_map) -> se sustituye cuando parser construya grid (S05A)
- Velocidad sin ajustar -> se calibra tras colisiones (S08A)
- No hay suelo/techo coloreado -> S04B (depende de S04A)
- No hay texturas en muros (solo color blanco plano) -> S07B

### Pendiente
- Cluster 5: merge a dev + push
- Quitar get_temp_map() cuando el parser provea el mapa real
