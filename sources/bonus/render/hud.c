/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   hud.c                                              :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: cristian <cristian@student.42.fr>          +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/24 14:00:00 by cristian          #+#    #+#             */
/*   Updated: 2026/06/24 14:00:00 by cristian         ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "cub3d.h"

static void	draw_hp_bar(t_data *data)
{
	int	x;
	int	y;
	int	width;
	int	color;

	width = data->player_hp * 2;
	if (width < 0)
		width = 0;
	y = WIN_H - 30;
	while (y < WIN_H - 15)
	{
		x = WIN_W - 220;
		while (x < WIN_W - 220 + width)
		{
			color = 0x00FF00;
			if (data->player_hp < 30)
				color = 0xFF0000;
			else if (data->player_hp < 60)
				color = 0xFFFF00;
			put_pixel(data, x, y, color);
			x++;
		}
		y++;
	}
}

static void	draw_wave_dots(t_data *data)
{
	int	i;
	int	x;
	int	y;

	i = 0;
	while (i < data->wave)
	{
		y = WIN_H - 45;
		while (y < WIN_H - 35)
		{
			x = WIN_W - 220 + i * 15;
			while (x < WIN_W - 210 + i * 15)
			{
				put_pixel(data, x, y, 0xFFFFFF);
				x++;
			}
			y++;
		}
		i++;
	}
}

static void	draw_game_over(t_data *data, int color)
{
	int	x;
	int	y;

	y = WIN_H / 2 - 75;
	while (y < WIN_H / 2 + 75)
	{
		x = WIN_W / 2 - 300;
		while (x < WIN_W / 2 + 300)
		{
			put_pixel(data, x, y, color);
			x++;
		}
		y++;
	}
}

void	render_hud(t_data *data)
{
	if (data->game_state == G_OVER)
	{
		draw_game_over(data, 0x440000);
		draw_text(data, "YOU LOSE", WIN_H / 2 - 55, 0xFF4444);
		draw_text(data, "PRESS R TO RESTART", WIN_H / 2 + 20, 0xFFFFFF);
		return ;
	}
	if (data->game_state == G_WIN)
	{
		draw_game_over(data, 0x004400);
		draw_text(data, "YOU WIN", WIN_H / 2 - 55, 0x44FF44);
		draw_text(data, "PRESS R TO RESTART", WIN_H / 2 + 20, 0xFFFFFF);
		return ;
	}
	draw_hp_bar(data);
	draw_wave_dots(data);
}
