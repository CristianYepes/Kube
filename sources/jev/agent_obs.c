/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   agent_obs.c                                        :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: cristian <cristian@student.42.fr>          +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/10/05 18:03:40 by cristian          #+#    #+#             */
/*   Updated: 2026/10/05 18:03:40 by cristian         ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "agent.h"

/* len + n, or a loud exit when snprintf had to cut the line. */
static int	grow(t_data *data, int len, int n)
{
	if (n < 0 || n >= OBS_MAX - len)
		agent_fail(data, "observation", "line longer than 4096 bytes");
	return (len + n);
}

/*
** The line up to the opening of the enemies list. t is the game's own clock:
** the sum of the frames' dt (each at most 0.05 s), the one the simulation runs
** on. weapon_ready is 1 while the weapon is idle. Floats take three decimals.
*/
static int	put_head(char *buf, t_data *data, t_obs_counts *c)
{
	int	n;

	n = snprintf(buf, OBS_MAX,
			"{\"type\":\"obs\",\"frame\":%u,\"t\":%.3f,\"dt\":%.3f,"
			"\"state\":%d,\"wave\":%d,\"hp\":%d,\"weapon_ready\":%d,"
			"\"player\":{\"x\":%.3f,\"y\":%.3f,\"dx\":%.3f,\"dy\":%.3f},"
			"\"drops\":%u,\"enemies\":[",
			c->frame, data->anim_clock, data->dt, data->game_state,
			data->wave, data->player_hp, data->weapon.state == W_IDLE,
			data->player.pos_x, data->player.pos_y,
			data->player.dir_x, data->player.dir_y, c->drops);
	return (grow(data, 0, n));
}

/* One enemy. los is the game's own has_los(), so Python does not redo it. */
static int	put_enemy(char *buf, int len, t_data *data, int i)
{
	t_enemy	*e;
	char	*sep;
	int		n;

	e = &data->enemies[i];
	sep = "";
	if (i > 0)
		sep = ",";
	n = snprintf(buf + len, OBS_MAX - len,
			"%s{\"x\":%.3f,\"y\":%.3f,\"type\":%d,\"hp\":%d,\"ai\":%d,"
			"\"los\":%d}", sep, e->pos_x, e->pos_y, e->type, e->hp,
			e->state, has_los(data, e->pos_x, e->pos_y));
	return (grow(data, len, n));
}

static int	build_line(char *buf, t_data *data, t_obs_counts *c)
{
	int	len;
	int	i;

	len = put_head(buf, data, c);
	i = 0;
	while (i < data->enemy_count)
	{
		len = put_enemy(buf, len, data, i);
		i++;
	}
	return (grow(data, len, snprintf(buf + len, OBS_MAX - len, "]}\n")));
}

/*
** One observation per frame, in a single write. A full pipe (EAGAIN) costs
** the line and adds one to drops, which the next line reports. Any other
** result, a half-written line included, ends the run: nothing is cut silently.
*/
void	agent_print_obs(t_data *data)
{
	static t_obs_counts	counts;
	char				line[OBS_MAX];
	int					len;
	ssize_t				sent;

	counts.frame++;
	len = build_line(line, data, &counts);
	sent = write(STDOUT_FILENO, line, len);
	if (sent == len)
		return ;
	if (sent < 0 && errno == EAGAIN)
	{
		counts.drops++;
		return ;
	}
	if (sent < 0)
		agent_fail(data, "stdout", strerror(errno));
	agent_fail(data, "stdout", "short write: half an observation line");
}
