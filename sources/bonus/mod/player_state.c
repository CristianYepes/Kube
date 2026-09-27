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

static int	enemy_can_hit(t_data *data, t_enemy *e)
{
	double	dx;
	double	dy;

	dx = e->pos_x - data->player.pos_x;
	dy = e->pos_y - data->player.pos_y;
	if (dx * dx + dy * dy > 1.0)
		return (0);
	return (has_los(data, e->pos_x, e->pos_y));
}

void	update_player_hp(t_data *data)
{
	int	i;

	i = 0;
	while (i < data->enemy_count)
	{
		if (data->enemies[i].state == E_ATTACK
			&& enemy_can_hit(data, &data->enemies[i]))
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
	if (data->wave == 3 && data->enemy_count == 0)
		data->game_state = G_WIN;
}
