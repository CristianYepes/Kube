/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   agent_frame.c                                      :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: cristian <cristian@student.42.fr>          +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/10/05 17:50:16 by cristian          #+#    #+#             */
/*   Updated: 2026/10/05 17:50:16 by cristian         ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "agent.h"

/*
** Replaces sources/render/game_loop.c in cub3D_agent. It is the bonus frame
** at the base (0ac5649) plus two calls: agent_read_commands() first, so the
** keys the Python agent asked for are in place before the player moves, and
** agent_print_obs() once the frame is shown, to print its state.
*/

static void	tick_clock(t_data *data)
{
	struct timeval	now;

	gettimeofday(&now, NULL);
	data->dt = (now.tv_sec - data->last_time.tv_sec)
		+ (now.tv_usec - data->last_time.tv_usec) / 1000000.0;
	if (data->dt < 0)
		data->dt = 0;
	if (data->dt > 0.05)
		data->dt = 0.05;
	data->last_time = now;
	data->anim_clock += data->dt;
}

int	game_loop(t_data *data)
{
	agent_read_commands(data);
	tick_clock(data);
	if (data->game_state == G_PLAY)
	{
		move_player(data);
		update_sim(data);
	}
	paint_floor_ceiling(data);
	cast_rays(data);
	render_sprites(data);
	render_enemies(data);
	if (data->game_state == G_PLAY)
	{
		tick_shotgun(data, data->dt);
		draw_shotgun(data);
	}
	render_hud(data);
	if (data->player.minimap)
		display_minimap(data);
	mlx_put_image_to_window(data->mlx, data->win, data->img.img, 0, 0);
	agent_print_obs(data);
	return (0);
}
