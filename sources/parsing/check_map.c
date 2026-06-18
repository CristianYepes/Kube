/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   check_map.c                                        :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: cristian <cristian@student.42.fr>          +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 20:42:30 by cristian          #+#    #+#             */
/*   Updated: 2026/06/18 21:12:32 by cristian         ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "cub3d.h"

int	check_map(t_data *data)
{
	int	i;
	int	j;
	int	count;

	i = 0;
	count = 0;
	while (i < data->map_height)
	{
		j = 0;
		while (data->map[i][j])
		{
			if (ft_strchr("01NSEW", data->map[i][j]) == NULL)
				return (err_msg(NULL, ERR_INVALID_CHAR, FAILURE));
			if (ft_strchr("NSEW", data->map[i][j]) != NULL)
				count++;
			j++;
		}
		i++;
	}
	if (count != 1)
		return (err_msg(NULL, ERR_PLAYER_COUNT, FAILURE));
	return (SUCCESS);
}
