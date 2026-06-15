/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   parsing_utils.c                                    :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: cristian <cristian@student.42.fr>          +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/13 19:15:00 by cristian          #+#    #+#             */
/*   Updated: 2026/06/15 00:39:03 by cristian         ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "cub3d.h"

int	is_a_white_space(char c)
{
	if (c == ' ' || c == '\t' || c == '\n' || c == '\r')
		return (1);
	return (0);
}

char	*skip_spaces(char *str)
{
	while (*str == ' ' || *str == '\t')
		str++;
	return (str);
}

void	free_file_lines(t_data *data)
{
	int	i;

	i = 0;
	if (!data->file_lines)
		return ;
	while (i < data->file_nb_lines)
	{
		free(data->file_lines[i]);
		i++;
	}
	free(data->file_lines);
	data->file_lines = NULL;
}

void	free_parsing(t_data *data)
{
	int	i;

	i = 0;
	free_file_lines(data);
	while (i < 4)
	{
		if (data->tex_paths[i])
		{
			free(data->tex_paths[i]);
			data->tex_paths[i] = NULL;
		}
		i++;
	}
}

int	find_biggest_len(t_data *data, int start, int end)
{
	int	max;
	int	len;
	int	i;

	max = 0;
	i = start;
	while (i <= end)
	{
		len = (int)ft_strlen(data->file_lines[i]);
		while (len > 0 && (data->file_lines[i][len - 1] == '\n'
			|| data->file_lines[i][len - 1] == '\r'))
			len--;
		if (len > max)
			max = len;
		i++;
	}
	return (max);
}
