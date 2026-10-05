/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   agent_loop.c                                       :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: cristian <cristian@student.42.fr>          +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/10/05 17:50:08 by cristian          #+#    #+#             */
/*   Updated: 2026/10/05 17:50:08 by cristian         ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "cub3d.h"

/*
** Replaces sources/mlx_loop_and_hook/mlx.c in cub3D_agent. It is the bonus
** loop() at the base (0ac5649) without the key and mouse hooks: nobody types
** or clicks, a program drives the player. Closing the window still works.
*/

void	loop(t_data *data)
{
	mlx_hook(data->win, 17, 0L, close_window, data);
	gettimeofday(&data->last_time, NULL);
	mlx_loop_hook(data->mlx, game_loop, data);
	mlx_loop(data->mlx);
}
