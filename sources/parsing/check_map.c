/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   check_map.c                                        :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: rodrigo <rodrigo@student.42.fr>            +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/17 20:42:30 by cristian          #+#    #+#             */
/*   Updated: 2026/06/22 22:59:12 by rodrigo          ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "cub3d.h"

static void	set_ns(t_player *p, char c)
{
	p->dir_x = 0;
	p->plane_y = 0;
	if (c == 'N')
	{
		p->dir_y = -1;
		p->plane_x = 0.66;
	}
	else
	{
		p->dir_y = 1;
		p->plane_x = -0.66;
	}
}

static void	set_ew(t_player *p, char c)
{
	p->dir_y = 0;
	p->plane_x = 0;
	if (c == 'E')
	{
		p->dir_x = 1;
		p->plane_y = 0.66;
	}
	else
	{
		p->dir_x = -1;
		p->plane_y = -0.66;
	}
}

static void	set_player_at(t_data *data, int i, int j)
{
	char	c;

	c = data->map[i][j];
	data->player.pos_x = j + 0.5;
	data->player.pos_y = i + 0.5;
	if (c == 'N' || c == 'S')
		set_ns(&data->player, c);
	else
		set_ew(&data->player, c);
	data->map[i][j] = '0';
}

static void	set_player_spawn(t_data *data)
{
	int	i;
	int	j;

	i = 0;
	while (i < data->map_height)
	{
		j = 0;
		while (data->map[i][j])
		{
			if (ft_strchr("NSEW", data->map[i][j]))
			{
				set_player_at(data, i, j);
				return ;
			}
			j++;
		}
		i++;
	}
}

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
			if (ft_strchr("0123NSEW", data->map[i][j]) == NULL)
				return (err_msg(NULL, ERR_INVALID_CHAR, FAILURE));
			if (ft_strchr("NSEW", data->map[i][j]) != NULL)
				count++;
			j++;
		}
		i++;
	}
	if (count != 1)
		return (err_msg(NULL, ERR_PLAYER_COUNT, FAILURE));
	set_player_spawn(data);
	return (SUCCESS);
}
