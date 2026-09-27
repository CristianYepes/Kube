/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   input.c                                            :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: cristian <cristian@student.42.fr>          +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/07 21:00:00 by cristian          #+#    #+#             */
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

int	key_press(int keycode, t_data *data)
{
	if (keycode == KEY_ESC)
		exit_game(data);
	handle_movement(keycode, &data->player, 1);
	return (0);
}

int	key_release(int keycode, t_data *data)
{
	handle_movement(keycode, &data->player, 0);
	return (0);
}
