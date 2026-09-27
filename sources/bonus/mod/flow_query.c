/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   flow_query.c                                       :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: rodrigo <rodrigo@student.42.fr>            +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/26 08:00:00 by rodrigo           #+#    #+#             */
/*   Updated: 2026/06/26 08:00:00 by rodrigo          ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "cub3d.h"

static int	get_flow_val(t_data *data, int x, int y)
{
	if (x < 0 || x >= data->map_width)
		return (-1);
	if (y < 0 || y >= data->map_height)
		return (-1);
	return (data->flow[y][x]);
}

static void	best_neighbor(t_data *data, int *pos, int *best)
{
	int	i;
	int	n[2];
	int	val;
	int	bval;

	bval = data->flow[pos[1]][pos[0]];
	best[0] = pos[0];
	best[1] = pos[1];
	i = -1;
	while (++i < 4)
	{
		n[0] = pos[0] + (i == 0) - (i == 1);
		n[1] = pos[1] + (i == 2) - (i == 3);
		val = get_flow_val(data, n[0], n[1]);
		if (val >= 0 && val < bval)
		{
			bval = val;
			best[0] = n[0];
			best[1] = n[1];
		}
	}
}

void	flow_dir(t_data *data, t_enemy *e, double *dx, double *dy)
{
	int		pos[2];
	int		best[2];
	double	len;

	pos[0] = (int)e->pos_x;
	pos[1] = (int)e->pos_y;
	best_neighbor(data, pos, best);
	*dx = (best[0] + 0.5) - e->pos_x;
	*dy = (best[1] + 0.5) - e->pos_y;
	len = (*dx) * (*dx) + (*dy) * (*dy);
	if (len < 0.001)
	{
		*dx = 0;
		*dy = 0;
		return ;
	}
	len = sqrt(len);
	*dx /= len;
	*dy /= len;
}
