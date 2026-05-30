# S02A — Plan de ejecucion (FINAL)

> `parsing/check_args.c` — validar extension `.cub`, detectar directorio, verificar existencia.
> Prerequisito: S01A done.

---

## Decisiones cerradas (D1-D5 + B2 + N1)

| ID | Decision |
|---|---|
| D1 | Retornos en `int` con `SUCCESS`/`FAILURE`. Sin `bool` ni `<stdbool.h>`. |
| D2 | `int check_file(char *arg)` — un solo parametro. Nada de `is_xpm_file` ni `bool cub`. Eso entra en S06A. |
| D3 | Orden de validacion: existencia -> tipo (dir/file) -> extension. |
| D4 | Deteccion de directorio sin `stat`: `open(arg, O_RDONLY)` -> fd valido -> `read(fd, &buf, 1)` -> si devuelve -1 y `errno == EISDIR`, es directorio. |
| D5 | Mensajes: `strerror(errno)` para errores de sistema (no existe, es dir); constante `ERR_FILE_NOT_CUB` para error logico de extension. |
| B2 | Capturar `errno` en `int saved_errno` inmediatamente despues del `read()`, antes de cualquier `close()`. Patron canonico C. |
| N1 | `read == -1 && errno != EISDIR` -> tratar como fichero legible (`return SUCCESS`). El parser en S03A lo pillara. Justificacion: YAGNI. |

---

## Tareas (T1-T10, orden estricto)

### T1 — Estructura del archivo

Crear `sources/parsing/check_args.c` con header 42. El directorio `parsing/` nace ahora.
`#include "cub3d.h"` (ya trae `fcntl`, `unistd`, `errno`, `string` — no anadir includes al header).

**Verify:** archivo existe, header 42 presente, include correcto.

---

### T2 — Constante de error en el header

Anadir en `includes/cub3d.h`, junto a `ERR_USAGE`:

```c
# define ERR_FILE_NOT_CUB "Not a .cub file"
```

**Verify:** constante accesible desde `check_args.c`.

---

### T3 — `static int is_cub_file(char *arg)` — extension .cub

Orden de operaciones obligatorio (B1):
1. `len = ft_strlen(arg);`
2. `if (len < 4) return (FAILURE);` — PRIMERO. Si calculas `arg + len - 4` con `len < 4` lees fuera del buffer (UB).
3. Comparar la cola: `ft_strncmp(arg + len - 4, ".cub", 4)`.

Edge cases cubiertos:
- `len < 4` -> KO
- `.CUB` mayusculas -> KO (estricto minusculas)
- `map.cub.txt` -> KO
- `.cub` solo -> OK
- `a.cubx` -> KO

**Verify mental:** `a.cub`->OK, `a.txt`->KO, `a.cubx`->KO, `.cub`->OK, longitud 2->KO.

---

### T4 — `static int is_readable_file(char *arg)` — existencia + directorio

Flujo con errno corregido:
1. `fd = open(arg, O_RDONLY);`
2. Si `fd == -1` -> `return (err_msg(arg, strerror(errno), FAILURE));` (errno fresco, no hay syscall en medio).
3. Declarar `char buf;` y hacer `read(fd, &buf, 1)`.
4. Si `read == -1`:
   - `int saved_errno = errno;` — capturar YA (B2).
   - Si `saved_errno == EISDIR` -> `close(fd)`, `return (err_msg(arg, strerror(saved_errno), FAILURE));`
   - Si `saved_errno != EISDIR` -> `close(fd)`, `return (SUCCESS);` (N1: YAGNI, S03A lo pilla).
5. `close(fd);` y `return (SUCCESS);`

Cuenta de variables: `fd` + `buf` + `saved_errno` = 3 (< 5).

**Verify:** `nonexistent.cub`->no-existe; directorio existente->EISDIR; `.cub` real->pasa. Sin fd colgando.

---

### T5 — `int check_file(char *arg)` — orquestador

Orden segun D3:
1. `is_readable_file(arg)` -> si falla, propagar `FAILURE` (err_msg ya se llamo dentro).
2. `is_cub_file(arg)` -> si falla, `return (err_msg(arg, ERR_FILE_NOT_CUB, FAILURE));`
3. Si todo OK -> `return (SUCCESS);`

Asimetria consciente (N2): errores de sistema se reportan donde nace el `errno`; error logico se reporta aqui. Justificacion para defensa lista.

**Verify:** retorna int, encaja con patron existente.

---

### T6 — Prototipo en `cub3d.h`

Anadir solo el publico:

```c
int	check_file(char *arg);
```

Las `static` no se declaran en el header.

**Verify:** prototipo anadido, nada mas tocado.

---

### T7 — Cableado en `main.c`

- Eliminar `(void)argv;`.
- Tras el check de `argc`, antes del `return (SUCCESS)`:

```c
if (check_file(argv[1]) != SUCCESS)
    return (FAILURE);
```

**Verify:** main <= 25 lineas, sin logica de validacion dentro.

---

### T8 — Makefile

En la variable `SRC` anadir `parsing/check_args.c` (sin `sources/` — la linea 22 ya hace `addprefix`).
No tocar ninguna regla: la linea 30 (`mkdir -p $(dir $@)`) ya crea `obj/parsing/` sola.

**Verify:** `make` compila sin warnings y genera `obj/parsing/check_args.o`.

---

### T9 — Definition of Done

Preparar fixture (B4):

```bash
mkdir -p maps/good
echo "NO ./textures/north.xpm" > maps/good/test_basic.cub
```

Luego correr en orden:

| Comando | stderr esperado | Exit |
|---|---|---|
| `./cub3D` | `Error\nUsage: ./cub3D <map.cub>` | 1 |
| `./cub3D nonexistent.cub` | `Error\nnonexistent.cub: No such file or directory` | 1 |
| `./cub3D docs/` | `Error\ndocs/: Is a directory` | 1 |
| `touch foo.txt && ./cub3D foo.txt` | `Error\nfoo.txt: Not a .cub file` | 1 |
| `./cub3D maps/good/test_basic.cub` | (nada) | 0 |

Verificar exit con `echo $?` tras cada uno. Luego:

```bash
norminette sources/parsing/check_args.c includes/cub3d.h
```

**Verify:** los 5 casos pasan, norminette limpia.

---

### T10 — Commit

```bash
git add sources/parsing/check_args.c sources/main.c includes/cub3d.h Makefile maps/good/test_basic.cub
git commit -m "feat(parsing): validate .cub argument (extension, dir, exists)"
```

Incluir el fixture en el commit (la regla: vive con su test).

---

## Lo que NO tocar

- D1-D5 y el truco `open->read->EISDIR`: correctos en Linux.
- 3 funciones en `check_args.c` (< 5 por archivo).
- `ft_strncmp` existe en libft.
- Includes ya presentes en `cub3d.h` — solo anadir `ERR_FILE_NOT_CUB` + prototipo.
- `(void)argv` se elimina en T7 (ahora si se usa).
