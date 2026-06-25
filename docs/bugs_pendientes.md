# Bugs pendientes — Auditoría adversarial 2026-06-25

## Confirmados (lógica, no crash)

### 1. FSM fall-through en `enemy_ai.c:66-74`
- **Fichero:** `sources/bonus/mod/enemy_ai.c`
- **Líneas:** 66-74
- **Problema:** Los `if` encadenados sin `else` permiten que un enemigo salte de `E_IDLE` → `E_CHASE` → `E_ATTACK` en un solo tick. Al setear `e->state = E_CHASE` (l.67), el siguiente `if (e->state == E_CHASE)` (l.68) se evalúa en el mismo frame.
- **Impacto:** Los enemigos nunca pasan un frame en IDLE; si están a dist<1.0, saltan directo a ATTACK en un tick.
- **Fix:** Cambiar los `if` posteriores a `else if` tras la mutación de state.

## Sospechosos (diseño, no crash)

### 2. Dual weapon state desincronizado
- **Ficheros:** `shotgun.c` (visual: `gun_firing/gun_timer`) vs `sim.c` (mecánico: `weapon.state/weapon.timer`)
- **Problema:** La animación visual dura 0.32s (4 frames × 0.08s) pero el cooldown mecánico dura 0.6s (`FIRE_COOLDOWN`). Hay una ventana de 0.28s donde la animación ya terminó pero el arma no puede disparar.
- **Impacto:** Feedback visual confuso — el jugador ve el arma en idle pero no puede disparar.
- **Fix posible:** Sincronizar ambos timers o usar solo `weapon.timer` para ambos.

### 3. `render_sprites()` no se llama en game_loop bonus
- **Fichero:** `sources/render/game_loop.c` (bonus path)
- **Problema:** El game_loop bonus llama a `render_enemies()` pero no a `render_sprites()`. Los sprites de mapa ('2'/'3') están alocados en memoria pero son invisibles.
- **Impacto:** Los sprites decorativos del mapa no se ven en el build bonus (solo los enemigos).
- **Fix:** Añadir `render_sprites(data);` en el game_loop bonus, después de `cast_rays` y antes de `render_enemies`.

### 4. Shotgun/crosshair se renderizan en G_OVER/G_WIN
- **Ficheros:** `game_loop.c:34-35`, `shotgun_draw.c`
- **Problema:** `tick_shotgun` y `draw_shotgun` se llaman sin comprobar `game_state`. El arma y la cruz se dibujan incluso en pantalla de muerte/victoria (quedan debajo del rectángulo HUD).
- **Impacto:** Visual menor. El jugador no lo nota porque el HUD lo tapa.
- **Fix opcional:** Envolver en `if (data->game_state == G_PLAY)`.

### 5. `has_los` — división por 0 teórica
- **Fichero:** `sources/bonus/mod/utils.c:29-31`
- **Problema:** Si `d == 0` (posición del enemigo == posición del jugador), se divide `dx/d` y `dy/d` → NaN/inf.
- **Impacto:** Inalcanzable en la práctica (spawn cells están a >2.0 de distancia), pero no defensivo.
- **Fix opcional:** `if (d < 0.01) return (1);` al principio.

## Checks que pasan limpio

- `norminette sources/ includes/`: 0 errores (44 ficheros)
- `grep -rn "\babs\b" sources/`: 0 hits
- Funciones prohibidas (sprintf/snprintf/strdup/memset/atoi/bzero/stat/rand/getenv): 0
- Validación F/C en parser: implementada
- Math functions: solo `fabs`, `sqrt`, `sin`, `cos`, `floor` (todas permitidas)
