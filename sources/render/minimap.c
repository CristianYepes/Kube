/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   minimap.c                                          :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: rodrigo <rodrigo@student.42.fr>            +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/22 17:11:37 by rodrigo           #+#    #+#             */
/*   Updated: 2026/06/23 15:25:18 by rodrigo          ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "cub3d.h"

void	draw_square(int x, int y, int size, t_data *data)
{
	int	i;

	x += data->mini_x;
	y += data->mini_y;
	i = 0;
	while (i++ < size)
		put_pixel(data, x + i, y, 0x0000FF);
	i = 0;
	while (i < size)
	{
		put_pixel(data, x, y + i, 0x0000FF);
		i++;
	}
	i = 0;
	while (i < size)
	{
		put_pixel(data, x + size, y + i, 0x0000FF);
		i++;
	}
	i = 0;
	while (i < size)
	{
		put_pixel(data, x + i, y + size, 0x0000FF);
		i++;
	}
}

void	draw_player(int x, int y, int size, t_data *data)
{
	int	i;

	x += data->mini_x;
	y += data->mini_y;
	i = 0;
	while (i++ < size)
		put_pixel(data, x + i, y, 0xFF0000);
	i = 0;
	while (i < size)
	{
		put_pixel(data, x, y + i, 0xFF0000);
		i++;
	}
	i = 0;
	while (i < size)
	{
		put_pixel(data, x + size, y + i, 0xFF0000);
		i++;
	}
	i = 0;
	while (i < size)
	{
		put_pixel(data, x + i, y + size, 0xFF0000);
		i++;
	}
}

void	draw_map(t_data *data)
{
	char	**map;
	int		y;
	int		x;

	map = data->map;
	y = 0;
	while (map[y])
	{
		x = 0;
		while (map[y][x])
		{
			if (map[y][x] == '2')
				draw_sprite(x * 20 + 5, y * 20 + 5, 10, data);
			if (map[y][x] == '1')
				draw_square(x * 20, y * 20, 20, data);
			x++;
		}
		y++;
	}
}

void	draw_frame(t_data *data, int mx, int my, int color)
{
	int	x;
	int	y;

	y = 0;
	while (y < my)
	{
		x = 0;
		while (x < mx)
		{
			put_pixel(data, data->mini_x + x, data->mini_y + y, color);
			x++;
		}
		y++;
	}
}

void	display_minimap(t_data *data)
{
	int	h;

	if (data->map_width < 15 && data->map_height < 15)
	{
		h = data->map_height * 20;
		data->mini_x = 0;
		data->mini_y = 0;
		draw_frame(data, data->map_width * 20, h, 0x000000);
		draw_map(data);
		draw_player(data->player.pos_x * 20 - 2,
			data->player.pos_y * 20 - 2, 5, data);
	}
	else
	{
		data->mini_x = 0;
		data->mini_y = 0;
		draw_frame(data, 190, 190, 0x000000);
		draw_frame(data, 180, 180, 0x1A1A1A);
		draw_map2(data);
	}
}
