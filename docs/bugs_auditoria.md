# Bugs — Auditoría adversarial (2026-06-26)

Resultado de la auditoría de contexto con postura adversarial. Todos pendientes de
implementar. Prioridad: B1 > S3 > S1 > B2 > S2/S4/S5 (informativo).

---

## CONFIRMADOS

### B1 — `has_los` divide por cero si dist == 0

**Fichero:** `sources/bonus/mod/utils.c:29-30`
**Input:** Enemigo exactamente en la misma posición que el jugador (dist ≈ 0).
**Qué pasa:** `d = sqrt(0) = 0` → `dx = dx/0 = NaN`, `dy = dy/0 = NaN`. El while
no itera, retorna 1 (tiene LOS). No crashea pero produce NaN en el step.
**Fix:** Guard `if (d < 0.01) return (1);` antes de normalizar.
**Impacto:** Bajo — en la práctica `enemy_can_hit` ya filtra dist > 1.0, pero el
NaN es UB técnico.

### B2 — BFS dirty check falla en primer frame / tras restart

**Fichero:** `sources/bonus/mod/flow_field.c:82-83`
**Input:** Jugador spawna en celda (0, Y) o tras restart `flow_px`/`flow_py` = 0.
**Qué pasa:** `flow_px` se inicializa a 0. Si el jugador está en x=0 (o la celda
coincide con el valor por defecto), la condición `px == flow_px && py == flow_py`
pasa → BFS no se ejecuta → `flow[]` queda todo -1 → enemigos usan fallback directo.
**Fix:** Inicializar `flow_px = -1` y `flow_py = -1` (valor imposible) para forzar
el primer cálculo. También en `restart.c` al resetear.
**Impacto:** Medio — pathfinding BFS desaprovechado en ciertos spawns.

---

## SOSPECHOSOS

### S1 — `place_enemy` sobreescribe sprites decorativos

**Fichero:** `sources/bonus/mod/waves.c:34`
**Input:** Mapa pequeño donde las celdas '2'/'3' son las únicas '0' disponibles para
spawn (poco probable pero posible).
**Qué pasa:** `map[y][x] = 'Z'` marca la celda; `clear_spawn_marks` la pone en '0'.
Si la celda original era '2' o '3', el sprite decorativo desaparece para siempre.
**Fix:** `is_valid_spawn` debería rechazar celdas que no sean exactamente '0'.
**Impacto:** Bajo — solo si el mapa tiene muy pocas celdas libres.

### S2 — Filtro `E_DEAD` en `find_target` es código muerto

**Fichero:** `sources/bonus/mod/combat.c:56`
**Input:** Cualquiera.
**Qué pasa:** `kill_enemy` usa swap-remove del array; nadie pone `E_DEAD` porque el
enemigo se borra directamente. El check `E_DEAD` nunca se satisface.
**Fix:** Borrar el check o dejar como guard defensivo. No es un bug funcional.
**Impacto:** Nulo.

### S3 — G_WIN inalcanzable si wave 3 no puede spawnear

**Fichero:** `sources/bonus/mod/player_state.c:55`
**Input:** Mapa tan pequeño que `spawn_wave` en wave 3 no encuentra celdas → `placed=0`
→ `last_spawn=0` → condición `last_spawn > 0` nunca se cumple → game loop atrapado.
**Fix:** Tratar `enemy_count == 0 && wave == 3 && last_spawn == 0` como G_WIN también,
o garantizar al menos 1 spawn con spawn_relax forzado.
**Impacto:** Medio en mapas tiny — el jugador nunca puede ganar.

### S4 — Bitmap font solo soporta 13 caracteres

**Fichero:** `sources/bonus/render/font.c:38`
**Input:** Cualquier texto con letra fuera de `"YOUWINLSEPRTA"`.
**Qué pasa:** `glyph_rows` retorna NULL → carácter invisible (no crash).
**Fix:** No necesario ahora — el HUD solo usa esas letras. Pero si se añade texto
nuevo hay que ampliar el charset.
**Impacto:** Nulo con el código actual.

### S5 — Double-tap R: `free(NULL)` en restart

**Fichero:** `sources/bonus/mod/restart.c:45`
**Input:** Pulsar R dos veces muy rápido.
**Qué pasa:** `free(NULL)` es safe según C99. No bug real.
**Fix:** Ninguno necesario.
**Impacto:** Nulo.

---

## NOTA

Los docs `Espec_mejoras_desfasadoB.md` y `plan_entrega_desfasadol.md` están obsoletos
(el nombre lo indica). No afectan al código pero ensucian el repo para evaluación.
