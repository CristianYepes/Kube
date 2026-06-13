NAME        = cub3D
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
				init/init_game.c \
				render/render_utils.c \
				render/raycasting.c \
				render/game_loop.c \
				movement/player.c \
				movement/input.c \
				exit/exit_game.c

SRCS        = $(addprefix $(SRC_PATH), $(SRC))

OBJ_PATH    = obj/
OBJS        = $(SRCS:$(SRC_PATH)%.c=$(OBJ_PATH)%.o)

all: $(MLX) $(LIBFT) $(NAME)

$(OBJ_PATH)%.o: $(SRC_PATH)%.c
	@mkdir -p $(dir $@)
	@echo "\033[0;33mCompiling $<...\033[0m"
	@$(CC) $(CFLAGS) -c $< -o $@ $(INC)

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
	@echo "\033[1;32mcub3D compiled successfully!\033[0m"

bonus: all

clean:
	@echo "\033[1;31mRemoving object files...\033[0m"
	@rm -rf $(OBJ_PATH)
	@[ -d $(LIBFT_PATH) ] && make -sC $(LIBFT_PATH) clean || true
	@[ -d $(MLX_PATH) ] && make -sC $(MLX_PATH) clean || true

fclean: clean
	@echo "\033[1;31mRemoving $(NAME)...\033[0m"
	@rm -f $(NAME)
	@[ -d $(LIBFT_PATH) ] && make -sC $(LIBFT_PATH) fclean || true

re: fclean all

.PHONY: all clean fclean re bonus
