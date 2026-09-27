/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   exit_game.c                                        :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: cristian <cristian@student.42.fr>          +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/07 21:00:00 by cristian          #+#    #+#             */
/*   Updated: 2026/06/24 12:00:00 by cristian         ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "cub3d.h"

static void	free_textures(t_data *data)
{
	int	i;

	i = 0;
	while (i < 4)
	{
		if (data->textures[i])
			free(data->textures[i]);
		i++;
	}
}

void	destroy_game(t_data *data)
{
	free_textures(data);
	free_sprites(data);
	free_shotgun(data);
	if (data->door_tex)
		free(data->door_tex);
	if (data->enemies)
		free(data->enemies);
	if (data->z_buffer)
		free(data->z_buffer);
	if (data->img.img)
		mlx_destroy_image(data->mlx, data->img.img);
	if (data->win)
		mlx_destroy_window(data->mlx, data->win);
}

int	close_window(t_data *data)
{
	exit_game(data);
	return (0);
}

void	exit_game(t_data *data)
{
	destroy_game(data);
	free_parsing(data);
	exit(SUCCESS);
}
