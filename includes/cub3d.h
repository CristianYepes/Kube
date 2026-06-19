/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   cub3d.h                                            :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: cristian <cristian@student.42.fr>          +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/05/24 22:48:50 by cristian          #+#    #+#             */
/*   Updated: 2026/06/18 20:51:56 by cristian         ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#ifndef CUB3D_H
# define CUB3D_H
# include "libft.h"
# include "mlx.h"
# include <errno.h>
# include <fcntl.h>
# include <math.h>
# include <stdio.h>
# include <stdlib.h>
# include <string.h>
# include <unistd.h>

/*Window*/
# define WIN_W 1280
# define WIN_H 720

/*movement*/
# define MOVE_SPEED 0.05
# define ROT_SPEED 0.03

/*Keycodes*/
# define KEY_W 119
# define KEY_A 97
# define KEY_S 115
# define KEY_D 100
# define KEY_LEFT 65361
# define KEY_RIGHT 65363
# define KEY_ESC 65307

/*Return codes*/
# define SUCCESS 0
# define FAILURE 1
# define ERR 2
# define BREAK 3
# define CONTINUE 4

/*Line Types*/
# define TYPE_EMPTY 0
# define TYPE_TEXTURE 1
# define TYPE_COLOR 2
# define TYPE_MAP 3

/*Texture Index*/
# define NORTH 0
# define SOUTH 1
# define WEST 2
# define EAST 3

/*Error strings*/
# define ERR_USAGE "Usage: ./cub3D <map.cub>"
# define ERR_FILE_NOT_CUB "Not a .cub file"
# define ERR_EMPTY_FILE "Empty file"
# define ERR_DUPLICATE_TEXTURE "Duplicate Texture"
# define ERR_EMPTY_PATH "Empty path"
# define ERR_DUPLICATE_COLOR "Duplicate color"
# define ERR_INVALID_COLOR "Invalid color format"
# define ERR_ID_AFTER_MAP "Map must be last"
# define ERR_MAP_MISSING "Map not found"
# define ERR_EMPTY_LINE_IN_MAP "Empty line in map"
# define ERR_INVALID_CHAR "Invalid character in map"
# define ERR_PLAYER_COUNT "Map must have exactly one player"
# define ERR_MAP_NOT_CLOSED "Map is not closed"
# define ERR_MISSING_ID "Missing texture path"
# define ERR_TEX_NOT_XPM "Texture is not a .xpm file"

/*render*/
# define TEX_SIZE 64

/*Structs*/
typedef struct s_img
{
	void	*img;
	char	*addr;
	int		bpp;
	int		size_line;
	int		endian;
}			t_img;

typedef struct s_player
{
	double	pos_x;
	double	pos_y;
	double	dir_x;
	double	dir_y;
	double	plane_x;
	double	plane_y;
	int		key_up;
	int		key_down;
	int		key_left;
	int		key_right;
	int		rotate_left;
	int		rotate_right;
}			t_player;

typedef struct s_ray
{
	double	dir_x;
	double	dir_y;
	double	delta_x;
	double	delta_y;
	double	side_x;
	double	side_y;
	double	wall_dist;
	int		map_x;
	int		map_y;
	int		step_x;
	int		step_y;
	int		side;
	int		hit;
}			t_ray;

typedef struct s_data
{
	/*Parsing*/
	char		**file_lines;
	int			file_nb_lines;
	int			map_start;
	int			id_flags;
	int			map_height;
	int			map_width;
	/*Scene*/
	char		*tex_paths[4];
	int			floor_color;
	int			ceiling_color;
	char		**map;
	int			*textures[4];
	/*MLX*/
	void		*mlx;
	void		*win;
	t_img		img;
	/*Game*/
	t_player	player;
}				t_data;

/*ERROR*/
int				err_msg(char *detail, char *str, int code);
/*PARSING*/
int				check_file(char *arg);
int				parse_memory(char *path, t_data *data);
int				get_file_data(t_data *data);
int				fill_color_textures(char *line, t_data *data);
int				create_map(t_data *data);
int				parsing(char *path, t_data *data);
int				check_map(t_data *data);
int				check_map_borders(t_data *data);
int				check_textures(t_data *data);
/*PARSING UTILS*/
int				is_a_white_space(char c);
char			*skip_spaces(char *str);
void			free_file_lines(t_data *data);
void			free_parsing(t_data *data);
int				find_biggest_len(t_data *data, int start, int end);
/*INIT*/
int				init_game(t_data *data);
void			init_player(t_player *player);
int				*xpm_to_int(t_data *data, char *path);
int				init_textures(t_data *data);
/*RENDER*/
void			put_pixel(t_data *data, int x, int y, int color);
void			cast_rays(t_data *data);
int				game_loop(t_data *data);
void			paint_floor_ceiling(t_data *data);
/*MOVEMENT*/
int				key_press(int keycode, t_data *data);
int				key_release(int keycode, t_data *data);
void			move_player(t_player *p);
/*EXIT*/
void			exit_game(t_data *data);
int				close_window(t_data *data);
#endif
