# SPEC — Mejoras B: endscreen + limpieza visual (rama `mejoras-B`)

## Contexto

El mod zombies está **completo y funcional** (3 oleadas, IA, hitscan, niebla, HUD). Pero la
pantalla de fin de partida es un rectángulo de color plano sin texto — el jugador no sabe si
ganó o perdió, ni que puede reiniciar. Además, la escopeta y el crosshair se siguen pintando
debajo del rectángulo (desperdicio visual), y los sprites decorativos del mapa ('2'/'3') son
**invisibles** porque `render_sprites()` no se llama en el game loop bonus.

Cristian (Persona B en esta rama) implementa **solo la parte de render/presentación**:
texto en pantalla, limpieza visual, y el fix del sprite. La lógica de restart (tecla R) la
hace Persona A en la rama `mejoras-A` — aquí solo se muestra el mensaje "Press R".

> Regla 42 en todo el spec: ≤25 líneas/func, ≤5 funcs/fichero, ≤4 params, ≤5 vars, sin
> globals, sin `rand`/`sprintf`/`stat`. Solo se dan **prototipos + pasos**, no cuerpos.

---

## Decisiones de diseño

- **D1 — `mlx_string_put` para texto.** Función de MiniLibX que dibuja directamente sobre
  la **ventana** (no sobre el buffer de imagen). Se llama DESPUÉS de `mlx_put_image_to_window`
  cada frame. No hay flicker porque el game loop redibuja en secuencia (blit imagen → texto
  encima → siguiente frame). **Función permitida** (subject Cap. V: todas las de MiniLibX).
- **D2 — Rectángulo de contraste como fondo.** El `draw_game_over()` actual en `hud.c`
  (200×40px, rojo/verde) se mantiene y se agranda a 200×60px con colores oscuros para que
  el texto blanco sea legible.
- **D3 — Sin bitmap font propio.** `mlx_string_put` usa la fuente X11 del sistema. Es
  pequeña pero funcional. No merece implementar un motor de texto para dos strings.
- **D4 — `render_sprites` ANTES de `render_enemies`.** Los sprites decorativos se pintan
  primero (z-buffer ya relleno por `cast_rays`); los enemigos se pintan después y los tapan
  si están más cerca. Orden correcto de painter's algorithm.

---

## FASE B1 — Texto "YOU WIN" / "YOU LOSE" + "Press R to restart"

### B1.1 Nueva función static en `sources/render/game_loop.c`

Ubicarla ANTES de `game_loop()` (entre el `#ifdef BONUS` y la función principal):
```c
static void	draw_endscreen(t_data *data)
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
- 2 vars (`cx`, `cy`) · 12 líneas · 0 params extra (solo `data`).

### B1.2 Llamada en `game_loop()` (l.40, tras `mlx_put_image_to_window`)

Insertar después de la línea 40:
```c
if (data->game_state != G_PLAY)
    draw_endscreen(data);
