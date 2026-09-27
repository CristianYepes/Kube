/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   check_textures.c                                   :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: cristian <cristian@student.42.fr>          +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/18 20:21:57 by cristian          #+#    #+#             */
/*   Updated: 2026/06/18 20:47:53 by cristian         ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "cub3d.h"

static int	validate_one_texture(char *path)
{
	int		len;
	int		fd;
	char	buf;

	len = (int)ft_strlen(path);
	if (len < 4 || ft_strncmp(&path[len - 4], ".xpm", 4) != 0)
		return (err_msg(path, ERR_TEX_NOT_XPM, FAILURE));
	fd = open(path, O_RDONLY);
	if (fd == -1)
		return (err_msg(path, strerror(errno), FAILURE));
	if (read(fd, &buf, 1) <= 0)
	{
		close(fd);
		if (errno)
			return (err_msg(path, strerror(errno), FAILURE));
		return (err_msg(path, "Empty or invalid file", FAILURE));
	}
	close(fd);
	return (SUCCESS);
}

int	check_textures(t_data *data)
{
	int	i;

	i = 0;
	while (i < 4)
	{
		if (data->tex_paths[i] == NULL)
			return (err_msg(NULL, ERR_MISSING_ID, FAILURE));
		if (validate_one_texture(data->tex_paths[i]) == FAILURE)
			return (FAILURE);
		i++;
	}
	return (SUCCESS);
}
