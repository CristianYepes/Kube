/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   waves.c                                            :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: cristian <cristian@student.42.fr>          +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/24 14:00:00 by cristian          #+#    #+#             */
/*   Updated: 2026/06/24 14:00:00 by cristian         ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "cub3d.h"

unsigned int	lcg_next(unsigned int *seed)
{
	*seed = *seed * 1103515245 + 12345;
	return ((*seed / 65536) % 32768);
}

static int	is_valid_spawn(t_data *data, int x, int y)
{
	double	dx;
	double	dy;

	if (data->map[y][x] != '0')
		return (0);
	dx = x + 0.5 - data->player.pos_x;
	dy = y + 0.5 - data->player.pos_y;
	if (dx * dx + dy * dy < 9.0)
		return (0);
	return (1);
}

static void	place_enemy(t_data *data, int idx, int type)
{
	int	x;
	int	y;
	int	attempts;

	attempts = 0;
	x = lcg_next(&data->seed) % data->map_width;
	y = lcg_next(&data->seed) % data->map_height;
	while (!is_valid_spawn(data, x, y) && attempts < 200)
	{
		x = lcg_next(&data->seed) % data->map_width;
		y = lcg_next(&data->seed) % data->map_height;
		attempts++;
	}
	data->enemies[idx].pos_x = x + 0.5;
	data->enemies[idx].pos_y = y + 0.5;
	data->enemies[idx].type = type;
	data->enemies[idx].state = E_IDLE;
	data->enemies[idx].timer = 0;
	data->enemies[idx].atk_timer = 0;
}

static void	get_wave_params(int wave, int *count, int *type, int *hp)
{
	if (wave == 1)
	{
		*count = 3;
		*type = ENEMY_GRUNT;
		*hp = 2;
	}
	else if (wave == 2)
	{
		*count = 4;
		*type = ENEMY_RUNNER;
		*hp = 1;
	}
	else
	{
		*count = 1;
		*type = ENEMY_BOSS;
		*hp = 8;
	}
}

void	spawn_wave(t_data *data)
{
	int	count;
	int	type;
	int	hp;
	int	i;

	get_wave_params(data->wave, &count, &type, &hp);
	if (data->enemies)
		free(data->enemies);
	data->enemies = malloc(sizeof(t_enemy) * count);
	if (!data->enemies)
		return ;
	data->enemy_count = count;
	i = -1;
	while (++i < count)
	{
		place_enemy(data, i, type);
		data->enemies[i].hp = hp;
	}
	if (data->wave == 3)
		data->fog = 1;
}