```

### B1.3 Conteo de norma tras B1

| Métrica | Valor |
|---------|-------|
| Funciones en `game_loop.c` | 3 (draw_endscreen + game_loop bonus + game_loop mandatory) — máx 5 ✓ |
| Líneas de `game_loop()` bonus | 25 (23 actuales + 2 nuevas) — límite justo ✓ |
| Líneas de `draw_endscreen` | 12 ✓ |
| Vars de `draw_endscreen` | 2 ✓ |

**Gate B1:** Al morir → "YOU LOSE" en rojo (#FF4444) + "Press R to restart" en blanco, centrados
sobre el rectángulo rojo del HUD. Al ganar → "YOU WIN" en verde (#44FF44) + mismo mensaje sobre
rectángulo verde. Se redibuja cada frame → sin flicker. Norminette 0 en `game_loop.c`.

---

## FASE B2 — Ocultar escopeta/arma + render_sprites + ajuste HUD

### B2.1 Guard de escopeta/arma en `game_loop.c` (l.34-36 actuales)

Cambiar:
```c
tick_shotgun(data, data->dt);
draw_shotgun(data);
render_weapon(data);
```
Por:
```c
if (data->game_state == G_PLAY)
{
    tick_shotgun(data, data->dt);
    draw_shotgun(data);
    render_weapon(data);
}
```
Esto **elimina** escopeta, crosshair y render_weapon de la pantalla de fin.

### B2.2 Añadir `render_sprites(data)` — fix bug sospechoso #3

Insertar **después de `cast_rays(data)`** y **antes de `render_enemies(data)`** (l.32-33):
```c
render_sprites(data);
```
Esto pinta los sprites decorativos del mapa ('2'/'3') usando el z-buffer que `cast_rays`
acaba de rellenar. Los enemigos se pintan después y tapan los sprites si están más cerca.

### B2.3 Ajuste de `draw_game_over` en `sources/bonus/render/hud.c` (l.67-83)

Cambiar:
```c
y = WIN_H / 2 - 20;
while (y < WIN_H / 2 + 20)
```
Por:
```c
y = WIN_H / 2 - 20;
while (y < WIN_H / 2 + 30)
```
(60px de alto en vez de 40, cubre la línea "Press R to restart".)

Cambiar los colores del rectángulo en `render_hud` (l.85-96):
```c
if (data->game_state == G_OVER)
{
    draw_game_over(data, 0x440000);    /* rojo oscuro para contraste */
    return ;
}
if (data->game_state == G_WIN)
{
    draw_game_over(data, 0x004400);    /* verde oscuro para contraste */
    return ;
}
```

### B2.4 Conteo de norma tras B2

| Métrica | Valor |
|---------|-------|
| Líneas de `game_loop()` bonus | ~22 (el guard agrupa 3 llamadas en un bloque `if`) ✓ |
| Funciones en `game_loop.c` | 3 (sin cambio) ✓ |
| `hud.c` funciones | 4 (sin cambio) ✓ |
| `draw_game_over` líneas | 11 (+1 por el cambio de alto) ✓ |

**Gate B2:** Pantalla de fin = fondo oscuro (rojo/verde) + texto (B1) + HUD (vida/wave) encima.
Sin escopeta, sin crosshair, sin render_weapon. Sprites decorativos del mapa visibles durante el
juego. `norminette sources/render/game_loop.c sources/bonus/render/hud.c` → 0 errores.

---

## Ficheros tocados

| Fichero | Cambio | Fase |
|---------|--------|------|
| `sources/render/game_loop.c` | +`draw_endscreen` static, +llamada post-blit, +guard arma `G_PLAY`, +`render_sprites(data)` | B1 + B2 |
| `sources/bonus/render/hud.c` | `draw_game_over` alto 40→60px, colores `0x440000`/`0x004400` | B2 |

Ningún fichero nuevo. Ningún cambio en `cub3d.h`.

---

## Orden de ejecución

1. **B1:** Añadir `draw_endscreen` + llamada tras `mlx_put_image_to_window`. Compilar, probar
   (morir y ganar → ver texto). Commit.
2. **B2:** Guard arma + `render_sprites` + ajuste HUD. Compilar, probar (pantalla limpia,
   sprites visibles). Commit.

---

## Dependencias con Persona A

| Fase B | Depende de A | Nota |
|--------|-------------|------|
| B1 | Ninguna | `game_state` ya existe |
| B2 | Ninguna | `render_sprites` ya está compilada y linkeada |
| — | A2 (restart) | El texto "Press R" se muestra ya; la tecla no hace nada hasta que A conecte `restart_game()` |

**Persona B puede empezar ya.** No hay bloqueo.

---

## Verificación (DoD global)

```bash
make bonus                        # 0 warnings
norminette sources/render/game_loop.c sources/bonus/render/hud.c   # 0 errores
valgrind --suppressions=mlx.supp ./cub3D_bonus maps/good/subject_map.cub
# Probar: jugar → morir → ver "YOU LOSE" + "Press R" → ESC → 0 leaks
# Probar: jugar → ganar (3 oleadas) → ver "YOU WIN" + "Press R" → ESC → 0 leaks
# Probar: durante juego → sprites decorativos visibles
# Probar: pantalla de fin → sin escopeta/crosshair visible
```

---

## Estado de avance
- [ ] Fase B1 — Texto "YOU WIN" / "YOU LOSE" + "Press R to restart"
- [ ] Fase B2 — Ocultar escopeta + render_sprites + ajuste HUD
