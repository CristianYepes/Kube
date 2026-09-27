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

static int	place_enemy(t_data *data, int idx, int type)
{
	int	n;
	int	pick;
	int	x;
	int	y;

	n = count_spawn_cells(data);
	if (n <= 0)
		return (0);
	pick = lcg_next(&data->seed) % n;
	if (!pick_spawn_cell(data, pick, &x, &y))
		return (0);
	data->enemies[idx].pos_x = x + 0.3
		+ (lcg_next(&data->seed) % 40) / 100.0;
	data->enemies[idx].pos_y = y + 0.3
		+ (lcg_next(&data->seed) % 40) / 100.0;
	data->enemies[idx].type = type;
	data->enemies[idx].state = E_IDLE;
	data->enemies[idx].timer = 0;
	data->enemies[idx].atk_timer = 0;
	data->map[y][x] = 'Z';
	return (1);
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

static void	clear_spawn_marks(t_data *data)
{
	int	x;
	int	y;

	y = 0;
	while (y < data->map_height)
	{
		x = 0;
		while (x < data->map_width)
		{
			if (data->map[y][x] == 'Z')
				data->map[y][x] = '0';
			x++;
		}
		y++;
	}
}

static void	set_spawn_mode(t_data *data)
{
	data->spawn_relax = 0;
	if (count_spawn_cells(data) == 0)
		data->spawn_relax = 1;
}

void	spawn_wave(t_data *data)
{
	int	count;
	int	type;
	int	hp;
	int	placed;

	get_wave_params(data->wave, &count, &type, &hp);
	free(data->enemies);
	data->enemy_count = 0;
	data->enemies = malloc(sizeof(t_enemy) * count);
	if (!data->enemies)
		return ;
	set_spawn_mode(data);
	placed = 0;
	while (placed < count)
	{
		if (!place_enemy(data, placed, type))
			break ;
		data->enemies[placed].hp = hp;
		placed++;
	}
	clear_spawn_marks(data);
	data->enemy_count = placed;
	data->last_spawn = placed;
	if (data->wave == 3)
		data->fog = 1;
}
