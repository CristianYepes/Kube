/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   get_file_data.c                                    :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: cristian <cristian@student.42.fr>          +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/05/31 16:30:05 by cristian          #+#    #+#             */
/*   Updated: 2026/06/15 00:52:55 by cristian         ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "cub3d.h"

static int	line_type(char *line)
{
	char	*t;

	t = skip_spaces(line);
	if (t[0] == '\n' || t[0] == '\0')
		return (TYPE_EMPTY);
	if (ft_strncmp(t, "NO", 2) == 0
		&& (t[2] == ' ' || t[2] == '\t' || t[2] == '\n' || t[2] == '\0'))
		return (TYPE_TEXTURE);
	if (ft_strncmp(t, "SO", 2) == 0
		&& (t[2] == ' ' || t[2] == '\t' || t[2] == '\n' || t[2] == '\0'))
		return (TYPE_TEXTURE);
	if (ft_strncmp(t, "WE", 2) == 0
		&& (t[2] == ' ' || t[2] == '\t' || t[2] == '\n' || t[2] == '\0'))
		return (TYPE_TEXTURE);
	if (ft_strncmp(t, "EA", 2) == 0
		&& (t[2] == ' ' || t[2] == '\t' || t[2] == '\n' || t[2] == '\0'))
		return (TYPE_TEXTURE);
	if ((t[0] == 'F' || t[0] == 'C')
		&& (t[1] == ' ' || t[1] == '\t' || t[1] == '\n' || t[1] == '\0'))
		return (TYPE_COLOR);
	return (TYPE_MAP);
}

static int	extract_texture(char *line, t_data *data)
{
	int	index;

	if (ft_strncmp(line, "NO", 2) == 0)
		index = NORTH;
	else if (ft_strncmp(line, "SO", 2) == 0)
		index = SOUTH;
	else if (ft_strncmp(line, "WE", 2) == 0)
		index = WEST;
	else
		index = EAST;
	if (data->tex_paths[index] != NULL)
		return (err_msg(NULL, ERR_DUPLICATE_TEXTURE, FAILURE));
	data->tex_paths[index] = ft_strtrim(&line[2], " \t\n\r");
	if (!data->tex_paths[index])
		return (err_msg(NULL, strerror(errno), FAILURE));
	if (data->tex_paths[index][0] == '\0')
		return (err_msg(NULL, ERR_EMPTY_PATH, FAILURE));
	return (SUCCESS);
}

static int	process_line(char *line, int type, t_data *data)
{
	char	*trimmed;

	if (type == TYPE_EMPTY)
		return (SUCCESS);
	trimmed = skip_spaces(line);
	if (type == TYPE_TEXTURE)
		return (extract_texture(trimmed, data));
	if (type == TYPE_COLOR)
		return (fill_color_textures(trimmed, data));
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
		if (type == TYPE_MAP && data->map_start == -1)
			data->map_start = i;
		if ((type == TYPE_TEXTURE || type == TYPE_COLOR)
			&& data->map_start != -1)
			return (err_msg(NULL, ERR_ID_AFTER_MAP, FAILURE));
		if (process_line(data->file_lines[i], type, data) == FAILURE)
			return (FAILURE);
		i++;
	}
	return (SUCCESS);
}
