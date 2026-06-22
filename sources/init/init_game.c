/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   init_game.c                                        :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: cristian <cristian@student.42.fr>          +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/07 21:00:00 by cristian          #+#    #+#             */
/*   Updated: 2026/06/19 12:00:00 by cristian         ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "cub3d.h"

int	init_game(t_data *data)
{
	init_player(&data->player);
	data->mlx = mlx_init();
	if (!data->mlx)
		return (err_msg(NULL, "MLX init failed", FAILURE));
	data->win = mlx_new_window(data->mlx, WIN_W, WIN_H, "cub3D");
	if (!data->win)
		return (err_msg(NULL, "MLX window failed", FAILURE));
	data->img.img = mlx_new_image(data->mlx, WIN_W, WIN_H);
	if (!data->img.img)
		return (err_msg(NULL, "MLX image failed", FAILURE));
	data->img.addr = mlx_get_data_addr(data->img.img, &data->img.bpp,
			&data->img.size_line, &data->img.endian);
	if (init_textures(data) == ERR)
	{
		mlx_destroy_image(data->mlx, data->img.img);
		mlx_destroy_window(data->mlx, data->win);
		return (err_msg(NULL, "Texture load failed", FAILURE));
	}
	return (SUCCESS);
}
