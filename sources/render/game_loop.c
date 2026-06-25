/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   game_loop.c                                        :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: cristian <cristian@student.42.fr>          +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/07 21:00:00 by cristian          #+#    #+#             */
/*   Updated: 2026/06/24 12:00:00 by cristian         ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "cub3d.h"

#ifdef BONUS

int	game_loop(t_data *data)
{
	struct timeval	now;

	gettimeofday(&now, NULL);
	data->dt = (now.tv_sec - data->last_time.tv_sec)
		+ (now.tv_usec - data->last_time.tv_usec) / 1000000.0;
	data->last_time = now;
	data->anim_clock += data->dt;
	if (data->game_state == G_PLAY)
	{
		move_player(data);
		update_sim(data);
	}
	paint_floor_ceiling(data);
	cast_rays(data);
	render_enemies(data);
	tick_shotgun(data, data->dt);
	draw_shotgun(data);
	render_weapon(data);
	render_hud(data);
	if (data->player.minimap)
		display_minimap(data);
	mlx_put_image_to_window(data->mlx, data->win, data->img.img, 0, 0);
	return (0);
}
#else

int	game_loop(t_data *data)
{
	move_player(data);
	paint_floor_ceiling(data);
	cast_rays(data);
	mlx_put_image_to_window(data->mlx, data->win, data->img.img, 0, 0);
	return (0);
}
#endif
