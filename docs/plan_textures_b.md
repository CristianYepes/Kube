# Plan: Persona B — Carga de texturas + Render texturizado (S03B + S07B)

## Contexto

El raycasting con muros de color plano (`0xFFFFFF`) ya funciona. El siguiente paso de Persona B es:
1. Cargar las texturas XPM a memoria como `int[]`
2. Usarlas en el renderizado de muros (en vez del color blanco fijo)

Archivos XPM disponibles en `files/`: `wall_cross.xpm`, `wall_pipes.xpm`, `floor_stone.xpm` (todos 64x64).

---

## Cluster 1 — Infraestructura (modificar structs)

**Archivo:** `includes/cub3d.h`

| # | Tarea | Detalle |
|---|---|---|
| 1.1 | Anadir macro `TEX_SIZE` | `# define TEX_SIZE 64` |
| 1.2 | Anadir campo `int *textures[4]` a `t_data` | Array de 4 punteros a int (uno por cara N/S/E/W) |
| 1.3 | Anadir prototipo `init_textures` | `void init_textures(t_data *data);` |

---

## Cluster 2 — Carga de XPM a int[] (S03B)

**Archivo nuevo:** `sources/init/init_textures.c`

| # | Tarea | Detalle |
|---|---|---|
| 2.1 | Funcion `static int *xpm_to_int(t_data *data, char *path)` | 1) `mlx_xpm_file_to_image(data->mlx, path, &w, &h)` -> obtiene `void *img`. 2) `mlx_get_data_addr(img, &bpp, &size_line, &endian)` -> obtiene `char *addr`. 3) `malloc(sizeof(int) * TEX_SIZE * TEX_SIZE)` -> buffer destino. 4) Copiar pixeles: bucle `y*size_line + x*(bpp/8)` -> cast a `unsigned int`. 5) `mlx_destroy_image(data->mlx, img)` -> liberar imagen temporal. 6) Devolver el `int *`. |
| 2.2 | Funcion `void init_textures(t_data *data)` | Llama a `xpm_to_int` 4 veces con rutas hardcodeadas: `"files/wall_cross.xpm"` (N+S) y `"files/wall_pipes.xpm"` (E+W). Guarda en `data->textures[NORTH..EAST]`. |
| 2.3 | Llamar `init_textures(data)` desde `init_game()` | Despues de `mlx_init` y antes del game loop. |

---

## Cluster 3 — Renderizado texturizado (S07B)

**Archivo a modificar:** `sources/render/raycasting.c` (funcion `draw_wall_column`)

| # | Tarea | Detalle |
|---|---|---|
| 3.1 | Elegir textura segun cara | `side==0 && dir_x<0` -> WEST, `side==0 && dir_x>0` -> EAST, `side==1 && dir_y<0` -> NORTH, `side==1 && dir_y>0` -> SOUTH. |
| 3.2 | Calcular `wall_x` | Si `side==0`: `wall_x = pos_y + wall_dist * ray->dir_y`. Si `side==1`: `wall_x = pos_x + wall_dist * ray->dir_x`. Luego `wall_x -= floor(wall_x)` (parte decimal). |
| 3.3 | Calcular `tex_x` | `tex_x = (int)(wall_x * TEX_SIZE)`. Invertir segun cara para evitar espejo: `if (side==0 && dir_x>0) tex_x = TEX_SIZE - tex_x - 1` / `if (side==1 && dir_y<0) tex_x = TEX_SIZE - tex_x - 1`. |
| 3.4 | Calcular `tex_y` en el bucle vertical | `step = TEX_SIZE / (double)line_h`. `tex_pos = (start - WIN_H/2 + line_h/2) * step` (ajustado si start fue clampeado). Bucle: `tex_y = (int)tex_pos & (TEX_SIZE - 1)`, `tex_pos += step`. |
| 3.5 | Leer color de textura | `color = data->textures[tex_idx][TEX_SIZE * tex_y + tex_x]`. |
| 3.6 | Shading caras N/E | `color = (color >> 1) & 0x7F7F7F` para oscurecer ligeramente las caras norte y este. |
| 3.7 | Reemplazar `put_pixel(data, x, start, 0xFFFFFF)` | Por `put_pixel(data, x, y, color)` con el color texturizado. |

---

## Cluster 4 — Cleanup + Verificacion

| # | Tarea | Detalle |
|---|---|---|
| 4.1 | Liberar texturas en `exit_game()` | Bucle `i = 0..3`: `free(data->textures[i])`. |
| 4.2 | Anadir `init_textures.c` al Makefile | En la variable `SRC`. |
| 4.3 | Compilar y probar | `make re && ./cub3D maps/good/test_basic.cub` -> muros con texturas visibles. |
| 4.4 | Norminette | `norminette sources/init/init_textures.c sources/render/raycasting.c includes/cub3d.h` |
| 4.5 | Commit | Mensaje descriptivo tipo `feat(render): load XPM textures and apply to wall faces` |

---

## Archivos tocados (resumen)

| Archivo | Accion |
|---|---|
| `includes/cub3d.h` | Anadir macro + campo + prototipo |
| `sources/init/init_textures.c` | **NUEVO** — carga XPM |
| `sources/init/init_game.c` | Anadir llamada a `init_textures` |
| `sources/render/raycasting.c` | Reescribir `draw_wall_column` con textura |
| `sources/exit/exit_game.c` | Anadir free de texturas |
| `Makefile` | Anadir `init_textures.c` a SRC |

---

## Verificacion final

1. `make re` compila sin warnings
2. Ejecutar con el mapa hardcodeado -> muros con textura visible (cross en N/S, pipes en E/W)
3. Girar 360 grados -> las texturas cambian entre caras
4. Caras N/E ligeramente mas oscuras que S/W
5. Sin leaks nuevos: `valgrind --leak-check=full ./cub3D maps/good/test_basic.cub` (cerrar con ESC)
6. `norminette` pasa en archivos modificados
