# Builds cub3D_agent, a third binary of the game, for spec 002 (Jev plays cub3D_bonus).
# It compiles the deliverable's own sources, except the three files that sources/jev/
# replaces, and links the same libft and MiniLibX. The deliverable is never edited.
#
# Run it from the repo root: the maps name their textures relative to it.
#   make -C agent
#   ./agent/cub3D_agent maps/bonus/subject_map.cub 7

NAME     = cub3D_agent
CC       = cc
CFLAGS   = -Wall -Wextra -Werror -D BONUS
INC      = -I../includes -I../libft -I../minilibx-linux

LIBFT    = ../libft/libft.a
MLX      = ../minilibx-linux/libmlx.a

# The three translation units that sources/jev/ replaces.
REPLACED = ../sources/main.c \
           ../sources/mlx_loop_and_hook/mlx.c \
           ../sources/render/game_loop.c
# A wildcard is fine here: this is not the 42 Makefile. It also finds sources/jev/.
SRCS     = $(filter-out $(REPLACED), $(wildcard ../sources/*.c ../sources/*/*.c ../sources/*/*/*.c))
OBJS     = $(SRCS:../sources/%.c=obj/%.o)
HEADERS  = ../includes/cub3d.h $(wildcard ../sources/jev/*.h)

all: $(NAME)

$(NAME): $(OBJS) $(LIBFT) $(MLX)
	$(CC) $(CFLAGS) -o $@ $(OBJS) $(LIBFT) $(MLX) -lXext -lX11 -lm

obj/%.o: ../sources/%.c $(HEADERS)
	@mkdir -p $(dir $@)
	$(CC) $(CFLAGS) $(INC) -c $< -o $@

# The deliverable's own Makefile builds libft and the pinned MiniLibX (it clones it at the
# commit it pins). FORCE makes this ask every time. Both libraries are rebuilt only if they
# changed, and make reads their dates again afterwards, so the binary relinks only then.
$(LIBFT): FORCE
	@$(MAKE) -s -C .. bonus

$(MLX): $(LIBFT)

FORCE:

clean:
	rm -rf obj

fclean: clean
	rm -f $(NAME)

.PHONY: all clean fclean FORCE
