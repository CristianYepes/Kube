/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   init_game.c                                        :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: cristian <cristian@student.42.fr>          +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/07 21:00:00 by cristian          #+#    #+#             */
/*   Updated: 2026/06/07 21:00:00 by cristian         ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "cub3d.h"

void	init_game(t_data *data)
{
	init_player(&data->player);
	data->mlx = mlx_init();
	data->win = mlx_new_window(data->mlx, WIN_W, WIN_H, "cub3D");
	data->img.img = mlx_new_image(data->mlx, WIN_W, WIN_H);
	data->img.addr = mlx_get_data_addr(data->img.img, &data->img.bpp,
			&data->img.size_line, &data->img.endian);
	if (init_textures(data) == ERR)
		exit_game(data);
}
