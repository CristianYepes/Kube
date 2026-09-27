/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   enemy_ai.c                                         :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: rodrigo <rodrigo@student.42.fr>            +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/24 14:00:00 by cristian          #+#    #+#             */
/*   Updated: 2026/06/25 16:21:08 by rodrigo          ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "cub3d.h"

static double	dist_sq(t_enemy *e, t_data *data)
{
	double	dx;
	double	dy;

	dx = e->pos_x - data->player.pos_x;
	dy = e->pos_y - data->player.pos_y;
	return (dx * dx + dy * dy);
}

static double	get_speed(t_enemy *e, t_data *data, int idx)
{
	double	base;
	double	spd;

	base = 0.012 + (idx % 4) * 0.003;
	if (e->type == ENEMY_BOSS)
		base = 0.01;
	spd = base * data->dt * 60.0;
	if (spd > 0.4)
		spd = 0.4;
	return (spd);
}

static void	chase_player(t_data *data, t_enemy *e, int idx)
{
	double	dx;
	double	dy;
	double	spd;

	flow_dir(data, e, &dx, &dy);
	if (dx == 0 && dy == 0)
	{
		dx = data->player.pos_x - e->pos_x;
		dy = data->player.pos_y - e->pos_y;
		spd = dx * dx + dy * dy;
		if (spd < 0.001)
			return ;
		spd = sqrt(spd);
		dx /= spd;
		dy /= spd;
	}
	spd = get_speed(e, data, idx);
	dx *= spd;
	dy *= spd;
	if (!is_wall(data, e->pos_x + dx, e->pos_y))
		e->pos_x += dx;
	if (!is_wall(data, e->pos_x, e->pos_y + dy))
		e->pos_y += dy;
}

static void	enemy_fsm(t_data *data, t_enemy *e, int idx)
{
	double	d;

	if (e->state == E_DEAD)
		return ;
	d = dist_sq(e, data);
	if (e->state == E_IDLE)
		e->state = E_CHASE;
	else if (e->state == E_CHASE)
	{
		chase_player(data, e, idx);
		if (d < 0.8)
			e->state = E_ATTACK;
	}
	else if (e->state == E_ATTACK)
	{
		if (d > 2.25)
			e->state = E_CHASE;
	}
}

void	update_enemies(t_data *data)
{
	int	i;

	i = 0;
	while (i < data->enemy_count)
	{
		enemy_fsm(data, &data->enemies[i], i);
		i++;
	}
}
