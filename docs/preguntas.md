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
