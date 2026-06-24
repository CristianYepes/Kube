/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   sim.c                                              :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: cristian <cristian@student.42.fr>          +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/24 14:00:00 by cristian          #+#    #+#             */
/*   Updated: 2026/06/24 14:00:00 by cristian         ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "cub3d.h"

static void	tick_weapon(t_data *data)
{
	if (data->weapon.state == W_FIRING)
	{
		data->weapon.timer -= data->dt;
		if (data->weapon.timer <= 0)
		{
			data->weapon.timer = 0;
			data->weapon.state = W_IDLE;
		}
	}
}

static void	check_wave_advance(t_data *data)
{
	if (data->enemy_count == 0 && data->wave < 3)
	{
		data->wave++;
		spawn_wave(data);
	}
}

void	update_sim(t_data *data)
{
	if (data->game_state != G_PLAY)
		return ;
	if (!data->enemies)
		spawn_wave(data);
	tick_weapon(data);
	update_enemies(data);
	try_fire(data);
	update_player_hp(data);
	check_game_state(data);
	check_wave_advance(data);
}
