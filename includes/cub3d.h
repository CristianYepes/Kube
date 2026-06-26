/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   cub3d.h                                            :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: rodrigo <rodrigo@student.42.fr>            +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/05/24 22:48:50 by cristian          #+#    #+#             */
/*   Updated: 2026/06/23 12:34:30 by rodrigo          ###   ########.fr       */
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
# include <sys/time.h>

/*Window*/
# define WIN_W 1280
# define WIN_H 720

/*movement*/
# define MOVE_SPEED 0.02
# define ROT_SPEED 0.03

/*Keycodes*/
# define KEY_M 109
# define KEY_W 119
# define KEY_A 97
# define KEY_S 115
# define KEY_D 100
# define KEY_LEFT 65361
# define KEY_RIGHT 65363
# define KEY_ESC 65307
# define KEY_SHOOT 65362
# define KEY_R 114

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
# define ERR_MISSING_COLOR "Missing floor/ceiling color"

/*render*/
# define TEX_SIZE 64
# define GUN_SIZE 900
# define GUN_FRAMES 4
# define FOG_MAX 6.0
# define FONT_SCALE 5

/*Bonus charset guard*/
# ifdef BONUS
#  define MAP_CHARS "0123DNSEW"
# else
#  define MAP_CHARS "01NSEW"
# endif

/*Doors*/
# define KEY_E 101
# define DOOR_CLOSED 'D'
# define DOOR_OPEN 'O'

/*Mod — enemy types*/
# define ENEMY_GRUNT 0
# define ENEMY_RUNNER 1
# define ENEMY_BOSS 2

/*Mod — enemy states*/
# define E_IDLE 0
# define E_CHASE 1
# define E_ATTACK 2
# define E_DEAD 3

/*Mod — weapon states*/
# define W_IDLE 0
# define W_FIRING 1

/*Mod — game states*/
# define G_PLAY 0
# define G_OVER 1
# define G_WIN 2

/*Mod — timers*/
# define FIRE_COOLDOWN 0.6
# define ATTACK_RATE 1.0
# define DEATH_TIME 0.4

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
	/*minimap*/
	int		minimap;
	int		rotate_left;
	int		rotate_right;
}			t_player;

typedef struct s_enemy
{
	double	pos_x;
	double	pos_y;
	double	distance;
	int		type;
	int		state;
	int		hp;
	double	timer;
	double	atk_timer;
}			t_enemy;

typedef struct s_weapon
{
	int		state;
	double	timer;
}			t_weapon;

typedef struct s_sprite
{
	double	pos_x;
	double	pos_y;
	double	distance;
	double	transform_x;
	double	transform_y;
	int		screen_x;
	int		size;
	double	anim_timer;
	int		frame_idx;
	int		type;
}			t_sprite;

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
	int		line_h;
	int		tex_idx;
	int		tex_x;
	int		is_door;
}			t_ray;

typedef struct s_data
{
	char			**file_lines;
	int				file_nb_lines;
	int				map_start;
	int				id_flags;
	int				map_height;
	int				map_width;
	char			*tex_paths[4];
	int				floor_color;
	int				ceiling_color;
	char			**map;
	int				*textures[4];
	void			*mlx;
	void			*win;
	t_img			img;
	double			*z_buffer;
	int				sprite_count;
	int				*sprite_tex[2];
	int				*sprite_tex2[2];
	struct timeval	last_time;
	t_sprite		*sprites;
	int				*gun_tex[GUN_FRAMES];
	int				gun_frame;
	int				gun_firing;
	double			gun_timer;
	int				mini_x;
	int				mini_y;
	int				*door_tex;
	double			dt;
	double			anim_clock;
	int				fire;
	t_enemy			*enemies;
	int				enemy_count;
	int				wave;
	int				player_hp;
	int				game_state;
	int				fog;
	t_weapon		weapon;
	unsigned int	seed;
	int				spawn_relax;
	int				last_spawn;
	double			spawn_x;
	double			spawn_y;
	char			spawn_dir;
	t_player		player;
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
void			set_ns(t_player *p, char c);
void			set_ew(t_player *p, char c);
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
int				*xpm_to_int_size(t_data *data, char *path, int size);
int				init_textures(t_data *data);
/*RENDER*/
void			put_pixel(t_data *data, int x, int y, int color);
void			cast_rays(t_data *data);
void			draw_wall_column(t_data *data, t_ray *ray, int x);
int				game_loop(t_data *data);
void			paint_floor_ceiling(t_data *data);
/*SPRITES*/
int				sprites_counter(char type, t_data *data);
void			init_sprites(char type, t_data *data);
int				init_sprites_data(t_data *data);
void			compute_sprite_distances(t_data *data);
void			sort_sprites(t_data *data);
void			render_sprites(t_data *data);
/*MOVEMENT*/
int				key_press(int keycode, t_data *data);
int				key_release(int keycode, t_data *data);
void			move_player(t_data *data);
void			rotate_player(t_player *p, double dir);
int				is_wall(t_data *data, double x, double y);
void			toggle_door(t_data *data);
# ifdef BONUS

int				key_press_bonus(int keycode, t_data *data);
int				mouse_tracker(int x, int y, t_data *data);
int				mouse_click(int button, int x, int y, t_data *data);

# endif

/*EXIT*/
void			exit_game(t_data *data);
void			destroy_game(t_data *data);
void			free_sprites(t_data *data);
void			free_shotgun(t_data *data);
int				close_window(t_data *data);
/*minimap*/
void			display_minimap(t_data *data);
void			draw_map2(t_data *data);
void			draw_square(int x, int y, int size, t_data *data);
void			draw_player(int x, int y, int size, t_data *data);
void			draw_sprite(int x, int y, int size, t_data *data);
/*mlx loop*/
void			loop(t_data *data);
/*Mod — simulation*/
void			update_sim(t_data *data);
void			spawn_wave(t_data *data);
void			update_enemies(t_data *data);
void			try_fire(t_data *data);
void			update_player_hp(t_data *data);
void			check_game_state(t_data *data);
unsigned int	lcg_next(unsigned int *seed);
int				count_spawn_cells(t_data *data);
int				pick_spawn_cell(t_data *data, int n, int *ox, int *oy);
int				has_los(t_data *data, double cx, double cy);
void			restart_game(t_data *data);
/*Mod — render*/
void			render_enemies(t_data *data);
void			render_weapon(t_data *data);
void			render_hud(t_data *data);
void			draw_text(t_data *data, char *s, int y, int color);
int				apply_fog(int color, double dist, int fog);
/*Shotgun*/
int				init_shotgun(t_data *data);
void			draw_shotgun(t_data *data);
void			tick_shotgun(t_data *data, double dt);
void			fire_shotgun(t_data *data);
#endif
