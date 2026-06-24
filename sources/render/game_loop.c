/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   game_loop.c                                        :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: rodrigo <rodrigo@student.42.fr>            +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/07 21:00:00 by cristian          #+#    #+#             */
/*   Updated: 2026/06/23 16:42:45 by rodrigo          ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "cub3d.h"

void	tick_sprite_anim(t_data *data, double dt)
{
	int	i;

	i = 0;
	while (i < data->sprite_count)
	{
		data->sprites[i].anim_timer += dt;
		if (data->sprites[i].anim_timer >= 0.20)
		{
			data->sprites[i].anim_timer = 0;
			data->sprites[i].frame_idx++;
			if (data->sprites[i].frame_idx >= 2)
				data->sprites[i].frame_idx = 0;
		}
		i++;
	}
}

int	game_loop(t_data *data)
{
	struct timeval	now;
	double			dt;

	gettimeofday(&now, NULL);
	dt = (now.tv_sec - data->last_time.tv_sec)
		+ (now.tv_usec - data->last_time.tv_usec) / 1000000.0;
	data->last_time = now;
	move_player(data);
	paint_floor_ceiling(data);
	cast_rays(data);
	compute_sprite_distances(data);
	sort_sprites(data);
	tick_sprite_anim(data, dt);
	render_sprites(data);
	tick_shotgun(data, dt);
	draw_shotgun(data);
	if (data->player.minimap)
		display_minimap(data);
	mlx_put_image_to_window(data->mlx, data->win, data->img.img, 0, 0);
	return (0);
}
