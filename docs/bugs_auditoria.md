# Bugs encontrados — Auditoría adversarial (2026-06-26)

## UB confirmados

### 1. Division by zero en `has_los` (utils.c:30)
- **Trigger:** enemigo exactamente en posición del jugador (d=0)
- **Efecto:** `0.0/0.0` → NaN. Loop no entra, retorna 1. Benigno en x86 pero UB.
- **Fix:** `if (d < 0.001) return (1);` antes de la division.

### 2. `(int)(inf)` en proyección de sprites (render_sprites.c:78, enemy_render.c:29)
- **Trigger:** sprite/enemigo exactamente en el plano de la cámara (transform_y == 0)
- **Efecto:** `screen_x = (int)(inf)` es UB. El guard `> 0.1` previene el draw pero la proyección ya ocurrió.
- **Fix:** guard `if (transform_y < 0.001) return;` antes de calcular screen_x/size.

## Lógica

### 3. Juego atascado si wave 3 no puede spawnear (sim.c:49 + player_state.c:55)
- **Trigger:** mapa con pocas celdas libres, todas bloqueadas al spawnear wave 3.
- **Efecto:** `last_spawn=0` → condición de victoria (`wave==3 && enemy_count==0 && last_spawn>0`) nunca se cumple. Juego queda en G_PLAY sin enemigos.
- **Fix:** detectar `placed==0` en spawn_wave y forzar G_WIN o reintentar.

### 4. Enemigo en celda inalcanzable ignora pathfinding (flow_query.c:31)
- **Trigger:** enemigo en celda con flow=-1 (inalcanzable por BFS).
- **Efecto:** `best_neighbor` devuelve la misma celda, `flow_dir` retorna dx=dy=0, fallback a persecución directa. No crashea pero enemigo puede quedar atascado.
- **Fix:** aceptable (fallback directo funciona con wall collision).

## Norma / limpieza

### 5. `project_sprite` no es static (render_sprites.c:62)
- Solo se usa dentro del mismo archivo. Debe ser `static`.

### 6. Archivo duplicado: `sources/bonus/mod/flow_field copy.c`
- Copia exacta de flow_field.c. Borrar.
