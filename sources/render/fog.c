/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   fog.c                                              :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: cristian <cristian@student.42.fr>          +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/25 14:00:00 by cristian          #+#    #+#             */
/*   Updated: 2026/06/25 14:00:00 by cristian         ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "cub3d.h"

int	apply_fog(int color, double dist, int fog)
{
	double	f;
	int		r;
	int		g;
	int		b;

	if (!fog)
		return (color);
	f = dist / FOG_MAX;
	if (f > 1.0)
		f = 1.0;
	r = (int)(((color >> 16) & 0xFF) * (1.0 - f));
	g = (int)(((color >> 8) & 0xFF) * (1.0 - f));
	b = (int)((color & 0xFF) * (1.0 - f));
	return ((r << 16) | (g << 8) | b);
}
