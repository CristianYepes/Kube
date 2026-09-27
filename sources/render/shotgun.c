/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   shotgun.c                                          :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: cristian <cristian@student.42.fr>          +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/23 17:00:00 by rodrigo           #+#    #+#             */
/*   Updated: 2026/06/24 12:00:00 by cristian         ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "cub3d.h"

int	init_shotgun(t_data *data)
{
	data->gun_tex[0] = xpm_to_int_size(data,
			"textures/shotgun/shotgun_idle.xpm", GUN_SIZE);
	data->gun_tex[1] = xpm_to_int_size(data,
			"textures/shotgun/shotgun_fire0.xpm", GUN_SIZE);
	data->gun_tex[2] = xpm_to_int_size(data,
			"textures/shotgun/shotgun_fire1.xpm", GUN_SIZE);
	data->gun_tex[3] = xpm_to_int_size(data,
			"textures/shotgun/shotgun_fire2.xpm", GUN_SIZE);
	if (!data->gun_tex[0] || !data->gun_tex[1]
		|| !data->gun_tex[2] || !data->gun_tex[3])
		return (FAILURE);
	data->gun_frame = 0;
	data->gun_firing = 0;
	data->gun_timer = 0;
	return (SUCCESS);
}

void	fire_shotgun(t_data *data)
{
	if (!data->gun_firing)
	{
		data->gun_firing = 1;
		data->gun_frame = 1;
		data->gun_timer = 0;
	}
}

void	tick_shotgun(t_data *data, double dt)
{
	if (!data->gun_firing)
		return ;
	data->gun_timer += dt;
	if (data->gun_timer >= 0.08)
	{
		data->gun_timer = 0;
		data->gun_frame++;
		if (data->gun_frame >= GUN_FRAMES)
		{
			data->gun_frame = 0;
			data->gun_firing = 0;
		}
	}
}
