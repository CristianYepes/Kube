# AUDITORIA ADVERSARIAL — rama `origin/bonus` (Rodrigo)

> Fecha: 2026-06-24
> Rama auditada: `origin/bonus` (commit `a3d6e78`)
> Base comparada: `dev` (commit `712d40c`)
> Metodo: 5 passes del protocolo ROMPE_MI_CODIGO.md

---

## ESTADO DE PASSES

| Pass | Nombre | Estado | Agente |
|---|---|---|---|
| 1 | Asesino de memoria | COMPLETADO | Hallazgos integrados |
| 2 | Demonio de inputs | COMPLETADO | Hallazgos integrados |
| 3 | Abogado de contratos | COMPLETADO | Hallazgos integrados |
| 4 | Saboteador logico | COMPLETADO | Hallazgos integrados |
| 5 | Policia de norma | COMPLETADO | Hallazgos integrados |

---

## 1. BLOQUEANTES PARA EVALUACION

### 1.1 Norminette (6 errores)

| Archivo | Linea | Error | Fix |
|---|---|---|---|
| `input.c` | 44 | TOO_MANY_LINES (27 en `key_press`) | Extraer helper |
| `init_game.c` | 43 | TOO_MANY_LINES | Extraer helper |
| `game_loop.c` | 33 | NEWLINE_PRECEDES_FUNC | Anadir linea en blanco |
| `render_sprites.c` | 33,36 | TOO_MANY_TAB | Reducir indentacion |
| `shotgun.c` | 102 | TOO_MANY_FUNCS (6 en archivo) | Mover funcion a otro .c |
| `cub3d.h` | 172 | MISALIGNED_VAR_DECL (`struct timeval`) | Alinear con tabs |

### 1.2 Funcion prohibida por subject (Cap. V)

| Archivo | Linea | Funcion | Fix |
|---|---|---|---|
| `render_sprites.c` | 81 | `abs()` — no en lista permitida | `if (val < 0) val = -val;` |

### 1.3 Sin guardia `#ifdef BONUS` — separacion mandatory/bonus INEXISTENTE

No hay ningun `#ifdef BONUS` en todo el codigo. Features bonus (sprites '2'/'3', escopeta,
mouse-look, minimapa) se compilan SIEMPRE. Un evaluador del mandatory vera bonus activo = FALLO.

Archivos afectados:
- `check_map.c:96` — acepta '2' y '3' incondicionalmente
- `sprites.c:64`, `init_sprites.c:15-34` — sprites cargados siempre
- `minimap.c:82`, `minimap_2.c:72` — minimap siempre activo
- `shotgun.c` (entero), `init_game.c:40-41`, `input.c:39-40`, `game_loop.c:49-50`
- `mlx.c:19-20` — mouse hooks registrados siempre

### 1.4 Validacion de F/C incompleta (BUG del parser)

- **Archivo:** `fill_color_textures.c` (pone bits en id_flags) + `parsing_data.c` (nunca verifica completitud)
- **Input:** `.cub` sin linea `F` o `C`
- **Resultado:** se renderiza con color 0x000000 en vez de rechazar el fichero
- **Subject:** exige que AMBOS esten presentes

---

## 2. MEMORY LEAKS CONFIRMADOS (PASS 1 completado — exhaustivo)

### 2.1 Tabla INIT vs EXIT — discrepancias

| Recurso | Allocado en | Liberado en `exit_game`? |
|---|---|---|
| `data->mlx` | init_game.c:18 | **NO** (falta `mlx_destroy_display` + `free`) |
| `data->win` | init_game.c:21 | SI (`mlx_destroy_window`) |
| `data->img.img` | init_game.c:24 | SI (`mlx_destroy_image`) |
| `data->z_buffer` | init_game.c:29 | SI (`free`) |
| `data->textures[0..3]` | init_textures.c:27-30 | SI (`free_textures`) |
| `data->sprite_tex[0..1]` | init_sprites.c:17-18 | **NO — LEAKED** |
| `data->sprite_tex2[0..1]` | init_sprites.c:19-20 | **NO — LEAKED** |
| `data->sprites` | init_sprites.c:29 | **NO — LEAKED** |
| `data->gun_tex[0..3]` | shotgun.c:17-24 | **NO — LEAKED** |
| `data->tex_paths[0..3]` | get_file_data.c:54 | SI (via `free_parsing`) |
| `data->map[0..n]` | create_game_map.c:63,92 | SI (via `free_parsing`) |
| `data->file_lines[0..n]` | parsing_data.c:76,48-53 | SI (freed antes de init) |

