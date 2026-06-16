/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   main.c                                             :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: cristian <cristian@student.42.fr>          +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/05/24 23:22:57 by cristian          #+#    #+#             */
/*   Updated: 2026/06/16 23:34:31 by cristian         ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "cub3d.h"

int	main(int argc, char *argv[])
{
	t_data	data;

	data = (t_data){0};
	if (argc != 2)
		return (err_msg(NULL, ERR_USAGE, FAILURE));
	if (check_file(argv[1]) == FAILURE)
		return (FAILURE);
	if (parsing(argv[1], &data) == FAILURE)
		return (FAILURE);
	init_game(&data);
	mlx_hook(data.win, 2, 1L << 0, key_press, &data);
	mlx_hook(data.win, 3, 1L << 1, key_release, &data);
	mlx_hook(data.win, 17, 0L, close_window, &data);
	mlx_loop_hook(data.mlx, game_loop, &data);
	mlx_loop(data.mlx);
	return (SUCCESS);
}
