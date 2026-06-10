makefile:

Explícame con tus palabras qué hace esa línea de OBJS. ¿Qué transformación está haciendo sobre SRCS?

¿Qué significan $< y $@ en esa regla? Si no lo sabes, búscalo en man make o en una referencia de Makefile. Tienes que saberlo, te lo van a preguntar

En tu Makefile de fractol, el target $(MLX) dependía de $(MLX_PATH). ¿Qué pasa si la carpeta minilibx-linux/ ya existe pero está vacía? ¿Y si tiene los .c pero no el libmlx.a? Piensa qué ejecuta Make en cada caso

El .gitignore debe incluir minilibx-linux/ y obj/ y *.a y cub3D.
Cuando empieces a tener subcarpetas en sources/ (parsing, render…), añadirás líneas al SRC con su ruta relativa, ej: parsing/check_args.c

Bloque A — Sobre el patrón de OBJS

¿Por qué $(SRCS:$(SRC_PATH)%.c=$(OBJ_PATH)%.o) y no $(SRCS:$(SRC_PATH)%=$(OBJ_PATH)%.o)? ¿Qué cambia en el nombre final del .o?
Si tengo sources/parsing/check_args.c en SRC, ¿cómo se llamará exactamente su archivo objeto?
¿Qué pasa si en SRC pongo un archivo con la ruta mal escrita (ej: parsing/check_args sin el .c)? ¿Make me avisa o falla silenciosamente?

Bloque B — Sobre las reglas de compilación

La regla $(OBJ_PATH)%.o: $(SRC_PATH)%.c — ¿qué significa el % y por qué tiene que aparecer en los dos lados?
¿Qué hace @mkdir -p $(dir $@) y por qué es necesario? ¿Qué pasa si lo quito?
¿Qué son $< y $@ en $(CC) $(CFLAGS) -c $< -o $@ $(INC)? ¿A qué se sustituyen exactamente?
¿Por qué los comandos empiezan con @? ¿Qué pasa si lo quito?

Bloque C — Sobre la MLX y el clonado

¿Por qué la regla $(MLX_PATH): no tiene prerequisitos? ¿Cuándo se ejecuta?
Si la carpeta minilibx-linux/ ya existe pero está vacía (un clone interrumpido), ¿qué hace Make la próxima vez que ejecuto make? ¿Vuelve a clonar? ¿Falla?
¿Qué hace --depth 1 en el git clone? ¿Por qué es buena idea?
¿Qué diferencia hay entre make -sC carpeta y make -C carpeta? ¿Por qué uso -s aquí?

Bloque D — Sobre el linking final

En la línea de linking, ¿por qué el orden es $(OBJS) $(LIBFT) $(MLX) y no al revés? ¿Importa el orden?
¿Qué hacen -lXext, -lX11, -lm? ¿Por qué los necesito?
¿Por qué -lm y no -lmath?

Bloque E — Sobre clean / fclean

¿Qué hace exactamente [ -d $(MLX_PATH) ] && make -sC $(MLX_PATH) clean || true? Tradúcelo a lenguaje humano paso a paso.
¿Por qué necesito el || true al final? ¿Qué pasa sin él?
¿Por qué clean borra obj/ pero fclean borra $(NAME)? ¿Cuál es la diferencia conceptual entre ambos?
Cuando hago make clean en mi proyecto, también se hace clean dentro de libft y MLX. ¿Es eso lo correcto o estoy borrando cosas que después tendré que recompilar inútilmente?

Bloque F — Sobre .PHONY y casos límite

¿Qué hace .PHONY? ¿Qué pasaría si tengo un archivo llamado clean en mi carpeta y no lo declaro como phony?
¿Por qué bonus: all por ahora? ¿Qué tendrá que cambiar cuando empiece los bonus oficiales?
¿Qué hace make re? ¿Por qué es útil tenerlo?

Bloque G — Sobre relinking y eficiencia

Si modifico sources/main.c y ejecuto make, ¿qué recompila Make? ¿Solo main.o y relinka, o recompila todo?
Si modifico includes/cub3d.h, ¿qué recompila Make? ¿Por qué? ¿Es un problema?
La regla $(LIBFT): no tiene prerequisitos. ¿Significa eso que solo se ejecuta una vez? ¿Qué pasa si modifico libft_c/ft_strlen.c?

Bloque H — Pregunta trampa de defensa

Si el evaluador hace esto en orden, ¿qué pasa en cada paso?

    git clone <tu_repo>
    cd <tu_repo>
    make
    make clean
    rm -rf minilibx-linux/
    make clean
    make re



¿Por qué imprimes los errores a stderr (fd 2) y no a stdout (fd 1)? ¿Qué diferencia hay y por qué importa?"


Pregunta para defensa
Quiero que pienses dos cosas mientras esperas:
1. ¿Por qué imprimes a stderr (fd 2) y no a stdout (fd 1)?
Esto SIEMPRE cae en defensa. Apunta la respuesta en preguntas.md antes de seguir.
Pista: piensa en lo que hace un usuario con ./cub3D 2>/tmp/err. ¿Por qué existe esa redirección? ¿Qué problema resuelve separar errores y salida normal?
2. ¿Por qué tu err_msg devuelve un int?
Podría ser void. ¿Qué ganas devolviendo int?
Pista: mira tu propio main.c:


tema bits:

Qué es un color en int?

  Un int tiene 32 bits. MiniLibX espera el color en
  este formato:

  bits:  31......24  23......16  15.......8
  7........0
         [  vacío  ] [   ROJO  ] [  VERDE  ] [  AZUL
   ]

  Si tienes R=220, G=100, B=0, quieres un solo int
  que sea:

  00000000  11011100  01100100  00000000
            R=220     G=100     B=0

  ---
  ¿Qué hace << (bit shift)?

  Mueve los bits a la izquierda N posiciones:

  ft_atoi("220") = 220       → 00000000 00000000
  00000000 11011100
  220 << 16                   → 00000000 11011100
  00000000 00000000
                                         ^^^^^^^^ ←
  R ya está en su sitio

  ft_atoi("100") = 100       → 00000000 00000000
  00000000 01100100
  100 << 8                    → 00000000 00000000
  01100100 00000000

  ^^^^^^^^ ← G en su sitio

  ft_atoi("0") = 0           → 00000000 00000000
  00000000 00000000
                                ← B ya está en su
  sitio (no necesita shift)

  ---
  ¿Qué hace | (OR)?

  Combina los tres en uno solo — cada uno ocupa su
  "franja" sin pisar al otro:

  (220 << 16) | (100 << 8) | 0  =  00000000 11011100
  01100100 00000000
                                              R
    G        B