**Total leak por ejecucion normal:** ~12.96 MB (4 gun_tex de 900x900x4 bytes) + 64 KB (4 sprite_tex de 64x64x4) + array sprites.

### 2.2 Leaks en salida normal (10 buffers)

| # | Recurso | Allocado en | Bytes |
|---|---|---|---|
| 1 | `data->sprites` | init_sprites.c:29 | `sizeof(t_sprite) * count` |
| 2 | `data->sprite_tex[0]` | init_sprites.c:17 | 16,384 |
| 3 | `data->sprite_tex[1]` | init_sprites.c:18 | 16,384 |
| 4 | `data->sprite_tex2[0]` | init_sprites.c:19 | 16,384 |
| 5 | `data->sprite_tex2[1]` | init_sprites.c:20 | 16,384 |
| 6 | `data->gun_tex[0]` | shotgun.c:17 | 3,240,000 |
| 7 | `data->gun_tex[1]` | shotgun.c:18 | 3,240,000 |
| 8 | `data->gun_tex[2]` | shotgun.c:19 | 3,240,000 |
| 9 | `data->gun_tex[3]` | shotgun.c:20 | 3,240,000 |
| 10 | `data->mlx` (X11 conn) | init_game.c:18 | variable |

### 2.3 Leaks en rutas de error de init (cascading failures)

| # | Ruta de error | Que se pierde |
|---|---|---|
| 1 | `mlx_new_window` falla (init_game.c:22) | `data->mlx` (no destroy_display) |
| 2 | `mlx_new_image` falla (init_game.c:24) | `data->mlx` + `data->win` |
| 3 | `init_textures` falla (init_game.c:32) | `z_buffer` + `mlx` (img/win destruidos pero mlx no) |
| 4 | `init_sprites_data` falla (init_game.c:38) | `z_buffer` + `textures[0..3]` + `img` + `win` + `mlx` |
| 5 | `init_shotgun` falla (init_game.c:40) | Todo anterior + sprites ya cargados |
| 6 | `sprite_tex[1]` falla (init_sprites.c:21) | `sprite_tex[0]` |
| 7 | `sprite_tex2[0]` falla (init_sprites.c:23) | `sprite_tex[0..1]` |
| 8 | `sprite_tex2[1]` falla (init_sprites.c:23) | `sprite_tex[0..1]` + `sprite_tex2[0]` |
| 9 | `gun_tex[n+1]` falla (shotgun.c:25) | `gun_tex[0..n]` |

### 2.4 Riesgos de double-free

| # | Ubicacion | Escenario | Riesgo actual |
|---|---|---|---|
| 1 | exit_game.c:34 + init_game.c:34-35 | Si `init_textures` falla, ya destruye img/win. Si luego exit_game se llama (signal), double-destroy. | BAJO (exit() previene re-entry) |
| 2 | exit_game.c:23 | `free(textures[i])` sin NULL posterior. Double-call = double-free. | BAJO (exit() inmediato) |

### 2.5 NULL checks faltantes

| # | Ubicacion | Que allocation |
|---|---|---|
| 1 | init_game.c:22 | `mlx_new_window` fail no limpia mlx |
| 2 | init_game.c:24 | `mlx_new_image` fail no limpia win + mlx |
| 3 | init_game.c:27 | `mlx_get_data_addr` return no verificado |

### 2.6 Fix requerido para `exit_game`

