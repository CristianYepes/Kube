/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   render_utils.c                                     :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: rodrigo <rodrigo@student.42.fr>            +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/07 21:00:00 by cristian          #+#    #+#             */
/*   Updated: 2026/06/14 17:30:58 by rodrigo          ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "cub3d.h"

void	put_pixel(t_data *data, int x, int y, int color)
{
	int	index;

	if (x >= WIN_W || y >= WIN_H || x < 0 || y < 0)
		return ;
	index = y * data->img.size_line + x * (data->img.bpp / 8);
	data->img.addr[index] = color & 0xFF;
	data->img.addr[index + 1] = (color >> 8) & 0xFF;
	data->img.addr[index + 2] = (color >> 16) & 0xFF;
}
