/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   init_textures.c                                    :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: rodrigo <rodrigo@student.42.fr>            +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 17:20:00 by rodrigo           #+#    #+#             */
/*   Updated: 2026/06/17 17:20:00 by rodrigo          ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "cub3d.h"

static void	cleanup_textures(t_data *data, int n)
{
	while (--n >= 0)
	{
		free(data->textures[n]);
		data->textures[n] = NULL;
	}
}

int	init_textures(t_data *data)
{
	ft_bzero(data->textures, sizeof(int *) * 4);
	data->textures[NORTH] = xpm_to_int(data, data->tex_paths[NORTH]);
	data->textures[SOUTH] = xpm_to_int(data, data->tex_paths[SOUTH]);
	data->textures[WEST] = xpm_to_int(data, data->tex_paths[WEST]);
	data->textures[EAST] = xpm_to_int(data, data->tex_paths[EAST]);
	if (!data->textures[NORTH] || !data->textures[SOUTH]
		|| !data->textures[WEST] || !data->textures[EAST])
	{
		cleanup_textures(data, 4);
		return (ERR);
	}
	return (SUCCESS);
}
