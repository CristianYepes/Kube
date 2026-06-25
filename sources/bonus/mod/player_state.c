/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   player_state.c                                     :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: cristian <cristian@student.42.fr>          +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/24 14:00:00 by cristian          #+#    #+#             */
/*   Updated: 2026/06/24 14:00:00 by cristian         ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "cub3d.h"

void	update_player_hp(t_data *data)
{
	int	i;

	i = 0;
	while (i < data->enemy_count)
	{
		if (data->enemies[i].state == E_ATTACK)
		{
			data->enemies[i].atk_timer += data->dt;
			if (data->enemies[i].atk_timer >= ATTACK_RATE)
			{
				data->enemies[i].atk_timer = 0;
				data->player_hp -= 10;
			}
		}
		i++;
	}
}

void	check_game_state(t_data *data)
{
	if (data->player_hp <= 0)
	{
		data->game_state = G_OVER;
		return ;
	}
	if (data->wave == 3 && data->enemy_count == 0 && data->last_spawn > 0)
		data->game_state = G_WIN;
}
