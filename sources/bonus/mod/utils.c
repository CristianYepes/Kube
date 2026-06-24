/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   utils.c                                            :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: cristian <cristian@student.42.fr>          +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/24 14:00:00 by cristian          #+#    #+#             */
/*   Updated: 2026/06/24 14:00:00 by cristian         ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "cub3d.h"

unsigned int	lcg_next(unsigned int *seed)
{
	*seed = *seed * 1103515245 + 12345;
	return ((*seed / 65536) % 32768);
}

static int	is_valid_spawn(t_data *data, int x, int y)
{
	double	dx;
	double	dy;

	if (x < 1 || x >= data->map_width - 1)
		return (0);
	if (y < 1 || y >= data->map_height - 1)
		return (0);
	if (data->map[y][x] != '0')
		return (0);
	dx = x + 0.5 - data->player.pos_x;
	dy = y + 0.5 - data->player.pos_y;
	if (dx * dx + dy * dy < 4.0)
		return (0);
	return (1);
}

int	count_spawn_cells(t_data *data)
{
	int	x;
	int	y;
	int	n;

	n = 0;
	y = 1;
	while (y < data->map_height - 1)
	{
		x = 1;
		while (x < data->map_width - 1)
		{
			if (is_valid_spawn(data, x, y))
				n++;
			x++;
		}
		y++;
	}
	return (n);
}

int	pick_spawn_cell(t_data *data, int n, int *ox, int *oy)
{
	int	x;
	int	y;

	y = 1;
	while (y < data->map_height - 1)
	{
		x = 1;
		while (x < data->map_width - 1)
		{
			if (is_valid_spawn(data, x, y) && n-- == 0)
			{
				*ox = x;
				*oy = y;
				return (1);
			}
			x++;
		}
		y++;
	}
	return (0);
}
