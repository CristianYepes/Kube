# Bugs — Auditoria adversarial (2026-06-27)

Resultado de las auditorias de Cristian (A) y Rodrigo (B), actualizado con revision
adversarial post-merge. Prioridad: B4 > B5 > B1 > B2 > B2R > B3 > S3 > S7 > S8 > resto.

---

## CONFIRMADOS

### B1 — `has_los` divide por cero si dist == 0

**Fichero:** `sources/bonus/mod/utils.c:29-30`
**Input:** Enemigo exactamente en la misma posicion que el jugador (dist = 0).
**Que pasa:** `d = sqrt(0) = 0` -> `dx = dx/0 = NaN`, `dy = dy/0 = NaN`. El while
no itera, retorna 1 (tiene LOS). No crashea pero produce NaN en el step.
**Fix:** Guard `if (d < 0.01) return (1);` antes de normalizar.
**Impacto:** Bajo — en la practica `enemy_can_hit` ya filtra dist > 1.0, pero el
NaN es UB tecnico.
**Estado:** SIN FIX en codigo.

### B2 — BFS dirty check falla si jugador en celda py==0

**Fichero:** `sources/bonus/mod/flow_field.c:82-83`
**Input:** Jugador spawna en fila y=0 (o cualquier celda donde py==0).
**Que pasa:** `flow_px` se inicializa a -1 (init_game.c:46), PERO `flow_py` NO se
inicializa a -1 — queda en 0 (del `(t_data){0}` en main.c:19). Si el jugador esta
en py==0, la condicion `px == flow_px && py == flow_py` puede pasar en el caso
`flow_px` ya se actualizo pero `flow_py` coincide con 0.
**Fix:** Anadir `data->flow_py = -1;` en `init_mod_state` (init_game.c:46).
**Impacto:** Medio — pathfinding BFS desaprovechado en spawns de fila 0.
**Estado:** FIX PARCIAL (solo `flow_px`, falta `flow_py`).

### B2R — BFS stale tras restart (NUEVO)

**Fichero:** `sources/bonus/mod/restart.c` (funcion `reset_mod_state`)
**Input:** Jugador gana/pierde, pulsa R para restart.
**Que pasa:** `restart_game` no resetea `flow_px`/`flow_py` a -1. Tras restart el
jugador vuelve al spawn. Si el spawn esta en la misma celda que el ultimo
`flow_px`/`flow_py` del round anterior, la condicion dirty-check pasa y BFS no se
recalcula. `flow[]` queda con el mapa de distancias del round anterior (enemigos
ya muertos) — los nuevos enemigos usan un flow field obsoleto hasta que el jugador
se mueva a otra celda.
**Fix:** Anadir `data->flow_px = -1; data->flow_py = -1;` en `reset_mod_state`.
**Impacto:** Medio — pathfinding incorrecto durante el primer frame(s) tras restart.

### B3 — `(int)(inf)` en proyeccion de sprites

**Fichero:** `sources/render/render_sprites.c:76-80`, `sources/bonus/render/enemy_render.c:29-31`
**Input:** Sprite/enemigo exactamente en el plano de la camara (transform_y == 0).
**Que pasa:** `screen_x = (int)((WIN_W/2) * (1 + transform_x / 0))` = UB.
El guard `> 0.1` previene el draw pero la proyeccion (lineas 76-80) ya ocurrio.
**Fix:** Guard `if (transform_y < 0.001)` ANTES de calcular screen_x/size (o skip
la iteracion entera con `continue`).
**Impacto:** Bajo — transform_y == 0 es extremadamente raro en gameplay real.
**Estado:** SIN FIX en codigo.

### B4 — Enemigos atraviesan muros con lag spike (NUEVO)

