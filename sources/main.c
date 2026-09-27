/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   main.c                                             :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: rodrigo <rodrigo@student.42.fr>            +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/05/24 23:22:57 by cristian          #+#    #+#             */
/*   Updated: 2026/06/22 21:47:21 by rodrigo          ###   ########.fr       */
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
	if (init_game(&data) != SUCCESS)
	{
		free_parsing(&data);
		return (FAILURE);
	}
	loop(&data);
	return (SUCCESS);
}
