/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   restart.c                                          :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: cristian <cristian@student.42.fr>          +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/26 10:00:00 by cristian          #+#    #+#             */
/*   Updated: 2026/06/26 10:00:00 by cristian         ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "cub3d.h"

static void	reset_player(t_data *data)
{
	data->player.pos_x = data->spawn_x;
	data->player.pos_y = data->spawn_y;
	if (data->spawn_dir == 'N' || data->spawn_dir == 'S')
		set_ns(&data->player, data->spawn_dir);
	else
		set_ew(&data->player, data->spawn_dir);
	data->player.key_up = 0;
	data->player.key_down = 0;
	data->player.key_left = 0;
	data->player.key_right = 0;
	data->player.rotate_left = 0;
	data->player.rotate_right = 0;
}

static void	reset_mod_state(t_data *data)
{
	struct timeval	now;

	data->wave = 1;
	data->player_hp = 100;
	data->game_state = G_PLAY;
	data->fog = 0;
	data->weapon.state = W_IDLE;
	data->weapon.timer = 0;
	data->fire = 0;
	data->gun_frame = 0;
	data->gun_firing = 0;
	data->gun_timer = 0;
	free(data->enemies);
	data->enemies = NULL;
	data->enemy_count = 0;
	data->last_spawn = 0;
	data->spawn_relax = 0;
	gettimeofday(&now, NULL);
	data->seed = now.tv_usec;
}

static void	reset_doors(t_data *data)
{
	int	x;
	int	y;

	y = 0;
	while (y < data->map_height)
	{
		x = 0;
		while (data->map[y][x])
		{
			if (data->map[y][x] == 'O')
				data->map[y][x] = 'D';
			x++;
		}
		y++;
	}
}

void	restart_game(t_data *data)
{
	reset_player(data);
	reset_mod_state(data);
	reset_doors(data);
}
