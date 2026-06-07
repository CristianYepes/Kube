# S03A + S04A — Ruta de ejecucion (FINAL, verificada)

> S03A: `parsing/parse_data.c` + `get_file_data.c` — leer fichero .cub a memoria y clasificar lineas.
> S04A: `parsing/fill_color_textures.c` — parsear y validar F/C RGB.
> Prerequisito: S02A done.

---

## PARTE 0 — Gate antes de teclear NADA

### D0 — BLOQUEANTE: el modelo de datos es compartido y los docs se contradicen 3 veces

S02A no toco structs. S03A es donde nace el modelo de datos, y eso lo consume Rodrigo (render). Lo unico que la verificacion de codigo NO puede arreglar:

1. **Representacion de texturas a tres bandas en los docs:**
   - roadmap: `char *tex_paths[4]` (roadmap.md:488)
   - cronograma S03A: `texinfo.north/south/west/east` (4 campos) (cronograma.md:489)
   - cronograma S04A/S06A: `texinfo.hex_floor/hex_ceiling`
   Son incompatibles. Elige UNA antes de la primera linea.

2. El roadmap F1 usa `void + exit(1)` en sitio (roadmap.md:709,753) y la cronograma S03A tambien (`void parse_data`, cronograma.md:479). Eso rompe tu modelo ya cerrado (`int` + `err_msg` que propaga, sin `exit` en el parser). Toda firma `void` de esos listados se convierte en `int`.

3. `cub3d.h` es compartido y Rodrigo esta en rama divergente. Definir el struct raiz por tu cuenta = conflicto en el merge.

**D0 RESUELTO:** Struct raiz = `t_data` (en `cub3d.h`). Rodrigo tiene `t_cub3d` en `cubed.h` pero su codigo necesita reescritura completa (no pasa norminette, arquitectura render por decidir). Se reconcilia en el merge, no ahora.

**Recomendacion adoptada:** `char *tex_paths[4]` indexado por enum `{NORTH, SOUTH, WEST, EAST}` que coincida con el `tex_num` del raycaster (0=NO,1=SO,2=WE,3=EA). El enum tiene uso inmediato (indexar en S03A), no es especulativo.

**Estado de Rodrigo (revision 2026-05-31):** tiene raycaster funcional basado en angulo (no vector+plano DDA del roadmap). Su codigo usa bool, no pasa norminette, no tiene parser/texturas/colores/cleanup. Minas de integracion: (1) solape input/movimiento, (2) choque arquitectura render, (3) estilo/naming. Ninguna bloquea S03A/S04A — el parser es independiente del render.

---

### D1 — Modelo de datos minimo (SOLO lo que S03A+S04A escribe)

Nada de player/ray/keys/img/bonus/sprite (eso nace en lado B cuando su codigo nazca). Campos:

| Campo | Tipo | Quien lo escribe | Vida |
|---|---|---|---|
| lineas crudas del fichero | `char **` | S03A (lectura) | transitorio (se libera al acabar parsing) |
| n de lineas | `int` | S03A | -- |
| rutas textura | `char *tex_paths[4]` | S03A | hasta free global (S09AB) |
| color suelo / techo | `int floor_color` / `int ceiling_color` | S04A | -- |
| flags "ya visto" (4 tex + 2 color) | `int` (o bitmask) | S03A/S04A | duplicados |

---

### D2 — Lectura del fichero

Recomendado dos pasadas (contar lineas con GNL -> cerrar -> reabrir -> rellenar array dimensionado): mas facil de norminar. Doble I/O aceptable (fichero pequeno).

**Trampas confirmadas en tu GNL (get_next_line.c):**
- GNL devuelve la linea CON `\n`. La ultima puede venir SIN `\n`.
- GNL tiene buffer estatico `keep`: si sales del bucle antes de NULL, leakeas. Hay que drenar a NULL en cada pasada, tambien en la rama de error. `close(fd)` NO limpia ese buffer.

---

### D3 — Dispatcher (clasificar cada linea ya leida)

Tras saltar espacios iniciales:
- vacia / solo whitespace -> ignora (en S03A; dentro del mapa sera error en S05A).
- token exacto `NO`/`SO`/`WE`/`EA` seguido de whitespace -> textura. (Ojo: "NORTH"/"NOPE" NO deben matchear NO; exige el whitespace tras el token.)
- token exacto `F`/`C` seguido de whitespace -> color (lo procesa S04A). ("Fabc" no es color valido ni mapa -> error.)
- resto -> candidata a mapa (se valida en S05A).
- Decide AHORA (aunque lo enforces en S05A): identificador que aparece DESPUES de empezar el mapa -> error (subject: mapa siempre al final). Linea en blanco dentro del mapa -> error.