```c
// Anadir ANTES de free_textures:
int i = 0;
while (i < 2)
{
    if (data->sprite_tex[i])
        free(data->sprite_tex[i]);
    if (data->sprite_tex2[i])
        free(data->sprite_tex2[i]);
    i++;
}
if (data->sprites)
    free(data->sprites);
i = 0;
while (i < GUN_FRAMES)
{
    if (data->gun_tex[i])
        free(data->gun_tex[i]);
    i++;
}
// Anadir DESPUES de mlx_destroy_window:
mlx_destroy_display(data->mlx);
free(data->mlx);
```

### 2.7 Prototipo duplicado en header

- `cub3d.h:225,238` — `mouse_tracker` declarado dos veces (no leak pero codigo muerto)

---

## 3. BUGS LOGICOS (PASS 4 completado)

| # | Archivo:linea | Bug | Trigger | Gravedad |
|---|---|---|---|---|
| 1 | `raycasting.c:71` | DDA sale del mapa con hit=0, draw_wall_column dibuja "muro fantasma" en el borde | Ray que escapa del mapa (masked por check_map_borders) | Baja (defended by parser) |
| 2 | `render_sprites.c:72` | Div por ~0: `1.0/(plane_x*dir_y - dir_x*plane_y)` sin guardia | Millones de rotaciones (fp drift) | Muy baja |
| 3 | `shotgun.c:107` | start_x=690, textura 900px → x va de 690 a 1589 (pantalla=1280). start_y=-130. **~395K put_pixel descartados por frame (~49% waste)** | Cada frame incondicional | **Alta (perf)** |
| 4 | `game_loop.c` | Render incondicional cada frame (se elimino optimizacion `has_moved`) | Siempre | Baja (perf) |
| 5 | `player.c:46` | `is_wall` solo bloquea '1' — sprites ('2','3') son atravesables | Caminar a sprite | Info (probablemente intencionado) |
| 6 | `minimap.c:116` | Minimap en (0,0) superior izquierda, DoD pide inferior izquierda | Siempre | Media (bonus DoD) |

### Detalle PASS 4 — Analisis exhaustivo

**BUG 3 ampliado (shotgun perf):**
```
start_x = WIN_W/2 - GUN_SIZE/2 + 500 = 640 - 450 + 500 = 690
start_y = WIN_H - GUN_SIZE + 50 = 720 - 900 + 50 = -130
```
Iteraciones totales: 900x900 = 810,000 por frame.
Fuera de pantalla: (1589-1280)*900 = 278,100 (derecha) + 130*900 = 117,000 (arriba) ≈ 395,100 calls descartados.
El offset `+500` es casi seguro un error o la textura no esta pensada para ese tamano.

**BUG 1 ampliado (ray miss):**
Cuando hit=0, `wall_dist = side_x - delta_x` produce la distancia al borde del mapa (valor
positivo valido por la matematica del DDA). Se dibuja un muro fantasma con textura real.
Actualmente defended por `check_map_borders` que fuerza bordes '1'. No crashea pero es
arquitecturalmente incorrecto (deberia skip con `if (!ray->hit) continue;`).

### Sospechosos logicos (no crashean)

| # | Archivo:linea | Razonamiento | Riesgo |
|---|---|---|---|
| S1 | `render_sprites.c:24` | tex_x podria alcanzar TEX_SIZE si size es muy pequeno. Analisis muestra que truncacion entera lo previene. | Muy bajo |
| S2 | `game_loop.c:27` | `frame_idx` llega a 2 brevemente antes del reset. Safe solo porque `tick_sprite_anim` corre ANTES de `render_sprites`. Si cambia el orden → OOB en `sprite_tex[2]`. | Bajo (fragil) |
| S3 | `draw_wall.c:84` | wall_dist podria ser negativo en teoria. Guard `< 0.0001` en linea 87 lo cubre. | Ninguno |

---

## 4. HALLAZGOS DEL PARSER (PASS 2)

### 4.1 Confirmados

1. **F/C no validados** (ver 1.4 arriba)
2. **`init_sprites` ignora parametro `type`** — `(void)type;` en sprites.c:55. Funciona por
   accidente porque hardcodea `'2' || '3'`. Bomba de mantenimiento.

