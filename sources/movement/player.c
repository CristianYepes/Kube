/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   player.c                                           :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: cristian <cristian@student.42.fr>          +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/07 21:00:00 by cristian          #+#    #+#             */
/*   Updated: 2026/06/07 21:00:00 by cristian         ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "cub3d.h"

void	init_player(t_player *player)
{
	player->x = WIN_W / 2;
	player->y = WIN_H / 2;
	player->angle = M_PI / 2;
	player->key_up = 0;
	player->key_down = 0;
	player->key_left = 0;
	player->key_right = 0;
	player->rotate_left = 0;
	player->rotate_right = 0;
}

static void	rotate_player(t_player *p)
{
	float	angle_speed;

	angle_speed = 0.03f;
	if (p->rotate_left)
		p->angle -= angle_speed;
	if (p->rotate_right)
		p->angle += angle_speed;
	if (p->angle > 2 * M_PI)
		p->angle = 0;
	if (p->angle < 0)
		p->angle = 2 * M_PI;
}

static void	move_forward_back(t_player *p, float cos_a, float sin_a)
{
	int	speed;

	speed = 2;
	if (p->key_up)
	{
		p->x += cos_a * speed;
		p->y += sin_a * speed;
	}
	if (p->key_down)
	{
		p->x -= cos_a * speed;
		p->y -= sin_a * speed;
	}
}

static void	move_strafe(t_player *p, float cos_a, float sin_a)
{
	int	speed;

	speed = 2;
	if (p->key_left)
	{
		p->x += sin_a * speed;
		p->y -= cos_a * speed;
	}
	if (p->key_right)
	{
		p->x -= sin_a * speed;
		p->y += cos_a * speed;
	}
}

void	move_player(t_player *p)
{
	float	cos_a;
	float	sin_a;

	cos_a = cos(p->angle);
	sin_a = sin(p->angle);
	rotate_player(p);
	move_forward_back(p, cos_a, sin_a);
	move_strafe(p, cos_a, sin_a);
}