---

### D4 — Texturas: SOLO extraer y guardar (NO validar existencia)

Confirmado: existencia + extension .xpm es S06A (check_textures, cronograma.md:680,698). En S03A:
- salta identificador + espacios, toma el resto hasta fin de linea,
- strip del `\n` y del `\r` (CRLF Windows) — usa `ft_strtrim(rest, " \t\n\r")`. OJO: `ft_strtrim` YA hace malloc de una copia recortada. NO hagas `ft_strdup` despues — duplicarias memoria o leakeas el intermedio. Una sola asignacion propietaria: `path = ft_strtrim(rest, " \t\n\r")` y nada mas.
- detecta duplicado (flag "ya visto").
- **Caso extra:** identificador sin ruta (`NO\n` o `NO   \n`). Tras saltar NO + espacios y hacer strip, queda cadena vacia -> error.

Beneficio: tus fixtures NO necesitan .xpm reales.

---

### D5 — Propiedad de memoria

- **Lineas del fichero:** las posee la struct hasta acabar el parsing; liberalas cuando ya no las uses (decide: tras construir grid en S05A, o copias y liberas ya?). Documenta.
- **Rutas textura:** `ft_strdup` -> struct -> free global (S09AB).
- **Cualquier rama de error:** libera lo alocado + drena GNL a NULL antes de `return (FAILURE)`. Tienes `ft_free_strs(char**, char**, char**)` en tu libft (libft.h:100) para arrays.
- **DoD:** valgrind clean tambien con un input que falla (no solo el feliz).

---

### D6 (S04A) — RGB con validacion

- localiza F/C, salta espacios, toma el resto, strip `\n`/`\r`.
- trocea por `,`. **Trampa confirmada (ft_split.c):** colapsa delimitadores consecutivos -> `"220,,100"`->2 tokens (se rechaza, bien), pero `"220,100,0,,"`->3 tokens (pasa!). Y `",,,"`->0 palabras con `tab[0]==NULL` (tu conteo no debe segfaultear).
- exige exactamente 3 tokens.
- cada token: solo digitos (rechaza `-`, `+`, letras, vacio, y espacios interiores tipo `F 220, 100, 0` -> decide: rechazalos, es defendible). `ft_isdigit` esta en libft.
- **overflow confirmado (ft_atoi.c no lo detecta):** 99999999999 envuelve y puede caer en rango -> anade tope de longitud (>3 digitos = rechazo) ademas del rango [0,255]. NOTA: >3 digitos tambien rechaza zero-padding como `0255` (4 digitos, valor real 255). Es defendible (estricto) y resuelve el overflow limpiamente. NO parchear ft_atoi — validar ANTES.
- compon `(R<<16)|(G<<8)|B`, guarda como int.
- duplicado: si F (o C) ya seteado -> error.

---

## PARTE 1 — S03A (tareas)

### T1 — Estructura de archivos

Crea `sources/parsing/parse_data.c` + `sources/parsing/get_file_data.c` (header 42, `#include "cub3d.h"`).

**Verify:** ambos existen.

---

### T2 — Modelo de datos en cub3d.h

(TRAS D0) anade a `cub3d.h` SOLO los campos de D1 + el enum. No metas t_game/player/ray/keys/img/bonus/sprite (roadmap.md:517-537) — YAGNI + iman de conflictos. Coordina con Rodrigo.

**Verify:** struct con <= los 6 campos de D1; nada mas.

---

### T3 — Lector de fichero

`open` (`O_RDONLY`) -> si -1 `return (err_msg(path, strerror(errno), FAILURE))` -> bucle GNL guardando cada linea hasta NULL -> close. En fallo de malloc: libera parcial + drena GNL a NULL -> `return (FAILURE)`.

**Verify:** `line_count` correcto; sin leak (valgrind) en exito y en error. Si `line_count == 0` (fichero vacio), `return (err_msg(NULL, ERR_INVALID_MAP, FAILURE))` aqui — es el sitio mas barato y temprano.

---

### T4 — Dispatcher get_file_data

