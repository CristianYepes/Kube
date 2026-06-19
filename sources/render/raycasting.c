/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   raycasting.c                                       :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: rodrigo <rodrigo@student.42.fr>            +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/07 21:00:00 by cristian          #+#    #+#             */
/*   Updated: 2026/06/12 13:51:22 by rodrigo          ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "cub3d.h"

static void	init_ray(t_ray *ray, t_player *p, int x)
{
	double	camera_x;

	camera_x = 2.0 * x / (double)WIN_W - 1.0;
	ray->dir_x = p->dir_x + p->plane_x * camera_x;
	ray->dir_y = p->dir_y + p->plane_y * camera_x;
	ray->map_x = (int)p->pos_x;
	ray->map_y = (int)p->pos_y;
	ray->delta_x = fabs(1.0 / ray->dir_x);
	ray->delta_y = fabs(1.0 / ray->dir_y);
}

static void	init_step(t_ray *ray, t_player *p)
{
	if (ray->dir_x < 0)
	{
		ray->step_x = -1;
		ray->side_x = (p->pos_x - ray->map_x) * ray->delta_x;
	}
	else
	{
		ray->step_x = 1;
		ray->side_x = (ray->map_x + 1.0 - p->pos_x) * ray->delta_x;
	}
	if (ray->dir_y < 0)
	{
		ray->step_y = -1;
		ray->side_y = (p->pos_y - ray->map_y) * ray->delta_y;
	}
	else
	{
		ray->step_y = 1;
		ray->side_y = (ray->map_y + 1.0 - p->pos_y) * ray->delta_y;
	}
}

static void	perform_dda(t_data *data, t_ray *ray)
{
	ray->hit = 0;
	while (!ray->hit)
	{
		if (ray->side_x < ray->side_y)
		{
			ray->side_x += ray->delta_x;
			ray->map_x += ray->step_x;
			ray->side = 0;
		}
		else
		{
			ray->side_y += ray->delta_y;
			ray->map_y += ray->step_y;
			ray->side = 1;
		}
		if (ray->map_x < 0 || ray->map_x >= data->map_width
			|| ray->map_y < 0 || ray->map_y >= data->map_height)
			return ;
		if (data->map[ray->map_y][ray->map_x] == '1')
			ray->hit = 1;
	}
}

static void	draw_wall_column(t_data *data, t_ray *ray, int x)
{
	int	line_h;
	int	start;
	int	end;

	if (ray->side == 0)
		ray->wall_dist = ray->side_x - ray->delta_x;
	else
		ray->wall_dist = ray->side_y - ray->delta_y;
	line_h = (int)(WIN_H / ray->wall_dist);
	start = -line_h / 2 + WIN_H / 2;
	end = line_h / 2 + WIN_H / 2;
	while (start < end)
	{
		put_pixel(data, x, start, 0xFFFFFF);
		start++;
	}
}

void	cast_rays(t_data *data)
{
	t_ray	ray;
	int		x;

	x = 0;
	while (x < WIN_W)
	{
		init_ray(&ray, &data->player, x);
		init_step(&ray, &data->player);
		perform_dda(data, &ray);
		draw_wall_column(data, &ray, x);
		x++;
	}
}
