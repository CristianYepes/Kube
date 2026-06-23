/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   mlx.c                                              :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: rodrigo <rodrigo@student.42.fr>            +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/22 21:35:56 by rodrigo           #+#    #+#             */
/*   Updated: 2026/06/23 12:53:30 by rodrigo          ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "cub3d.h"

void	loop(t_data *data)
{
	mlx_hook(data->win, 2, 1L << 0, key_press, data);
	mlx_hook(data->win, 3, 1L << 1, key_release, data);
	mlx_hook(data->win, 4, 1L << 2, mouse_click, data);
	mlx_hook(data->win, 6, 1L << 6, mouse_tracker, data);
	mlx_hook(data->win, 17, 0L, close_window, data);
	gettimeofday(&data->last_time, NULL);
	mlx_loop_hook(data->mlx, game_loop, data);
	mlx_loop(data->mlx);
}
