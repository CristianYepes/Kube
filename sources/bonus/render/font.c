/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   font.c                                             :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: cristian <cristian@student.42.fr>          +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/25 18:00:00 by cristian          #+#    #+#             */
/*   Updated: 2026/06/25 18:00:00 by cristian         ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "cub3d.h"

static const unsigned char	*font_table(void)
{
	static const unsigned char	t[91] = {
		0x11, 0x11, 0x11, 0x0A, 0x04, 0x04, 0x04,
		0x0E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E,
		0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E,
		0x11, 0x11, 0x11, 0x15, 0x15, 0x1B, 0x11,
		0x1F, 0x04, 0x04, 0x04, 0x04, 0x04, 0x1F,
		0x11, 0x19, 0x15, 0x13, 0x11, 0x11, 0x11,
		0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x1F,
		0x0E, 0x11, 0x10, 0x0E, 0x01, 0x11, 0x0E,
		0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x1F,
		0x1E, 0x11, 0x11, 0x1E, 0x10, 0x10, 0x10,
		0x1E, 0x11, 0x11, 0x1E, 0x14, 0x12, 0x11,
		0x1F, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04,
		0x0E, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11
	};

	return (t);
}

static const unsigned char	*glyph_rows(char c)
{
	static const char	set[] = "YOUWINLSEPRTA";
	int					i;

	i = 0;
	while (set[i])
	{
		if (set[i] == c)
			return (font_table() + i * 7);
		i++;
	}
	return (NULL);
}

static void	fill_block(t_data *data, int bx, int by, int color)
{
	int	i;
	int	j;

	i = 0;
	while (i < FONT_SCALE)
	{
		j = 0;
		while (j < FONT_SCALE)
		{
			put_pixel(data, bx + j, by + i, color);
			j++;
		}
		i++;
	}
}

static void	draw_glyph(t_data *data, const unsigned char *rows, int *xy,
		int color)
{
	int	r;
	int	c;

	r = 0;
	while (r < 7)
	{
		c = 0;
		while (c < 5)
		{
			if (rows[r] & (1 << (4 - c)))
				fill_block(data, xy[0] + c * FONT_SCALE,
					xy[1] + r * FONT_SCALE, color);
			c++;
		}
		r++;
	}
}

void	draw_text(t_data *data, char *s, int y, int color)
{
	int					xy[2];
	const unsigned char	*g;

	xy[0] = WIN_W / 2 - (int)(ft_strlen(s) * 6 * FONT_SCALE / 2);
	xy[1] = y;
	while (*s)
	{
		g = glyph_rows(*s);
		if (g)
			draw_glyph(data, g, xy, color);
		xy[0] += 6 * FONT_SCALE;
		s++;
	}
}
