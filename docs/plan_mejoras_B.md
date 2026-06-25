# SPEC — Mejoras mod zombies: Persona B (render/presentación)

## Contexto

Tres mejoras al mod zombies DESPUÉS de que todo esté funcional:
1. **Pathfinding BFS flow field** — enemigos esquivan muros (Persona A hace la lógica)
2. **Texto "YOU WIN" / "YOU LOSE" en pantalla** — feedback visual claro al terminar
3. **Feedback visual de restart** — que el jugador sepa que puede pulsar R

Persona B se encarga del RENDER: texto en pantalla de fin, indicación visual de restart,
y cualquier ajuste visual que acompañe al nuevo pathfinding (nada, los enemigos simplemente
se mueven mejor). Persona A se encarga de la lógica (flow field + estado de restart).

> Norma 42: ≤25 líneas/func, ≤5 funcs/fichero, ≤4 params, ≤5 vars. Solo funciones
> permitidas (subject Cap. V).

---

## Decisiones de diseño

- **D1 — `mlx_string_put` para texto:** La función de MiniLibX dibuja texto directamente
  sobre la ventana (NO en el buffer de imagen). Se llama DESPUÉS de `mlx_put_image_to_window`
  cada frame. No hay flicker porque el game_loop redibuja cada frame en secuencia
  (blit imagen → texto encima → siguiente frame).
- **D2 — Rectángulo de contraste debajo:** El `draw_game_over()` actual (rectángulo
  rojo/verde) se mantiene como fondo de contraste para el texto.
- **D3 — Sin bitmap font propio:** `mlx_string_put` usa la fuente X11 del sistema. Es
  pequeña pero funcional. No merece la pena implementar un motor de texto bitmap para
  dos strings.
- **D4 — Indicación de restart:** Debajo del texto principal, un segundo `mlx_string_put`
  con "Press R to restart" en blanco.

---

## FASE B1 — Texto de fin de partida ("YOU WIN" / "YOU LOSE")

### B1.1 Dónde va el código
En `sources/render/game_loop.c`, función `game_loop()` (bloque `#ifdef BONUS`),
DESPUÉS de la línea `mlx_put_image_to_window(...)`:

```c
if (data->game_state == G_OVER)
{
    mlx_string_put(data->mlx, data->win,
        WIN_W / 2 - 36, WIN_H / 2 - 5, 0xFF4444, "YOU LOSE");
    mlx_string_put(data->mlx, data->win,
        WIN_W / 2 - 52, WIN_H / 2 + 20, 0xFFFFFF, "Press R to restart");
}
else if (data->game_state == G_WIN)
{
    mlx_string_put(data->mlx, data->win,
        WIN_W / 2 - 30, WIN_H / 2 - 5, 0x44FF44, "YOU WIN");
    mlx_string_put(data->mlx, data->win,
        WIN_W / 2 - 52, WIN_H / 2 + 20, 0xFFFFFF, "Press R to restart");
}
```

### B1.2 Norma — ajuste de líneas
El `game_loop` bonus actual tiene ~23 líneas. Añadir el bloque de texto directamente
excedería 25. **Solución:** Extraer a función helper (static en `game_loop.c`):

```c
static void    draw_endscreen(t_data *data);  /* mlx_string_put para G_OVER/G_WIN */
```

En `game_loop.c`, después del `mlx_put_image_to_window`:
```c
if (data->game_state != G_PLAY)
    draw_endscreen(data);
```

### B1.3 Función `draw_endscreen`
```c
static void    draw_endscreen(t_data *data)
{
    int    cx;
    int    cy;

    cx = WIN_W / 2;
    cy = WIN_H / 2;
    if (data->game_state == G_OVER)
        mlx_string_put(data->mlx, data->win,
            cx - 36, cy - 5, 0xFF4444, "YOU LOSE");
    else
        mlx_string_put(data->mlx, data->win,
            cx - 30, cy - 5, 0x44FF44, "YOU WIN");
    mlx_string_put(data->mlx, data->win,
        cx - 52, cy + 20, 0xFFFFFF, "Press R to restart");
}
```

### B1.4 Fondo de contraste
El `draw_game_over()` actual en `hud.c` YA dibuja un rectángulo de color en el buffer
de imagen (200×40px). Se mantiene tal cual — sirve de fondo para que el texto sea legible.
Opcionalmente agrandar a 200×60 para cubrir la línea de "Press R".

**Gate B1:** Al morir, aparece "YOU LOSE" en rojo sobre fondo rojo oscuro + "Press R to
restart" en blanco. Al ganar, "YOU WIN" en verde + mismo mensaje. Sin flicker. Norma OK.

---

## FASE B2 — Ajustes visuales opcionales

### B2.1 Agrandar rectángulo de contraste
En `hud.c`, `draw_game_over()`:
- Cambiar altura de 40px a 60px: `y < WIN_H / 2 + 30` (en vez de +20).
- Oscurecer el color del fondo para más contraste: usar `0x440000` (rojo oscuro) y
  `0x004400` (verde oscuro) en vez de rojo/verde puros.

### B2.2 Ocultar escopeta/crosshair/weapon en fin de partida
El `game_loop` bonus actual tiene ~23 líneas. Para no exceder 25 al añadir los guards,
meter `tick_shotgun`, `draw_shotgun` y `render_weapon` DENTRO del bloque `G_PLAY` que ya
existe (líneas 26-30):

```c
if (data->game_state == G_PLAY)
{
    move_player(data);
    update_sim(data);
    tick_shotgun(data, data->dt);
}
```
Y mover `draw_shotgun` + `render_weapon` al mismo condicional o a uno nuevo justo después:
```c
if (data->game_state == G_PLAY)
{
    draw_shotgun(data);
    render_weapon(data);
}
```

> **Nota norma:** Esto REDUCE líneas del game_loop (las 4 llamadas sueltas se agrupan en
> 2 bloques `if`). El resultado queda en ~20 líneas. `draw_endscreen` va FUERA de la
> función (después de `mlx_put_image_to_window`, como texto de ventana — no de imagen).

Esto elimina escopeta, crosshair Y render_weapon de la pantalla de fin.

**Gate B2:** Pantalla de fin limpia: solo fondo + texto + HUD. Sin arma visible.

---

## Ficheros tocados / nuevos

- **Fase B1:** `sources/render/game_loop.c` (+`draw_endscreen` + llamada tras put_image).
- **Fase B2:** `sources/bonus/render/hud.c` (ajustar rectángulo), `sources/render/game_loop.c`
  (guard escopeta con game_state).

Ningún fichero nuevo. Solo modificaciones menores.

---

## Dependencias con Persona A

| Fase B | Depende de A | Descripción |
|--------|-------------|-------------|
| B1 | Ninguna | Puede hacerse ya (game_state ya existe) |
| B2 | Ninguna | Puede hacerse ya |
| — | A2 (restart) | El texto "Press R" solo tiene sentido si A ya implementó el restart. Pero el texto se puede poner antes — simplemente la tecla no hará nada hasta que A lo conecte. |

**Orden recomendado:** B puede empezar primero (es más rápido). A implementa flow field + restart en paralelo.

---

## Estado de avance
- [ ] Fase B1 — Texto "YOU WIN" / "YOU LOSE" + "Press R"
- [ ] Fase B2 — Ajustes visuales (rectángulo + ocultar escopeta)
