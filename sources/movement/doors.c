/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   doors.c                                            :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: cristian <cristian@student.42.fr>          +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/24 12:00:00 by cristian          #+#    #+#             */
/*   Updated: 2026/06/24 12:00:00 by cristian         ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "cub3d.h"

void	toggle_door(t_data *data)
{
	int		cx;
	int		cy;
	char	cell;

	cx = (int)(data->player.pos_x + data->player.dir_x);
	cy = (int)(data->player.pos_y + data->player.dir_y);
	if (cx < 0 || cx >= data->map_width
		|| cy < 0 || cy >= data->map_height)
		return ;
	cell = data->map[cy][cx];
	if (cell == DOOR_CLOSED)
		data->map[cy][cx] = DOOR_OPEN;
	else if (cell == DOOR_OPEN)
	{
		if ((int)data->player.pos_x == cx
			&& (int)data->player.pos_y == cy)
			return ;
		data->map[cy][cx] = DOOR_CLOSED;
	}
}
