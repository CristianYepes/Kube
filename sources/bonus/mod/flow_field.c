/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   flow_field.c                                       :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: rodrigo <rodrigo@student.42.fr>            +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/26 07:41:50 by rodrigo           #+#    #+#             */
/*   Updated: 2026/06/26 07:46:31 by rodrigo          ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "cub3d.h"

static int	cell_walkable(t_data *data, int x, int y)
{
	if (x < 0 || x >= data->map_width)
		return (0);
	if (y < 0 || y >= data->map_height)
		return (0);
	if (data->map[y][x] == '1' || data->map[y][x] == DOOR_CLOSED)
		return (0);
	return (1);
}

static void	bfs_init(t_data *data, int *head, int *tail)
{
	int	x;
	int	y;

	y = 0;
	while (y < data->map_height)
	{
		x = 0;
		while (x < data->map_width)
			data->flow[y][x++] = -1;
		y++;
	}
	*head = 0;
	*tail = 1;
	data->flow[data->flow_py][data->flow_px] = 0;
	data->qx[0] = data->flow_px;
	data->qy[0] = data->flow_py;
}

static void	bfs_loop(t_data *data, int head, int tail)
{
	int	cx;
	int	cy;
	int	i;
	int	nx;
	int	ny;

	while (head < tail)
	{
		cx = data->qx[head];
		cy = data->qy[head++];
		i = -1;
		while (++i < 4)
		{
			nx = cx + (i == 0) - (i == 1);
			ny = cy + (i == 2) - (i == 3);
			if (cell_walkable(data, nx, ny) && data->flow[ny][nx] == -1)
			{
				data->flow[ny][nx] = data->flow[cy][cx] + 1;
				data->qx[tail] = nx;
				data->qy[tail++] = ny;
			}
		}
	}
}

void	update_flow_field(t_data *data)
{
	int	px;
	int	py;
	int	head;
	int	tail;

	px = (int)data->player.pos_x;
	py = (int)data->player.pos_y;
	if (px == data->flow_px && py == data->flow_py)
		return ;
	if (data->map_width >= MAX_MAP || data->map_height >= MAX_MAP)
		return ;
	data->flow_px = px;
	data->flow_py = py;
	bfs_init(data, &head, &tail);
	bfs_loop(data, head, tail);
}
