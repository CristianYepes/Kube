/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   enemy_render.c                                     :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: cristian <cristian@student.42.fr>          +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/24 14:00:00 by cristian          #+#    #+#             */
/*   Updated: 2026/06/24 14:00:00 by cristian         ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "cub3d.h"

static void	project_enemy(t_data *data, t_enemy *e, t_sprite *s)
{
	double	sx;
	double	sy;
	double	inv;

	sx = e->pos_x - data->player.pos_x;
	sy = e->pos_y - data->player.pos_y;
	inv = 1.0 / (data->player.plane_x * data->player.dir_y
			- data->player.dir_x * data->player.plane_y);
	s->transform_x = inv * (data->player.dir_y * sx
			- data->player.dir_x * sy);
	s->transform_y = inv * (-data->player.plane_y * sx
			+ data->player.plane_x * sy);
	s->screen_x = (int)((WIN_W / 2)
			* (1 + s->transform_x / s->transform_y));
	s->size = (int)fabs(WIN_H / s->transform_y);
}

static void	draw_enemy_col(t_data *data, t_sprite *s, int x, int *tex)
{
	int	y;
	int	start_y;
	int	tex_x;
	int	color;

	start_y = -s->size / 2 + WIN_H / 2;
	tex_x = (x - (s->screen_x - s->size / 2)) * TEX_SIZE / s->size;
	y = start_y;
	while (y < s->size / 2 + WIN_H / 2)
	{
		if (y >= 0 && y < WIN_H)
		{
			color = tex[((y - start_y) * TEX_SIZE / s->size)
				* TEX_SIZE + tex_x];
			if (color != 0)
				put_pixel(data, x, y,
					apply_fog(color, s->transform_y, data->fog));
		}
		y++;
	}
}

static void	draw_enemy(t_data *data, t_sprite *s, int *tex)
{
	int	x;
	int	start_x;
	int	end_x;

	start_x = s->screen_x - s->size / 2;
	end_x = s->screen_x + s->size / 2;
	x = start_x;
	while (x < end_x)
	{
		if (x >= 0 && x < WIN_W
			&& s->transform_y < data->z_buffer[x])
			draw_enemy_col(data, s, x, tex);
		x++;
	}
}

void	render_enemies(t_data *data)
{
	int			i;
	t_sprite	proj;
	int			*tex;
	int			frame;

	frame = (int)(data->anim_clock * 4) % 2;
	i = 0;
	while (i < data->enemy_count)
	{
		project_enemy(data, &data->enemies[i], &proj);
		if (proj.transform_y > 0.1)
		{
			if (data->enemies[i].type == ENEMY_GRUNT
				|| data->enemies[i].type == ENEMY_BOSS)
				tex = data->sprite_tex[frame];
			else
				tex = data->sprite_tex2[frame];
			if (tex)
				draw_enemy(data, &proj, tex);
		}
		i++;
	}
}
