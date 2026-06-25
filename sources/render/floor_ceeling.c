/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   floor_ceeling.c                                    :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: rodrigo <rodrigo@student.42.fr>            +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/12 13:44:29 by rodrigo           #+#    #+#             */
/*   Updated: 2026/06/25 16:00:00 by cristian         ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "cub3d.h"

static int	fog_row(t_data *data, int y)
{
	double	dist;
	int		base;

	if (y < WIN_H / 2)
	{
		base = data->ceiling_color;
		dist = FOG_MAX * y / (WIN_H / 2.0);
	}
	else
	{
		base = data->floor_color;
		dist = FOG_MAX * (WIN_H - y) / (WIN_H / 2.0);
	}
	return (apply_fog(base, dist, data->fog));
}

void	paint_floor_ceiling(t_data *data)
{
	int	x;
	int	y;
	int	col;

	y = 0;
	while (y < WIN_H)
	{
		col = fog_row(data, y);
		x = 0;
		while (x < WIN_W)
		{
			put_pixel(data, x, y, col);
			x++;
		}
		y++;
	}
}
