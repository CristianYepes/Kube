/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   player.c                                           :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: rodrigo <rodrigo@student.42.fr>            +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/07 21:00:00 by cristian          #+#    #+#             */
/*   Updated: 2026/06/17 17:55:56 by rodrigo          ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "cub3d.h"

void	init_player(t_player *player)
{
	player->key_up = 0;
	player->key_down = 0;
	player->key_left = 0;
	player->key_right = 0;
	player->rotate_left = 0;
	player->rotate_right = 0;
}

static void	rotate_player(t_player *p, double dir)
{
	double	angle;
	double	old_dir_x;
	double	old_plane_x;

	angle = ROT_SPEED * dir;
	old_dir_x = p->dir_x;
	p->dir_x = p->dir_x * cos(angle) - p->dir_y * sin(angle);
	p->dir_y = old_dir_x * sin(angle) + p->dir_y * cos(angle);
	old_plane_x = p->plane_x;
	p->plane_x = p->plane_x * cos(angle) - p->plane_y * sin(angle);
	p->plane_y = old_plane_x * sin(angle) + p->plane_y * cos(angle);
}

void	move_player(t_player *p)
{
	if (p->rotate_left)
		rotate_player(p, -1);
	if (p->rotate_right)
		rotate_player(p, 1);
	if (p->key_up)
	{
		p->pos_x += p->dir_x * MOVE_SPEED;
		p->pos_y += p->dir_y * MOVE_SPEED;
	}
	if (p->key_down)
	{
		p->pos_x -= p->dir_x * MOVE_SPEED;
		p->pos_y -= p->dir_y * MOVE_SPEED;
	}
	if (p->key_left)
	{
		p->pos_x -= p->plane_x * MOVE_SPEED;
		p->pos_y -= p->plane_y * MOVE_SPEED;
	}
	if (p->key_right)
	{
		p->pos_x += p->plane_x * MOVE_SPEED;
		p->pos_y += p->plane_y * MOVE_SPEED;
	}
}
