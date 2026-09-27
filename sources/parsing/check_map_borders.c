/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   check_map_borders.c                                :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: cristian <cristian@student.42.fr>          +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/18 19:35:27 by cristian          #+#    #+#             */
/*   Updated: 2026/06/18 20:15:50 by cristian         ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "cub3d.h"

static int	check_first_last_col(t_data *data)
{
	int	i;

	i = 0;
	while (i < data->map_height)
	{
		if (data->map[i][0] != '1')
			return (err_msg(NULL, ERR_MAP_NOT_CLOSED, FAILURE));
		if (data->map[i][data->map_width - 1] != '1')
			return (err_msg(NULL, ERR_MAP_NOT_CLOSED, FAILURE));
		i++;
	}
	return (SUCCESS);
}

int	check_map_borders(t_data *data)
{
	int	j;

	if (data->map_width < 3 || data->map_height < 3)
		return (err_msg(NULL, ERR_MAP_NOT_CLOSED, FAILURE));
	j = 0;
	while (j < data->map_width)
	{
		if (data->map[0][j] != '1')
			return (err_msg(NULL, ERR_MAP_NOT_CLOSED, FAILURE));
		j++;
	}
	j = 0;
	while (j < data->map_width)
	{
		if (data->map[data->map_height - 1][j] != '1')
			return (err_msg(NULL, ERR_MAP_NOT_CLOSED, FAILURE));
		j++;
	}
	return (check_first_last_col(data));
}
