/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   draw_wall.c                                        :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: rodrigo <rodrigo@student.42.fr>            +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/19 13:00:00 by cristian          #+#    #+#             */
/*   Updated: 2026/06/22 22:34:25 by rodrigo          ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "cub3d.h"

static int	get_tex_index(t_ray *ray)
{
	if (ray->side == 0)
	{
		if (ray->dir_x > 0)
			return (EAST);
		return (WEST);
	}
	if (ray->dir_y > 0)
		return (SOUTH);
	return (NORTH);
}

static int	get_tex_x(t_data *data, t_ray *ray)
{
	double	wall_x;
	int		tex_x;

	if (ray->side == 0)
		wall_x = data->player.pos_y + ray->wall_dist * ray->dir_y;
	else
		wall_x = data->player.pos_x + ray->wall_dist * ray->dir_x;
	wall_x -= floor(wall_x);
	tex_x = (int)(wall_x * TEX_SIZE);
	if (ray->side == 0 && ray->dir_x > 0)
		tex_x = TEX_SIZE - tex_x - 1;
	if (ray->side == 1 && ray->dir_y < 0)
		tex_x = TEX_SIZE - tex_x - 1;
	return (tex_x);
}

static int	get_tex_color(t_data *data, t_ray *ray, double tex_pos)
{
	int	tex_y;
	int	color;

	tex_y = (int)tex_pos & (TEX_SIZE - 1);
	if (ray->is_door && data->door_tex)
		color = data->door_tex[TEX_SIZE * tex_y + ray->tex_x];
	else
		color = data->textures[ray->tex_idx][TEX_SIZE * tex_y + ray->tex_x];
	if (!ray->is_door && (ray->tex_idx == NORTH || ray->tex_idx == EAST))
		color = (color >> 1) & 0x7F7F7F;
	color = apply_fog(color, ray->wall_dist, data->fog);
	return (color);
}

static void	paint_column(t_data *data, t_ray *ray, int x)
{
	int		start;
	int		end;
	double	step;
	double	tex_pos;

	start = -ray->line_h / 2 + WIN_H / 2;
	end = ray->line_h / 2 + WIN_H / 2;
	if (start < 0)
		start = 0;
	if (end > WIN_H)
		end = WIN_H;
	step = (double)TEX_SIZE / ray->line_h;
	tex_pos = (start - WIN_H / 2 + ray->line_h / 2) * step;
	while (start < end)
	{
		put_pixel(data, x, start, get_tex_color(data, ray, tex_pos));
		tex_pos += step;
		start++;
	}
}

void	draw_wall_column(t_data *data, t_ray *ray, int x)
{
	if (!ray->hit)
	{
		data->z_buffer[x] = 1e30;
		return ;
	}
	if (ray->side == 0)
		ray->wall_dist = ray->side_x - ray->delta_x;
	else
		ray->wall_dist = ray->side_y - ray->delta_y;
	if (ray->wall_dist < 0.0001)
		ray->wall_dist = 0.0001;
	data->z_buffer[x] = ray->wall_dist;
	ray->line_h = (int)(WIN_H / ray->wall_dist);
	ray->is_door = (data->map[ray->map_y][ray->map_x] == DOOR_CLOSED);
	ray->tex_idx = get_tex_index(ray);
	ray->tex_x = get_tex_x(data, ray);
	paint_column(data, ray, x);
}