### 4.2 Sospechosos

| # | Archivo:linea | Escenario | Riesgo |
|---|---|---|---|
| 1 | `get_file_data.c:37` | Linea basura → TYPE_MAP → error confuso "Map must be last" | Evaluador confundido |
| 2 | `check_map_borders.c:24` | Asume rectangular (safe por padding, pero acoplado a create_game_map) | Futuro refactor |
| 3 | `fill_color_textures.c` | Acepta `F 007,008,009` (leading zeros) | Evaluador estricto |
| 4 | `check_args.c:21` | Acepta `.cub` como nombre (hidden file sin basename) | Menor |

### 4.3 Validaciones que SI funcionan correctamente

- '2'/'3' en borde del mapa → rechazado por check_map_borders (requiere '1' en bordes)
- Mapa sin jugador → rechazado (count != 1)
- RGB negativo, overflow → rechazado
- Lineas de mapa de longitud irregular → padding correcto con '1'
- GNL trailing '\n' → correctamente stripped con ft_strtrim

---

## 5. CONTRATOS CALLER/CALLEE (PASS 3)

### 5.1 Confirmados

Todos los items de la seccion 2 (leaks) vienen de contratos rotos entre init y exit.

### 5.2 Notas positivas

- ft_split delimitadores consecutivos: guardado por check `count_char(str,',') != 2`
- ft_atoi overflow: guardado por check de longitud <= 3 digitos
- Return value conventions (SUCCESS/FAILURE/ERR): consistentes entre callers/callees
- GNL '\n' trailing: correctamente manejado en todos los call sites

---

## 6. RESUMEN EJECUTIVO

| Categoria | Count | Bloquea evaluacion? |
|---|---|---|
| Norminette | 6 errores | SI |
| Funcion prohibida (`abs`) | 1 | SI |
| Sin `#ifdef BONUS` | ~15 archivos | SI |
| Parser F/C no validado | 1 | SI |
| Memory leaks (salida normal) | 7+ buffers | SI (valgrind) |
| Memory leaks (error paths) | 5 paths | SI (valgrind) |
| Bugs logicos | 6 | Parcial |
| Sospechosos | 5 | No |

**Veredicto: esta rama NO es mergeable sin arreglos.**

---

## 7. FIXES PRIORITARIOS PARA MERGEAR

### Criticos (bloquean evaluacion — hacer ANTES de merge):
1. `exit_game.c` — anadir free de sprites, sprite_tex, sprite_tex2, gun_tex, mlx (ver 2.6)
2. `render_sprites.c:81` — reemplazar `abs()` por calculo manual
3. 6 errores de norminette (ver 1.1)
4. Separar mandatory de bonus con `#ifdef BONUS` o estructura de archivos
5. Validar presencia de F y C en el parser

### Importantes (afectan calidad pero no bloquean solos):
6. `shotgun.c:107` — corregir offset (+500 incorrecto) o reducir GUN_SIZE
7. `init_game.c` — cascading cleanup en error paths
8. `init_sprites.c` / `shotgun.c` — partial-failure cleanup
9. `minimap.c` — mover a esquina inferior izquierda
10. Prototipo duplicado en header (`mouse_tracker`)

### Opcionales (mejora arquitectural):
11. `raycasting.c` — skip draw_wall_column si hit=0
12. `game_loop.c` — restaurar optimizacion `has_moved`
13. `game_loop.c:27` — hacer frame_idx wrap mas robusto (no depender del orden de llamadas)

---

## 8. CONCLUSION

**Los 5 passes del protocolo adversarial estan COMPLETOS.**

La rama `origin/bonus` de Rodrigo tiene trabajo funcional significativo (minimapa, mouse,
sprites animados, escopeta) pero NO esta lista para merge. Hay 9+ issues bloqueantes para
evaluacion y ~13 MB de leaks por ejecucion.

Recomendacion: coordinar con Rodrigo para que arregle norminette + leaks en su rama,
o mergear y arreglar juntos en `dev` con un plan de integracion claro.

---
