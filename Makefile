NAME        = cub3D
NAME_BONUS  = cub3D_bonus
CC          = gcc
CFLAGS      = -Wall -Wextra -Werror

LIBFT_PATH  = libft/
LIBFT_NAME  = libft.a
LIBFT       = $(LIBFT_PATH)$(LIBFT_NAME)

MLX_PATH    = minilibx-linux/
MLX_NAME    = libmlx.a
MLX         = $(MLX_PATH)$(MLX_NAME)
MLX_REPO    = https://github.com/42Paris/minilibx-linux.git

INC         = -I ./includes/ \
              -I ./$(LIBFT_PATH) \
              -I ./$(MLX_PATH)

SRC_PATH    = sources/
SRC         =	main.c \
				error.c \
				parsing/check_args.c \
				parsing/get_file_data.c \
				parsing/parsing_data.c \
				parsing/fill_color_textures.c \
				parsing/parsing_utils.c \
				parsing/create_game_map.c \
				parsing/check_map.c \
				parsing/check_map_borders.c \
				parsing/check_textures.c \
				init/init_game.c \
				init/init_textures.c \
				render/render_utils.c \
				render/raycasting.c \
				render/game_loop.c \
				render/textures.c \
				render/floor_ceeling.c \
				render/draw_wall.c \
				movement/player.c \
				movement/input.c \
				exit/exit_game.c \
				exit/free_bonus.c \
				mlx_loop_and_hook/mlx.c

BONUS_SRC   =	render/minimap.c \
				render/minimap_2.c \
				render/sprites.c \
				render/render_sprites.c \
				render/shotgun.c \
				render/shotgun_draw.c \
				init/init_sprites.c \
				movement/input_bonus.c \
				movement/doors.c \
				bonus/mod/sim.c \
				bonus/render/enemy_render.c \
				bonus/render/weapon.c \
				bonus/render/hud.c

SRCS        = $(addprefix $(SRC_PATH), $(SRC))
BONUS_SRCS  = $(addprefix $(SRC_PATH), $(BONUS_SRC))

OBJ_PATH    = obj/
OBJ_B_PATH  = obj_bonus/
OBJS        = $(SRCS:$(SRC_PATH)%.c=$(OBJ_PATH)%.o)
OBJS_BONUS  = $(SRCS:$(SRC_PATH)%.c=$(OBJ_B_PATH)%.o) \
              $(BONUS_SRCS:$(SRC_PATH)%.c=$(OBJ_B_PATH)%.o)

all: $(MLX) $(LIBFT) $(NAME)

$(OBJ_PATH)%.o: $(SRC_PATH)%.c
	@mkdir -p $(dir $@)
	@echo "\033[0;33mCompiling $<...\033[0m"
	@$(CC) $(CFLAGS) -c $< -o $@ $(INC)

$(OBJ_B_PATH)%.o: $(SRC_PATH)%.c
	@mkdir -p $(dir $@)
	@echo "\033[0;33mCompiling (bonus) $<...\033[0m"
	@$(CC) $(CFLAGS) -D BONUS -c $< -o $@ $(INC)

$(MLX_PATH):
	@echo "\033[1;34mCloning MiniLibX...\033[0m"
	@git clone --depth 1 $(MLX_REPO) $(MLX_PATH)

$(MLX): $(MLX_PATH)
	@echo "\033[1;34mBuilding MiniLibX...\033[0m"
	@make -sC $(MLX_PATH)

$(LIBFT):
	@echo "\033[1;34mBuilding libft...\033[0m"
	@make -sC $(LIBFT_PATH)

$(NAME): $(OBJS)
	@echo "\033[1;34mLinking $(NAME)...\033[0m"
	@$(CC) $(CFLAGS) -o $(NAME) $(OBJS) $(LIBFT) $(MLX) -lXext -lX11 -lm
	@echo "\033[1;32m$(NAME) compiled successfully!\033[0m"

$(NAME_BONUS): $(OBJS_BONUS)
	@echo "\033[1;34mLinking $(NAME_BONUS)...\033[0m"
	@$(CC) $(CFLAGS) -o $(NAME_BONUS) $(OBJS_BONUS) $(LIBFT) $(MLX) -lXext -lX11 -lm
	@echo "\033[1;32m$(NAME_BONUS) compiled successfully!\033[0m"

bonus: $(MLX) $(LIBFT) $(NAME_BONUS)

clean:
	@echo "\033[1;31mRemoving object files...\033[0m"
	@rm -rf $(OBJ_PATH) $(OBJ_B_PATH)
	@[ -d $(LIBFT_PATH) ] && make -sC $(LIBFT_PATH) clean || true
	@[ -d $(MLX_PATH) ] && make -sC $(MLX_PATH) clean || true

fclean: clean
	@echo "\033[1;31mRemoving executables...\033[0m"
	@rm -f $(NAME) $(NAME_BONUS)
	@[ -d $(LIBFT_PATH) ] && make -sC $(LIBFT_PATH) fclean || true

re: fclean all

.PHONY: all clean fclean re bonus
