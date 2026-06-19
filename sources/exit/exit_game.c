/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   exit_game.c                                        :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: cristian <cristian@student.42.fr>          +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/07 21:00:00 by cristian          #+#    #+#             */
/*   Updated: 2026/06/19 13:00:00 by cristian         ###   ########.fr       */
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

int	close_window(t_data *data)
{
	exit_game(data);
	return (0);
}

void	exit_game(t_data *data)
{
	free_textures(data);
	if (data->img.img)
		mlx_destroy_image(data->mlx, data->img.img);
	if (data->win)
		mlx_destroy_window(data->mlx, data->win);
	free_parsing(data);
	exit(SUCCESS);
}
