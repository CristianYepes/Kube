/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   floor_ceeling.c                                    :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: rodrigo <rodrigo@student.42.fr>            +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/12 13:44:29 by rodrigo           #+#    #+#             */
/*   Updated: 2026/06/12 13:50:08 by rodrigo          ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "cub3d.h"

void	paint_floor_ceiling(t_data *data)
{
	int	x;
	int	y;

	y = 0;
	while (y < WIN_H)
	{
		x = 0;
		while (x < WIN_W)
		{
			if (y < WIN_H / 2)
				put_pixel(data, x, y, data->ceiling_color);
			else
				put_pixel(data, x, y, data->floor_color);
			x++;
		}
		y++;
	}
}
