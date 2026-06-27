---
name: contexto
description: Onboarding adversarial de contexto para el proyecto cub3D, antes de planificar, mergear o implementar. Usalo al empezar una sesion o al reorientarse. Recoge el estado real (git/ramas/commits, la rama del companero inspeccionada aparte, cronograma+roadmap+plan activo), reconcilia los docs con el codigo, INTENTA ROMPER el codigo cada vez (postura adversarial, traza ejecucion, lee la libft de la que dependa) y termina confirmando la posicion real y proponiendo siguientes pasos SIN implementar. Acepta foco opcional (un paso SXXX o un area como "merge"/"texturas").
---

# /contexto — Onboarding adversarial de cub3D

**Mision:** reconstruir el contexto COMPLETO del proyecto y dejar a Persona A lista
para decidir. Flujo de SOLO lectura/analisis: **no edites ni implementes**. Postura
por defecto: **adversarial** — no compruebas que el codigo funciona, intentas
DEMOSTRAR que falla. Termina proponiendo y esperando el OK del usuario.

## Principios (no negociables)
- **Senior socratico**: nunca escribas funciones completas; guia con preguntas.
- **Norma 42** (25 lineas/func · 5 vars · 80 cols · 4 params · 5 func/archivo) y
  **subject Cap. V** (solo funciones permitidas; `atoi`/`strdup`/`stat`/`sprintf`... prohibidas).
- **Compilar / valgrind / ejecutar: SOLO el usuario en Linux** (MLX-linux + X11). Tu
  estas en mac: solo `norminette` y analisis estatico. **Nunca compiles ni metas la MLX de mac.**
- **Scope locked**: mandatory + 5 bonus oficiales. `docs/preguntas.md`: contexto, **no lo respondas**.
- **Pareja**: A = parser/args/input/minimap/puertas · B (Rodrigo) =
  init/render/raycasting/texturas/raton/sprites. Merges **preservando la autoria de Rodrigo**.
- **VERIFICA, no asumas**: cada afirmacion (existe el fichero, la funcion esta en libft,
  el fixture dispara ese error, el merge da conflicto) se comprueba con una herramienta.

## Fase 1 — Git: la verdad del estado (primero)
- `git branch --show-current` · `git status --short` · `git fetch origin`.
- Tu trabajo sin integrar: `git log --oneline origin/dev..HEAD`.
- Ramas clave y divergencias: tu rama (A), `dev` (integracion), rama(s) de Rodrigo
  (`raycasting*`, B). `git log --oneline -5 <rama>` de cada una.
- Merges pendientes: orden y conflictos previstos con
  `git merge-tree --write-tree --name-only <ramaA> <ramaB>` (no toca nada).
- Lee los **mensajes** de commit del companero: "WIP", "sin implementar", "creacion
  de X sin..." = trabajo a medias que NO se mergea tal cual.

## Fase 2 — La rama del companero, sin tocarla (si hay divergencia con el lado B)
- Inspeccionala SIN checkout y sin tocar su working tree, extrayendola a /tmp:
  `git archive <rama-B> sources includes Makefile | tar -x -C /tmp/ladoB`
- `norminette /tmp/ladoB/sources /tmp/ladoB/includes` -> pasa la norma? cuantos errores?
- Lee su codigo nuevo y juzga que esta **completo vs a medias** (no te fies del
  mensaje de commit; miralo). Origen de un fichero suyo: `git log --oneline <rama-B> -- <fichero>`.
- Objetivo: saber que de su rama es mergeable ya y que hay que completar/arreglar.

## Fase 3 — Documentos: lee `docs/` a secas (descubre, NO asumas nombres)
- **Lista primero TODO lo que hay**: `ls docs/`. No hardcodees nombres de fase —
  los planes cambian con el paso (el plan de la fase 5 no sirve en la fase 8).
- Estables (leelos por su rol, no cambian de nombre): `subject.md` (permisos Cap. V +
  reglas de mapa) · `cronograma.md` (tabla -> posicion) · `roadmap.md` (indice + la
  seccion del paso actual).
- **Plan(es) activo(s): eligelos por el paso REAL** (el que salio en la Fase 1), no por
  un nombre fijo. De los `plan_*.md` que listaste, lee ENTERO solo el que cubre el paso
  en curso (mas el de integracion/merge si hay uno en marcha, y el del companero si toca
  integrar). **Ignora los planes de pasos ya cerrados — son ruido.**
- Regla de coste: indices y solo el detalle relevante; nunca vuelques docs viejos.

## Fase 4 — Reconciliar docs <-> codigo (la tabla MIENTE a veces)
- Fija la posicion REAL por commits y codigo, no por la tabla (suele ir por detras).
- Senala TODA desincronizacion: el plan dice X y el codigo hace Y; la tabla marca el
  paso N pero los commits llegan a M; el modelo del plan (p.ej. angular) vs el header
  real (p.ej. vectorial); un leak "marcado" que sigue abierto.

## Fase 5 — Intenta ROMPER el codigo (cada vez, postura adversarial)
- Aplica el protocolo adversarial del repo si existe (`docs/ROMPE_MI_CODIGO.md`):
  5 passes (memoria · inputs · contratos · logica · norma). No verificas que va;
  buscas el input que lo tumba.
- **Lee la libft de la que dependa** el codigo bajo analisis (`ft_split`, `ft_strtrim`,
  `get_next_line`, `ft_atoi`...). El bug casi siempre esta en como se USA libft, no en
  libft. Ejemplos reales de este repo: `ft_split` colapsa delimitadores consecutivos;
  GNL devuelve la linea CON `\n` (y la ultima quiza sin); `ft_strtrim` ya hace malloc.
- **TRAZA la ejecucion** de cada camino sospechoso a mano (entrada hostil -> que pasa
  linea a linea), no te limites a leerlo. Confirma cada bug con el input que lo rompe.
- `norminette sources/ includes/` (corre en mac). **No compiles.**
- Entrega: **BUGS CONFIRMADOS** (`fichero:linea` + input + que pasa) y **SOSPECHOSOS**.

## Fase 6 — Salida: confirmar y proponer (NO implementar)
Conciso:
1. **Posicion real:** "Estas en SXXX (Fase FY). Hecho: ... Pendiente: ...". Si difiere de
   la tabla, dilo.
2. **Ramas / merges:** que hay en dev, que falta integrar, conflictos previstos.
3. **Banderas:** bugs confirmados + sospechosos + desincronizaciones docs<->codigo.
4. **Siguientes pasos** (1-3 opciones con su porque). Ubica donde estas en el ciclo:
   contexto -> plan -> merge -> plan de implementacion -> programar -> merge a dev.
5. Termina con UNA pregunta de arranque y **espera el OK**. No edites ni implementes.

## Foco opcional
Con argumento (`/contexto S07A`, `/contexto merge`, `/contexto texturas`), prioriza ese
paso/area en las fases 3-6, pero nunca te saltes la Fase 1.

## Checklist de inputs (no cierres el contexto sin tocar los que apliquen)
- [ ] git: tu rama + `dev` + rama(s) de Rodrigo, con divergencias y conflictos previstos
- [ ] rama del companero extraida a /tmp + norminette + leida (si hay integracion)
- [ ] `ls docs/` hecho · subject · cronograma · roadmap · plan(es) del paso ACTUAL (no de pasos cerrados)
- [ ] codigo nuevo desde el ultimo merge: leido **y atacado**
- [ ] libft relevante leida (si el comportamiento del codigo depende de ella)
- [ ] hechos verificados con herramienta (ficheros existen, funciones en libft, fixtures disparan su error)
- [ ] `norminette` ejecutada