**Fichero:** `sources/bonus/mod/enemy_ai.c:58-59`
**Input:** dt >= 1.12 segundos (lag spike por focus loss, carga del sistema, suspend).
**Que pasa:** `get_speed` retorna `base * dt * 60 = 0.015 * 1.12 * 60 = 1.008` (> 1
celda). dx/dy son vectores unitarios, asi que tras multiplicar el step supera 1.0.
`is_wall` solo comprueba la celda destino (pos_x + dx), no las intermedias. El enemigo
salta de celda 3 a celda 5, atravesando un muro en celda 4.
**Fix:** Clamp dt en tick_clock: `if (data->dt > 0.05) data->dt = 0.05;`
**Impacto:** Medio-alto — enemigos traspasan muros o quedan atascados permanentemente.
**Estado:** SIN FIX en codigo.

### B5 — FSM deadlock: enemigo congelado entre ATTACK y CHASE (NUEVO)

**Fichero:** `sources/bonus/mod/enemy_ai.c:64-83` + `sources/bonus/mod/player_state.c:22`
**Input:** Jugador a distancia entre 1.0 y 1.414 unidades del enemigo (dist_sq entre
1.0 y 2.0). Se dispara al retroceder ligeramente tras entrar en rango de ataque.
**Que pasa:** (1) Enemigo entra en E_ATTACK cuando dist_sq < 1.0 (linea 76).
(2) Jugador retrocede a dist_sq = 1.5. (3) enemy_fsm rama E_ATTACK: comprueba
`d > 2.0` para volver a E_CHASE — FALSE (1.5 < 2.0), se queda en E_ATTACK.
(4) `chase_player` solo se llama en E_CHASE — enemigo no se mueve. (5) `enemy_can_hit`
comprueba `dist_sq > 1.0` — TRUE, retorna 0 — no hace dano. (6) Resultado: enemigo
CONGELADO, ni se mueve ni ataca. Exploitable por el jugador.
**Fix:** Cambiar umbral linea 81 de `d > 2.0` a `d > 1.0` (match con el hit range),
o llamar `chase_player` tambien en E_ATTACK cuando `enemy_can_hit` falla.
**Impacto:** Medio — distancia segura explotable, enemigos parecen rotos al evaluador.
**Estado:** SIN FIX en codigo.

---

## SOSPECHOSOS

### S1 — `place_enemy` sobreescribe sprites decorativos

**Fichero:** `sources/bonus/mod/waves.c:34`
**Input:** Mapa donde las celdas '2'/'3' son las unicas '0' disponibles para spawn.
**Que pasa:** `is_valid_spawn` filtra `map[y][x] != '0'` (utils.c:52), asi que
celdas con '2' o '3' NO se eligen para spawn. **Realmente safe.**
**Impacto:** Nulo — `is_valid_spawn` ya rechaza celdas != '0'.
**Veredicto:** FALSO POSITIVO (descartar).

### S2 — Filtro `E_DEAD` en `find_target` es codigo muerto

**Fichero:** `sources/bonus/mod/combat.c:55`
**Input:** Cualquiera.
**Que pasa:** `kill_enemy` usa swap-remove del array; nadie pone `E_DEAD` porque el
enemigo se borra directamente. El check `E_DEAD` nunca se satisface.
**Fix:** Borrar el check o dejar como guard defensivo. No es un bug funcional.
**Impacto:** Nulo.

### S3 — G_WIN inalcanzable si wave 3 no puede spawnear

**Fichero:** `sources/bonus/mod/player_state.c:55`
**Input:** Mapa tan pequeno que `spawn_wave` en wave 3 no encuentra celdas -> `placed=0`
-> `last_spawn=0` -> condicion `last_spawn > 0` nunca se cumple -> game loop atrapado.
**Fix:** Tratar `enemy_count == 0 && wave == 3 && last_spawn == 0` como G_WIN tambien,
o garantizar al menos 1 spawn con spawn_relax forzado.
**Impacto:** Medio en mapas tiny — el jugador nunca puede ganar.

### S4 — Bitmap font solo soporta 13 caracteres

