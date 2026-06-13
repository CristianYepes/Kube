# "ROMPE MI CÓDIGO" — Protocolo adversarial para C (42)

**Trigger:** digo "rompe mi código" antes de commitear.

**Filosofía:** no verificas que funciona — intentas demostrar que FALLA. No lees el plan. Lees el código y lo atacas.

---

## PASS 1 — ASESINO DE MEMORIA

Para cada función en los archivos tocados:

1. Identificar TODA alocación: `malloc`, `ft_split`, `ft_strtrim`, `ft_strdup`, `ft_strjoin`, `ft_substr`, `ft_itoa`, `ft_calloc`, `get_next_line`
2. Para CADA alocación, trazar TODOS los `return` posibles desde ese punto hacia abajo
3. Preguntas:
   - ¿Hay `free` en CADA path? (incluidos returns de error tempranos)
   - ¿Hay NULL check justo después?
   - ¿Se usa después de liberarlo?
   - ¿Se libera dos veces en algún path?

---

## PASS 2 — DEMONIO DE INPUTS

Para cada función que recibe datos del fichero .cub:

1. Definir la GRAMÁTICA EXACTA de lo que debería aceptar
2. Generar inputs JUSTO FUERA de esa gramática:
   - Vacío / solo whitespace / solo newline
   - Delimitador repetido / ausente / al borde (`,,value`, `value,,`, `val,,val`)
   - Espacios donde no deberían estar (antes del ID, entre número y coma)
   - Frontera numérica: -1, 0, 255, 256, 9999, 0255
   - Longitud máxima +1 del campo
   - Tipo inesperado: letras donde van dígitos, dígitos donde va path
3. Para cada input hostil: TRAZAR ejecución en el código → ¿crash, leak, o acepta lo que no debe?

---

## PASS 3 — ABOGADO DE CONTRATOS

Para cada función externa llamada (libft, libc, mlx):

1. Leer su IMPLEMENTACIÓN REAL en el repo (no lo que crees que hace)
2. Identificar edge cases del código fuente:
   - ¿Colapsa delimitadores? ¿Devuelve string vacío o NULL? ¿Envuelve en overflow?
3. ¿El código que la llama MANEJA todos esos edge cases?
4. Para funciones propias: ¿el caller y la función acuerdan en qué significa el retorno? (0=éxito vs 0=falso)

---

## PASS 4 — SABOTEADOR LÓGICO

Para cada condicional, bucle y variable:

1. ¿Alguna variable se LEE sin inicializar en algún path? (if sin else que asigne)
2. ¿Algún bucle con off-by-one? (`<` vs `<=`, índice base)
3. ¿Alguna precedencia de operador mal? (`!ptr != NULL`, shifts vs comparación)
4. ¿Alguna cadena de `if` donde ninguno matchea y la variable queda sin valor?
5. ¿Algún `return` dentro de un bucle que corta la iteración prematuramente?

---

## PASS 5 — POLICÍA DE NORMA

1. **Norminette:** 25 líneas/función, 5 vars, 80 cols, 4 params, 5 funciones/archivo, sin `for`/`switch`/`do-while`/`goto`
2. **Subject:** solo funciones permitidas (Ch. V), formato de error exacto (`"Error\n"` + mensaje a stderr)
3. **Includes:** ¿todo lo usado está incluido? ¿Todo lo incluido se usa?
4. **Defines:** ¿todo define referenciado existe? ¿La firma del prototipo coincide con la función?

---

## Output

Nunca digo "se ve bien". Solo entrego:
- **BUGS CONFIRMADOS:** archivo:línea + input que lo rompe + qué pasa
- **SOSPECHOSOS:** archivo:línea + razonamiento de por qué podría fallar

---

## Ejecución

- **Cambio pequeño** (1-2 archivos): las 5 passes inline
- **Cambio grande** (milestone, merge, nueva fase): agentes en paralelo, uno por pass, cada uno con instrucciones de atacar sin piedad
