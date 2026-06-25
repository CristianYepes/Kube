/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   combat.c                                           :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: cristian <cristian@student.42.fr>          +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/24 14:00:00 by cristian          #+#    #+#             */
/*   Updated: 2026/06/24 14:00:00 by cristian         ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "cub3d.h"

static int	hitscan_hit(t_data *data, t_enemy *e)
{
	double	dx;
	double	dy;
	double	dot;
	double	perp;

	dx = e->pos_x - data->player.pos_x;
	dy = e->pos_y - data->player.pos_y;
	dot = dx * data->player.dir_x + dy * data->player.dir_y;
	if (dot < 0)
		return (0);
	perp = fabs(dx * data->player.dir_y - dy * data->player.dir_x);
	if (perp < 0.5 && dot < 10.0 && has_los(data, e->pos_x, e->pos_y))
		return (1);
	return (0);
}

static void	kill_enemy(t_data *data, int idx)
{
	int	last;

	last = data->enemy_count - 1;
	if (idx < last)
		data->enemies[idx] = data->enemies[last];
	data->enemy_count--;
}

static int	find_target(t_data *data)
{
	int		i;
	double	best_d;
	int		best_i;
	double	d;

	best_d = 1e30;
	best_i = -1;
	i = -1;
	while (++i < data->enemy_count)
	{
		if (data->enemies[i].state == E_DEAD)
			continue ;
		if (!hitscan_hit(data, &data->enemies[i]))
			continue ;
		d = (data->enemies[i].pos_x - data->player.pos_x)
			* (data->enemies[i].pos_x - data->player.pos_x)
			+ (data->enemies[i].pos_y - data->player.pos_y)
			* (data->enemies[i].pos_y - data->player.pos_y);
		if (d < best_d)
		{
			best_d = d;
			best_i = i;
		}
	}
	return (best_i);
}

static void	hitscan(t_data *data)
{
	int	target;

	target = find_target(data);
	if (target >= 0)
	{
		data->enemies[target].hp--;
		if (data->enemies[target].hp <= 0)
			kill_enemy(data, target);
	}
}

void	try_fire(t_data *data)
{
	if (!data->fire)
		return ;
	data->fire = 0;
	if (data->weapon.state != W_IDLE)
		return ;
	data->weapon.state = W_FIRING;
	data->weapon.timer = FIRE_COOLDOWN;
	hitscan(data);
}