**Fichero:** `sources/bonus/render/font.c:38`
**Input:** Texto con letra fuera de `"YOUWINLSEPRTA"`.
**Que pasa:** `glyph_rows` retorna NULL -> caracter invisible (no crash).
**Fix:** No necesario — el HUD solo usa esas letras.
**Impacto:** Nulo con el codigo actual.

### S5 — Double-tap R: `free(NULL)` en restart

**Fichero:** `sources/bonus/mod/restart.c:45`
**Input:** Pulsar R dos veces muy rapido.
**Que pasa:** `free(NULL)` es safe segun C99. No bug real.
**Fix:** Ninguno necesario.
**Impacto:** Nulo.

### S6 — Enemigo en celda inalcanzable ignora pathfinding

**Fichero:** `sources/bonus/mod/flow_query.c:31`
**Input:** Enemigo en celda con flow=-1 (inalcanzable por BFS).
**Que pasa:** `best_neighbor` devuelve la misma celda, `flow_dir` retorna dx=dy=0,
fallback a persecucion directa en `enemy_ai.c:44-54`. No crashea pero enemigo puede
quedar atascado si hay muros entre el y el jugador.
**Fix:** Aceptable (fallback directo funciona con wall collision).
**Impacto:** Bajo.

### S7 — Sprites decorativos escriben en z_buffer (NUEVO)

**Fichero:** `sources/render/render_sprites.c:56`
**Input:** Sprite decorativo ('2') mas cerca del jugador que un enemigo.
**Que pasa:** `draw_sprite_3d` hace `data->z_buffer[x] = s->transform_y` tras dibujar
cada columna del sprite decorativo. Luego en `render_enemies` (llamado DESPUES de
`render_sprites` en game_loop.c:38-39), el check `s->transform_y < data->z_buffer[x]`
falla para enemigos que estan detras del sprite decorativo. El enemigo queda OCULTO
por la decoracion — correcto visualmente (occlusion). PERO: si el sprite decorativo
tiene pixeles transparentes (color == 0 → no se dibuja), el z_buffer ya se escribio
y el enemigo tampoco se dibuja en esas columnas aunque el pixel del sprite era
transparente.
**Fix:** Solo escribir z_buffer cuando el pixel se dibuja (mover la asignacion dentro
del `if (color != 0)`). O no escribir z_buffer en sprites decorativos (quitar L56).
**Impacto:** Bajo-medio visual — enemigos pueden parpadear/desaparecer parcialmente
detras de sprites decorativos transparentes.

### S8 — anim_clock negativo causa OOB en sprite_tex (NUEVO)

**Fichero:** `sources/bonus/render/enemy_render.c:111-112`
**Input:** Reloj del sistema retrocede (NTP adjustment o settimeofday manual) durante
el juego, produciendo dt negativo acumulado que empuja anim_clock por debajo de -0.25.
**Que pasa:** (1) tick_clock produce dt negativo (tiempo retrocede).
(2) `anim_clock += dt_negativo` -> anim_clock = -0.3. (3) `f[0] = (int)(-0.3 * 4) % 2`
= `(int)(-1.2) % 2` = `-1 % 2` = -1 (C99: resultado tiene signo del dividendo).
(4) `data->sprite_tex[-1]` -> lectura antes del inicio del array -> UB/segfault.
**Fix:** En tick_clock: `if (data->dt < 0) data->dt = 0;` O usar modulo unsigned:
`f[0] = ((int)(data->anim_clock * 4) % 2 + 2) % 2;`
**Impacto:** Bajo — requiere ajuste NTP backward durante gameplay (muy improbable en eval).

---

## NORMA / LIMPIEZA

### N1 — `project_sprite` no es static (render_sprites.c:62)
- Solo se usa dentro del mismo archivo. Debe ser `static`.

### N3 — Docs obsoletos en `docs/`
- `Espec_mejoras_desfasadoB.md` y `plan_entrega_desfasadol.md` estan desfasados.
  No afectan al codigo pero ensucian el repo.
