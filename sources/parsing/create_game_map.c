/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   create_game_map.c                                  :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: cristian <cristian@student.42.fr>          +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/15 00:54:36 by cristian          #+#    #+#             */
/*   Updated: 2026/06/15 02:05:17 by cristian         ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "cub3d.h"

static int	get_map_end(t_data *data)
{
	int	i;
	int	j;

	i = data->file_nb_lines - 1;
	while (i >= data->map_start)
	{
		j = 0;
		while (data->file_lines[i][j])
		{
			if (!is_a_white_space(data->file_lines[i][j]))
				return (i);
			j++;
		}
		i--;
	}
	return (data->map_start);
}

static int	check_no_gaps(t_data *data, int start, int end)
{
	int	i;
	int	j;

	i = start;
	while (i <= end)
	{
		j = 0;
		while (data->file_lines[i][j])
		{
			if (!is_a_white_space(data->file_lines[i][j]))
				break ;
			j++;
		}
		if (data->file_lines[i][j] == '\0')
			return (err_msg(NULL, ERR_EMPTY_LINE_IN_MAP, FAILURE));
		i++;
	}
	return (SUCCESS);
}

int	create_map(t_data *data)
{
	int	map_end;

	if (data->map_start == -1)
		return (err_msg(NULL, ERR_MAP_MISSING, FAILURE));
	map_end = get_map_end(data);
	if (check_no_gaps(data, data->map_start, map_end) == FAILURE)
		return (FAILURE);
	return (SUCCESS);
}
