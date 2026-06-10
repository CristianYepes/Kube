/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   get_file_data.c                                    :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: cristian <cristian@student.42.fr>          +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/05/31 16:30:05 by cristian          #+#    #+#             */
/*   Updated: 2026/06/11 00:52:06 by cristian         ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "cub3d.h"

static int	line_type(char	*line)
{
	if (line[0] == '\n' || line[0] == '\0')
		return (TYPE_EMPTY);
	if (ft_strncmp(line, "NO", 2) == 0 && (line[2] == ' ' || line[2] == '\t'))
		return (TYPE_TEXTURE);
	if (ft_strncmp(line, "SO", 2) == 0 && (line[2] == ' ' || line[2] == '\t'))
		return (TYPE_TEXTURE);
	if (ft_strncmp(line, "WE", 2) == 0 && (line[2] == ' ' || line[2] == '\t'))
		return (TYPE_TEXTURE);
	if (ft_strncmp(line, "EA", 2) == 0 && (line[2] == ' ' || line[2] == '\t'))
		return (TYPE_TEXTURE);
	if (ft_strncmp(line, "F", 1) == 0 && (line[1] == ' ' || line[1] == '\t'))
		return (TYPE_COLOR);
	if (ft_strncmp(line, "C", 1) == 0 && (line[1] == ' ' || line[1] == '\t'))
		return (TYPE_COLOR);
	return (TYPE_MAP);
}

static int	extract_texture(char *line, t_data *data)
{
	int	index;

	if (ft_strncmp(line, "NO", 2) == 0)
		index = NORTH;
	if (ft_strncmp(line, "SO", 2) == 0)
		index = SOUTH;
	if (ft_strncmp(line, "WE", 2) == 0)
		index = WEST;
	if (ft_strncmp(line, "EA", 2) == 0)
		index = EAST;
	if (data->tex_paths[index] != NULL)
		return (err_msg(NULL, ERR_DUPLICATE_TEXTURE, FAILURE));
	data->tex_paths[index] = ft_strtrim(&line[2], " \t\n\r");
	if (data->tex_paths[index][0] == '\0')
		return (err_msg(NULL, ERR_EMPTY_PATH, FAILURE));
	return (SUCCESS);
}

static int	process_line(char *line, int type, t_data *data)
{
	if (type == TYPE_EMPTY)
		return (SUCCESS);
	if (type == TYPE_TEXTURE)
		return (extract_texture(line, data));
	if (type == TYPE_COLOR)
		return (fill_color_textures(line, data));
	if (type == TYPE_MAP)
		return (SUCCESS);
	return (0);
}

int	get_file_data(t_data *data)
{
	int	i;
	int	type;

	i = 0;
	while (i < data->file_nb_lines)
	{
		type = line_type(data->file_lines[i]);
		if (process_line(data->file_lines[i], type, data) == FAILURE)
			return (FAILURE);
		i++;
	}
	return (SUCCESS);
}
