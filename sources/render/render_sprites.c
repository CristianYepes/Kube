/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   render_sprites.c                                   :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: rodrigo <rodrigo@student.42.fr>            +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/23 00:21:02 by rodrigo           #+#    #+#             */
/*   Updated: 2026/06/23 00:47:03 by rodrigo          ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "cub3d.h"

static void	draw_sprite_col(t_data *data, t_sprite *s, int x)
{
	int	y;
	int	start_y;
	int	tex_x;
	int	tex_y;
	int	color;

	start_y = -s->size / 2 + WIN_H / 2;
	tex_x = (x - (s->screen_x - s->size / 2)) * TEX_SIZE / s->size;
	y = start_y;
	while (y < s->size / 2 + WIN_H / 2)
	{
		if (y >= 0 && y < WIN_H)
		{
			tex_y = (y - start_y) * TEX_SIZE / s->size;
			if (s->type == 0)
				color = data->sprite_tex[s->frame_idx]
					[tex_y * TEX_SIZE + tex_x];
			else
				color = data->sprite_tex2[s->frame_idx]
					[tex_y * TEX_SIZE + tex_x];
			if (color != 0)
				put_pixel(data, x, y, color);
		}
		y++;
	}
}

static void	draw_sprite_3d(t_data *data, int i)
{
	int			x;
	int			start_x;
	int			end_x;
	t_sprite	*s;

	s = &data->sprites[i];
	start_x = s->screen_x - s->size / 2;
	end_x = s->screen_x + s->size / 2;
	x = start_x;
	while (x < end_x)
	{
		if (x >= 0 && x < WIN_W
			&& s->transform_y < data->z_buffer[x])
			draw_sprite_col(data, s, x);
		x++;
	}
}

void	project_sprite(t_data *data, int i)
{
	double	sx;
	double	sy;
	double	inv;

	sx = data->sprites[i].pos_x - data->player.pos_x;
	sy = data->sprites[i].pos_y - data->player.pos_y;
	inv = 1.0 / (data->player.plane_x * data->player.dir_y
			- data->player.dir_x * data->player.plane_y);
	data->sprites[i].transform_x = inv * (data->player.dir_y * sx
			- data->player.dir_x * sy);
	data->sprites[i].transform_y = inv * (-data->player.plane_y * sx
			+ data->player.plane_x * sy);
	data->sprites[i].screen_x = (int)((WIN_W / 2)
			* (1 + data->sprites[i].transform_x
				/ data->sprites[i].transform_y));
	data->sprites[i].size = abs((int)(WIN_H
				/ data->sprites[i].transform_y));
}

void	render_sprites(t_data *data)
{
	int	i;

	if (!data->sprites || data->sprite_count == 0)
		return ;
	i = 0;
	while (i < data->sprite_count)
	{
		project_sprite(data, i);
		if (data->sprites[i].transform_y > 0)
			draw_sprite_3d(data, i);
		i++;
	}
}
