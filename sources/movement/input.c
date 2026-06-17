/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   input.c                                            :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: rodrigo <rodrigo@student.42.fr>            +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/07 21:00:00 by cristian          #+#    #+#             */
/*   Updated: 2026/06/17 17:54:51 by rodrigo          ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "cub3d.h"

int	key_press(int keycode, t_data *data)
{
	t_player	*p;

	p = &data->player;
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
