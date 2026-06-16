/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   create_game_map.c                                  :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: cristian <cristian@student.42.fr>          +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/15 00:54:36 by cristian          #+#    #+#             */
/*   Updated: 2026/06/16 23:19:44 by cristian         ###   ########.fr       */
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

static char	*build_row(char *line, int width)
{
	int		i;
	char	*row;

	i = 0;
	row = malloc(width + 1);
	if (!row)
		return (NULL);
	while (line[i] && (line[i] != '\n' && line[i] != '\r') && i < width)
	{
		if (line[i] == ' ')
			row[i] = '1';
		else
			row[i] = line[i];
		i++;
	}
	while (i < width)
	{
		row[i] = '1';
		i++;
	}
	row[i] = '\0';
	return (row);
}

static int	fill_grid(t_data *data, int map_start, int map_end)
{
	int	i;
	int	width;

	i = 0;
	data->map_height = map_end - map_start + 1;
	width = find_biggest_len(data, map_start, map_end);
	data->map_width = width;
	data->map = malloc(sizeof(char *) * (data->map_height + 1));
	if (!data->map)
		return (FAILURE);
	while (i < data->map_height)
	{
		data->map[i] = build_row(data->file_lines[map_start + i], width);
		if (!data->map[i])
		{
			while (i-- > 0)
				free(data->map[i]);
			free(data->map);
			data->map = NULL;
			return (FAILURE);
		}
		i++;
	}
	data->map[i] = NULL;
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
	if (fill_grid(data, data->map_start, map_end) == FAILURE)
		return (FAILURE);
	return (SUCCESS);
}
