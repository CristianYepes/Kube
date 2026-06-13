/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   parsing_data.c                                     :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: cristian <cristian@student.42.fr>          +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/05/31 16:29:02 by cristian          #+#    #+#             */
/*   Updated: 2026/06/13 18:49:17 by cristian         ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "cub3d.h"

static int	count_lines(char *path)
{
	int		fd;
	int		count;
	char	*line;

	count = 0;
	line = 0;
	fd = open(path, O_RDONLY);
	if (fd == -1)
		return (-1);
	line = get_next_line(fd);
	while (line != NULL)
	{
		free(line);
		count++;
		line = get_next_line(fd);
	}
	close(fd);
	return (count);
}

static int	fill_lines(char *path, t_data *data)
{
	int		fd;
	int		i;
	char	*line;

	i = 0;
	line = 0;
	fd = open(path, O_RDONLY);
	if (fd == -1)
		return (err_msg(path, strerror(errno), FAILURE));
	line = get_next_line(fd);
	while (line != NULL && i < data->file_nb_lines)
	{
		data->file_lines[i] = line;
		i++;
		line = get_next_line(fd);
	}
	while (line != NULL)
	{
		free(line);
		line = get_next_line(fd);
	}
	data->file_lines[i] = NULL;
	close(fd);
	return (SUCCESS);
}

int	parse_memory(char *path, t_data *data)
{
	int		count;

	count = count_lines(path);
	if (count == -1)
		return (err_msg(path, strerror(errno), FAILURE));
	data->file_nb_lines = count;
	if (count == 0)
		return (err_msg(path, ERR_EMPTY_FILE, FAILURE));
	data->file_lines = malloc(sizeof(char *) * (count + 1));
	if (!data->file_lines)
		return (err_msg(path, strerror(errno), FAILURE));
	return (fill_lines(path, data));
}
