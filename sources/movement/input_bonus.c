/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   input_bonus.c                                      :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: cristian <cristian@student.42.fr>          +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/24 12:00:00 by cristian          #+#    #+#             */
/*   Updated: 2026/06/24 12:00:00 by cristian         ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "cub3d.h"

static void	handle_movement(int keycode, t_player *p, int state)
{
	if (keycode == KEY_W)
		p->key_up = state;
	if (keycode == KEY_S)
		p->key_down = state;
	if (keycode == KEY_A)
		p->key_left = state;
	if (keycode == KEY_D)
		p->key_right = state;
	if (keycode == KEY_LEFT)
		p->rotate_left = state;
	if (keycode == KEY_RIGHT)
		p->rotate_right = state;
}

int	key_press_bonus(int keycode, t_data *data)
{
	if (keycode == KEY_M)
		data->player.minimap = !data->player.minimap;
	if (keycode == KEY_E)
		toggle_door(data);
	if (keycode == KEY_SHOOT)
	{
		data->fire = 1;
		fire_shotgun(data);
	}
	if (keycode == KEY_ESC)
		exit_game(data);
	handle_movement(keycode, &data->player, 1);
	return (0);
}

int	mouse_click(int button, int x, int y, t_data *data)
{
	(void)x;
	(void)y;
	if (button == 1)
	{
		data->fire = 1;
		fire_shotgun(data);
	}
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
