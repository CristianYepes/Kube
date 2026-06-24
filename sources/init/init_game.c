/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   init_game.c                                        :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: cristian <cristian@student.42.fr>          +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/07 21:00:00 by cristian          #+#    #+#             */
/*   Updated: 2026/06/24 12:00:00 by cristian         ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "cub3d.h"

static int	init_mlx(t_data *data)
{
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
	return (SUCCESS);
}

#ifdef BONUS

static int	init_bonus_assets(t_data *data)
{
	data->door_tex = xpm_to_int(data, "textures/door.xpm");
	if (!data->door_tex)
		data->door_tex = xpm_to_int(data, data->tex_paths[WEST]);
	if (init_sprites_data(data) == FAILURE)
		return (err_msg(NULL, "Sprite init failed", FAILURE));
	if (init_shotgun(data) == FAILURE)
		return (err_msg(NULL, "Shotgun init failed", FAILURE));
	return (SUCCESS);
}

int	init_game(t_data *data)
{
	init_player(&data->player);
	if (init_mlx(data) == FAILURE)
		return (FAILURE);
	data->z_buffer = malloc(sizeof(double) * WIN_W);
	if (!data->z_buffer)
	{
		destroy_game(data);
		return (err_msg(NULL, "Z-buffer alloc failed", FAILURE));
	}
	if (init_textures(data) != SUCCESS)
	{
		destroy_game(data);
		return (err_msg(NULL, "Texture load failed", FAILURE));
	}
	if (init_bonus_assets(data) != SUCCESS)
	{
		destroy_game(data);
		return (FAILURE);
	}
	return (SUCCESS);
}
#else

int	init_game(t_data *data)
{
	init_player(&data->player);
	if (init_mlx(data) == FAILURE)
		return (FAILURE);
	data->z_buffer = malloc(sizeof(double) * WIN_W);
	if (!data->z_buffer)
	{
		destroy_game(data);
		return (err_msg(NULL, "Z-buffer alloc failed", FAILURE));
	}
	if (init_textures(data) != SUCCESS)
	{
		destroy_game(data);
		return (err_msg(NULL, "Texture load failed", FAILURE));
	}
	return (SUCCESS);
}
#endif
