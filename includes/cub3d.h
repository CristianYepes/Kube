/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   cub3d.h                                            :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: cristian <cristian@student.42.fr>          +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/05/24 22:48:50 by cristian          #+#    #+#             */
/*   Updated: 2026/06/11 00:36:41 by cristian         ###   ########.fr       */
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

/*Raycasting*/
# define BLOCK 64
# define FOV 1.0471975512f

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
	float	x;
	float	y;
	float	angle;
	int		key_up;
	int		key_down;
	int		key_left;
	int		key_right;
	int		rotate_left;
	int		rotate_right;
}			t_player;

typedef struct s_ray
{
	float	angle;
	float	dir_x;
	float	dir_y;
	float	delta_x;
	float	delta_y;
	float	side_x;
	float	side_y;
	float	wall_dist;
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
	int			id_flags;
	/*Scene*/
	char		*tex_paths[4];
	int			floor_color;
	int			ceiling_color;
	char		**map;
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
/*INIT*/
void			init_game(t_data *data);
void			init_player(t_player *player);
/*RENDER*/
void			put_pixel(t_data *data, int x, int y, int color);
void			clear_image(t_data *data);
void			cast_rays(t_data *data);
int				game_loop(t_data *data);
/*MOVEMENT*/
int				key_press(int keycode, t_data *data);
int				key_release(int keycode, t_data *data);
void			move_player(t_player *p);
/*EXIT*/
void			exit_game(t_data *data);
int				close_window(t_data *data);
#endif
