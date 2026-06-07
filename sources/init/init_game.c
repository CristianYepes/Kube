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

static char	**get_temp_map(void)
{
	char	**map;

	map = malloc(sizeof(char *) * 11);
	if (!map)
		return (NULL);
	map[0] = "111111111111111";
	map[1] = "100000000000001";
	map[2] = "100000000000001";
	map[3] = "100000100000001";
	map[4] = "100000000000001";
	map[5] = "100000010000001";
	map[6] = "100001000000001";
	map[7] = "100000000000001";
	map[8] = "100000000000001";
	map[9] = "111111111111111";
	map[10] = NULL;
	return (map);
}

void	init_game(t_data *data)
{
	init_player(&data->player);
	data->map = get_temp_map();
	data->mlx = mlx_init();
	data->win = mlx_new_window(data->mlx, WIN_W, WIN_H, "cub3D");
	data->img.img = mlx_new_image(data->mlx, WIN_W, WIN_H);
	data->img.addr = mlx_get_data_addr(data->img.img, &data->img.bpp,
			&data->img.size_line, &data->img.endian);
}
