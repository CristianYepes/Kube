/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   minimap_2.c                                        :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: rodrigo <rodrigo@student.42.fr>            +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/22 19:26:46 by rodrigo           #+#    #+#             */
/*   Updated: 2026/06/23 00:12:50 by rodrigo          ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "cub3d.h"

static int	in_bounds(t_data *data, int y, int x)
{
	if (y < 0 || y >= data->map_height)
		return (0);
	if (x < 0 || x >= data->map_width)
		return (0);
	if (!data->map[y][x])
		return (0);
	return (1);
}

void	draw_sprite(int x, int y, int size, t_data *data)
{
	int	i;

	i = 0;
	while (i++ < size)
		put_pixel(data, x + i, y, 0x00FF00);
	i = 0;
	while (i < size)
	{
		put_pixel(data, x, y + i, 0x00FF00);
		i++;
	}
	i = 0;
	while (i < size)
	{
		put_pixel(data, x + size, y + i, 0x00FF00);
		i++;
	}
	i = 0;
	while (i < size)
	{
		put_pixel(data, x + i, y + size, 0x00FF00);
		i++;
	}
}

void	draw_map2(t_data *data)
{
	int	y;
	int	x;
	int	start_y;
	int	start_x;

	start_y = (int)data->player.pos_y - 4;
	start_x = (int)data->player.pos_x - 4;
	y = start_y;
	while (y <= start_y + 8)
	{
		x = start_x;
		while (x <= start_x + 8)
		{
			if (in_bounds(data, y, x) && data->map[y][x] == '1')
				draw_square((x - start_x) * 20,
					(y - start_y) * 20, 20, data);
			if (in_bounds(data, y, x)
				&& (data->map[y][x] == '2' || data->map[y][x] == '3'))
				draw_sprite((x - start_x) * 20 + 5,
					(y - start_y) * 20 + 5, 10, data);
			x++;
		}
		y++;
	}
	draw_player(88, 88, 5, data);
}
