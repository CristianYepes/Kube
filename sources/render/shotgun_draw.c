/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   shotgun_draw.c                                     :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: cristian <cristian@student.42.fr>          +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/24 12:00:00 by cristian          #+#    #+#             */
/*   Updated: 2026/06/24 12:00:00 by cristian         ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "cub3d.h"

static void	draw_gun_layer(t_data *data, int *tex, int sx, int sy)
{
	int	x;
	int	y;
	int	color;

	y = 0;
	while (y < GUN_SIZE && sy + y < WIN_H)
	{
		if (sy + y >= 0)
		{
			x = 0;
			while (x < GUN_SIZE && sx + x < WIN_W)
			{
				if (sx + x >= 0)
				{
					color = tex[y * GUN_SIZE + x];
					if ((color & 0xFFFFFF) != 0xFF00FF)
						put_pixel(data, sx + x, sy + y, color);
				}
				x++;
			}
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

	start_x = WIN_W / 2 - GUN_SIZE / 2;
	start_y = WIN_H - GUN_SIZE;
	draw_gun_layer(data, data->gun_tex[data->gun_frame], start_x, start_y);
	draw_crosshair(data);
}
