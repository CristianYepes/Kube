/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   main.c                                             :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: cristian <cristian@student.42.fr>          +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/05/24 23:22:57 by cristian          #+#    #+#             */
/*   Updated: 2026/05/30 23:21:55 by cristian         ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "cub3d.h"

int	main(int argc, char *argv[])
{
	if (argc != 2)
		return (err_msg(NULL, ERR_USAGE, FAILURE));
	if (check_file(argv[1]) == FAILURE)
		return (FAILURE);
	return (SUCCESS);
}
