/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   shotgun.c                                          :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: rodrigo <rodrigo@student.42.fr>            +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/23 17:00:00 by rodrigo           #+#    #+#             */
/*   Updated: 2026/06/23 17:00:00 by rodrigo          ###   ########.fr       */
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

static void	draw_gun_layer(t_data *data, int *tex, int sx, int sy)
{
	int	x;
	int	y;
	int	color;

	y = 0;
	while (y < GUN_SIZE)
	{
		x = 0;
		while (x < GUN_SIZE)
		{
			color = tex[y * GUN_SIZE + x];
			if ((color & 0xFFFFFF) != 0xFF00FF)
				put_pixel(data, sx + x, sy + y, color);
			x++;
		}
		y++;
	}
}

static void	draw_crosshair(t_data *data)
{
	int	i;
	int	cx;
	int	cy;

	cx = WIN_W / 2;
	cy = WIN_H / 2;
	i = -5;
	while (i <= 5)
	{
		if (i < -1 || i > 1)
		{
			put_pixel(data, cx + i, cy, 0xFFFFFF);
			put_pixel(data, cx, cy + i, 0xFFFFFF);
		}
		i++;
	}
}

void	draw_shotgun(t_data *data)
{
	int	start_x;
	int	start_y;

	start_x = WIN_W / 2 - GUN_SIZE / 2 + 500;
	start_y = WIN_H - GUN_SIZE + 50;
	draw_gun_layer(data, data->gun_tex[data->gun_frame], start_x, start_y);
	draw_crosshair(data);
}
