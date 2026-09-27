/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   fill_color_textures.c                              :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: cristian <cristian@student.42.fr>          +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/10 00:25:43 by cristian          #+#    #+#             */
/*   Updated: 2026/06/13 19:00:00 by cristian         ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "cub3d.h"

static int	validate_colors(char **split)
{
	int	i;
	int	j;

	i = 0;
	while (i < 3)
	{
		j = 0;
		while (split[i][j])
		{
			if (ft_isdigit(split[i][j]) == 0)
				return (FAILURE);
			j++;
		}
		if (j == 0)
			return (FAILURE);
		if (j > 3)
			return (FAILURE);
		if (ft_atoi(split[i]) > 255)
			return (FAILURE);
		i++;
	}
	return (SUCCESS);
}

static int	count_char(char *str, char c)
{
	int	count;

	count = 0;
	while (*str)
	{
		if (*str == c)
			count++;
		str++;
	}
	return (count);
}

static int	free_color(char *str, char **arr, int ret)
{
	if (str)
		free(str);
	if (arr)
		ft_free_split(arr);
	return (ret);
}

static int	parse_color(char *line, int *color)
{
	char	*colors_str;
	char	**split;

	colors_str = ft_strtrim(&line[1], " \t\n\r");
	if (!colors_str)
		return (FAILURE);
	if (count_char(colors_str, ',') != 2)
		return (free_color(colors_str, NULL, FAILURE));
	split = ft_split(colors_str, ',');
	if (!split)
		return (free_color(colors_str, NULL, FAILURE));
	if (!split[0] || !split[1] || !split[2] || split[3] != NULL)
		return (free_color(colors_str, split, FAILURE));
	if (validate_colors(split) != SUCCESS)
		return (free_color(colors_str, split, FAILURE));
	*color = (ft_atoi(split[0]) << 16) | (ft_atoi(split[1]) << 8)
		| ft_atoi(split[2]);
	return (free_color(colors_str, split, SUCCESS));
}

int	fill_color_textures(char *line, t_data *data)
{
	int	is_floor;
	int	color;

	if (line[0] == 'F')
		is_floor = 1;
	else
		is_floor = 0;
	if (is_floor && (data->id_flags & (1 << 4)))
		return (err_msg(NULL, ERR_DUPLICATE_COLOR, FAILURE));
	if (!is_floor && (data->id_flags & (1 << 5)))
		return (err_msg(NULL, ERR_DUPLICATE_COLOR, FAILURE));
	if (parse_color(line, &color) == FAILURE)
		return (err_msg(NULL, ERR_INVALID_COLOR, FAILURE));
	if (is_floor)
		data->floor_color = color;
	else
		data->ceiling_color = color;
	if (is_floor)
		data->id_flags |= (1 << 4);
	else
		data->id_flags |= (1 << 5);
	return (SUCCESS);
}
