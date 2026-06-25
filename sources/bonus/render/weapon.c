/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   weapon.c                                           :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: cristian <cristian@student.42.fr>          +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/24 14:00:00 by cristian          #+#    #+#             */
/*   Updated: 2026/06/25 14:00:00 by cristian         ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "cub3d.h"

static void	draw_block(t_data *data, int px, int py, int col)
{
	int	x;
	int	y;

	y = 0;
	while (y < 3)
	{
		x = 0;
		while (x < 3)
		{
			put_pixel(data, px + x, py + y, col);
			x++;
		}
		y++;
	}
}

static void	draw_glyph(t_data *data, int bits, int px)
{
	int	r;
	int	c;
	int	py;

	py = WIN_H - 60;
	r = 0;
	while (r < 5)
	{
		c = 0;
		while (c < 3)
		{
			if ((bits >> (r * 3 + c)) & 1)
				draw_block(data, px + c * 3, py + r * 3, 0xFFFF00);
			c++;
		}
		r++;
	}
}

void	render_weapon(t_data *data)
{
	int	x;

	x = WIN_W / 2 - 16;
	draw_glyph(data, 448, x);
	draw_glyph(data, 18925, x + 11);
	draw_glyph(data, 29671, x + 22);
}
