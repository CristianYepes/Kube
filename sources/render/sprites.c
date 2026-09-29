/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   sprites.c                                          :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: rodrigo <rodrigo@student.42.fr>            +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/22 23:07:03 by rodrigo           #+#    #+#             */
/*   Updated: 2026/06/23 00:20:30 by rodrigo          ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "cub3d.h"

int	sprites_counter(char type, t_data *data)
{
	char	**map;
	int		counter;
	int		x;
	int		y;

	counter = 0;
	map = data->map;
	y = 0;
	while (map[y])
	{
		x = 0;
		while (map[y][x])
		{
			if (map[y][x] == type)
				counter++;
			x++;
		}
		y++;
	}
	return (counter);
}

static void	set_sprite(t_data *data, int counter, int x, int y)
{
	data->sprites[counter].pos_x = x + 0.5;
	data->sprites[counter].pos_y = y + 0.5;
}

void	init_sprites(char type, t_data *data)
{
	char	**map;
	int		counter;
	int		x;
	int		y;

	(void)type;
	counter = 0;
	map = data->map;
	y = 0;
	while (map[y])
	{
		x = 0;
		while (map[y][x])
		{
			if (map[y][x] == '2')
				set_sprite(data, counter++, x, y);
			x++;
		}
		y++;
	}
}

void	compute_sprite_distances(t_data *data)
{
	int		i;
	double	dx;
	double	dy;

	i = 0;
	while (i < data->sprite_count)
	{
		dx = data->player.pos_x - data->sprites[i].pos_x;
		dy = data->player.pos_y - data->sprites[i].pos_y;
		data->sprites[i].distance = dx * dx + dy * dy;
		i++;
	}
}

void	sort_sprites(t_data *data)
{
	int			i;
	int			j;
	t_sprite	tmp;

	i = 1;
	while (i < data->sprite_count)
	{
		tmp = data->sprites[i];
		j = i - 1;
		while (j >= 0 && data->sprites[j].distance < tmp.distance)
		{
			data->sprites[j + 1] = data->sprites[j];
			j--;
		}
		data->sprites[j + 1] = tmp;
		i++;
	}
}
