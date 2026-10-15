/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   player.c                                           :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: rodrigo <rodrigo@student.42.fr>            +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/07 21:00:00 by cristian          #+#    #+#             */
/*   Updated: 2026/06/23 17:23:05 by rodrigo          ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "cub3d.h"

void	init_player(t_player *player)
{
	player->minimap = 1;
	player->key_up = 0;
	player->key_down = 0;
	player->key_left = 0;
	player->key_right = 0;
	player->rotate_left = 0;
	player->rotate_right = 0;
}

void	rotate_player(t_player *p, double angle)
{
	double	old_dir_x;
	double	old_plane_x;

	old_dir_x = p->dir_x;
	p->dir_x = p->dir_x * cos(angle) - p->dir_y * sin(angle);
	p->dir_y = old_dir_x * sin(angle) + p->dir_y * cos(angle);
	old_plane_x = p->plane_x;
	p->plane_x = p->plane_x * cos(angle) - p->plane_y * sin(angle);
	p->plane_y = old_plane_x * sin(angle) + p->plane_y * cos(angle);
}

int	is_wall(t_data *data, double x, double y)
{
	char	c;

	if (x < 0 || y < 0 || (int)y >= data->map_height
		|| (int)x >= data->map_width)
		return (1);
	c = data->map[(int)y][(int)x];
	return (c == '1' || c == DOOR_CLOSED);
}

static void	try_move(t_data *data, double dx, double dy)
{
	t_player	*p;

	p = &data->player;
	if (!is_wall(data, p->pos_x + dx, p->pos_y))
		p->pos_x += dx;
	if (!is_wall(data, p->pos_x, p->pos_y + dy))
		p->pos_y += dy;
}

/*
** Strafing goes along the unit vector to the right of dir, (-dir_y, dir_x).
** plane points the same way but is 0.66 long, since it sets the field of view,
** so strafing along it was a third slower than walking.
*/
void	move_player(t_data *data)
{
	t_player	*p;
	double		step;
	double		turn;

	p = &data->player;
	step = MOVE_SPEED * data->dt;
	turn = ROT_SPEED * data->dt;
	if (p->rotate_left)
		rotate_player(p, -turn);
	if (p->rotate_right)
		rotate_player(p, turn);
	if (p->key_up)
		try_move(data, p->dir_x * step, p->dir_y * step);
	if (p->key_down)
		try_move(data, -p->dir_x * step, -p->dir_y * step);
	if (p->key_left)
		try_move(data, p->dir_y * step, -p->dir_x * step);
	if (p->key_right)
		try_move(data, -p->dir_y * step, p->dir_x * step);
}
