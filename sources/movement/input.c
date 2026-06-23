/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   input.c                                            :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: rodrigo <rodrigo@student.42.fr>            +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/07 21:00:00 by cristian          #+#    #+#             */
/*   Updated: 2026/06/22 22:18:43 by rodrigo          ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "cub3d.h"

int	key_press(int keycode, t_data *data)
{
	t_player	*p;

	p = &data->player;
	if (keycode == KEY_M)
	{
		if (p->minimap)
			p->minimap = 0;
		else
			p->minimap = 1;
	}
	if (keycode == KEY_W)
		p->key_up = 1;
	if (keycode == KEY_S)
		p->key_down = 1;
	if (keycode == KEY_A)
		p->key_left = 1;
	if (keycode == KEY_D)
		p->key_right = 1;
	if (keycode == KEY_LEFT)
		p->rotate_left = 1;
	if (keycode == KEY_RIGHT)
		p->rotate_right = 1;
	if (keycode == KEY_SHOOT)
		fire_shotgun(data);
	if (keycode == KEY_ESC)
		exit_game(data);
	return (0);
}

int	key_release(int keycode, t_data *data)
{
	t_player	*p;

	p = &data->player;
	if (keycode == KEY_W)
		p->key_up = 0;
	if (keycode == KEY_S)
		p->key_down = 0;
	if (keycode == KEY_A)
		p->key_left = 0;
	if (keycode == KEY_D)
		p->key_right = 0;
	if (keycode == KEY_LEFT)
		p->rotate_left = 0;
	if (keycode == KEY_RIGHT)
		p->rotate_right = 0;
	return (0);
}

int	mouse_click(int button, int x, int y, t_data *data)
{
	(void)x;
	(void)y;
	if (button == 1)
		fire_shotgun(data);
	return (0);
}

int	mouse_tracker(int x, int y, t_data *data)
{
	int	delta_x;

	(void)y;
	delta_x = x - WIN_W / 2;
	if (delta_x == 0)
		return (0);
	rotate_player(&data->player, (double)delta_x * 0.01);
	mlx_mouse_move(data->mlx, data->win, WIN_W / 2, WIN_H / 2);
	return (0);
}