Recorre lineas, clasifica por D3. Norma: extrae la clasificacion a un `static int line_type(char *line)` — si metes todo en una funcion te pasas de 25 lineas / 5 vars. Rutea textura->handler, deja F/C para S04A, deja mapa para S05A.

**Verify:** clasifica bien los 4 tipos; funcion <=25 lineas.

---

### T5 — Extraccion de ruta de textura

Strip `\n`/`\r` + `ft_strdup` + deteccion de duplicado. Sin `open()` (eso es S06A).

**Verify:** `tex_paths[i]` sin `\n` final; segunda NO -> error.

---

### T6 — Cableado en main.c

Tras `check_file`, propagando int. main <= 25 lineas.

---

### T7 — Prototipos publicos en cub3d.h

Solo los publicos (los static no).

---

### T8 — Makefile

Anade `parsing/parse_data.c` y `parsing/get_file_data.c` a SRC (sin `sources/`).

**Verify:** `make` sin warnings.

---

### T9 — Fixtures + DoD

No reutilices `test_basic.cub` (es 1 linea invalida; choca con SYNC2 "6 identificadores"). Crea:

- `valid.cub`: 6 identificadores + bloque de mapa pequeno.
- `dup_id.cub`: dos NO.
- `missing_id.cub`: falta uno.
- `crlf.cub`: terminaciones `\r\n`.
- `id_after_map.cub`: identificador tras linea de mapa.
- `empty.cub`: vacio (debe rechazarse en algun sitio — decide donde).
- ruta con espacios: `NO    ./tex.xpm`.

**Verify:** clasificacion correcta, norminette, valgrind clean en feliz Y en fallo.

---

### T10 — Commit

`feat(parsing): read .cub into memory and dispatch identifiers`

**Norma — reparto de funciones:** la cronograma asigna 7 funciones a S03A. Max 5 por archivo -> reparte 4/3 entre `parse_data.c` y `get_file_data.c`. Varias firmas de la cronograma estan al tope de 4 params; si texinfo vive dentro de data, pasa solo data y liberas un slot.

---

## PARTE 2 — S04A (tareas)

### T1 — Estructura del archivo

Crea `sources/parsing/fill_color_textures.c` (header, include). Usa `int`, no `bool` (`<stdbool.h>` no esta incluido y tocar el header compartido por un bool no compensa).

---

### T2 — Extraccion RGB + validacion

Split por `,` + validacion por token (solo digitos, sin signo/espacios, tope 3 digitos) + `ft_atoi` + rango [0,255]. Maneja `tab[0]==NULL` sin segfault.

**Verify:** acepta `220,100,0`; rechaza overflow, no-digito, !=3 tokens.

---

### T3 — Composicion del color

Compon el int `(R<<16)|(G<<8)|B`, guardalo en `floor_color`/`ceiling_color`. Duplicado F/C -> error.

---

### T4 — Conecta con el dispatcher

D3 rutea F/C aqui.

---

### T5 — Prototipo publico + entrada en Makefile

---

### T6 — Fixtures + DoD

Ademas de 999/abc/2-valores/4-valores/duplicado, anade los que marcan los quirks de ft_split/ft_atoi:

- `F 256,0,0` (frontera: 256 falla, 255 pasa)
- `F 220, 100, 0` (espacios interiores)
- `F -1,0,0` (negativo)
- `F 99999999999,0,0` (overflow)
- `F 220,100,0,,` (comas finales -> 3 tokens por el colapso)

**Verify:** todos dan error salvo el valido; norminette; valgrind clean (incl. input que falla).

---

### T7 — Commit

`feat(parsing): parse and validate F/C RGB colors`

---

## Funciones permitidas (verificadas en TU libft)

`get_next_line`, `ft_split`, `ft_atoi`, `ft_isdigit`, `ft_strdup`, `ft_substr`, `ft_strtrim`, `ft_strchr`, `ft_strncmp`, `ft_strlen`, `ft_free_strs` — todas existen.

`open`/`read`/`close`/`malloc`/`free`/`strerror` permitidas. Nada de `bool`, `stat`, `atoi`/`strdup` de libc.

---

## Riesgo residual

Con D0 resuelto (contrato con Rodrigo + `tex_paths[4]` + `int` + strip de `\n`/`\r`), el plan es implementable de principio a fin sin ciclo de rework. El unico riesgo que no es de codigo es el gate humano de D0: si defines el struct raiz por tu cuenta y choca con el de Rodrigo, hay rework en el merge — eso solo lo cierra hablar con el.
