/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   agent_cmd.c                                        :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: cristian <cristian@student.42.fr>          +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/10/05 22:50:36 by cristian          #+#    #+#             */
/*   Updated: 2026/10/05 22:50:36 by cristian         ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "agent.h"

/* "C 1 0 0 0 0 0 0": a C, then seven flags, each 0 or 1 after one space. */
static int	is_move_line(const char *s, int len)
{
	int	i;

	if (len != 15 || s[0] != 'C')
		return (0);
	i = 0;
	while (i < 7)
	{
		if (s[1 + 2 * i] != ' ')
			return (0);
		if (s[2 + 2 * i] != '0' && s[2 + 2 * i] != '1')
			return (0);
		i++;
	}
	return (1);
}

/*
** One complete line. "Q" quits cleanly. A move line sets the keys: its flags
** are forward, back, strafe left, strafe right, turn left, turn right, and
** the fire, which stays held until the next line. Anything else is ignored
** with a warning, so a bug on the writer's side does not go unseen.
*/
static void	apply_line(t_data *data, t_cmd_reader *r)
{
	t_player	*p;
	char		*s;

	s = r->line;
	if (!r->overflow && r->len == 1 && s[0] == 'Q')
		exit_game(data);
	if (r->overflow || !is_move_line(s, r->len))
	{
		err_msg(s, "ignored: not a command", 0);
		return ;
	}
	p = &data->player;
	p->key_up = s[2] - '0';
	p->key_down = s[4] - '0';
	p->key_left = s[6] - '0';
	p->key_right = s[8] - '0';
	p->rotate_left = s[10] - '0';
	p->rotate_right = s[12] - '0';
	r->fire = s[14] - '0';
}

/*
** One byte of input. A line ends at '\n'. A line longer than the buffer keeps
** only its start and is marked, so it is dropped as a whole at its end.
*/
static void	feed(t_data *data, t_cmd_reader *r, char c)
{
	if (c != '\n')
	{
		if (r->len < CMD_MAX - 1)
			r->line[r->len++] = c;
		else
			r->overflow = 1;
		return ;
	}
	r->line[r->len] = '\0';
	apply_line(data, r);
	r->len = 0;
	r->overflow = 0;
}

/*
** What stdin holds now, or 0 bytes if nothing is new. End of input means the
** Python side is gone, so the game exits cleanly: it must not outlive its
** driver. A terminal is never read: the read would wait for a key and freeze
** the game.
*/
static ssize_t	pull(t_data *data, t_cmd_reader *r, char *buf)
{
	ssize_t	n;

	if (!r->checked)
	{
		r->checked = 1;
		r->is_tty = isatty(STDIN_FILENO);
	}
	if (r->is_tty)
		return (0);
	n = read(STDIN_FILENO, buf, CMD_READ);
	if (n == 0)
		exit_game(data);
	if (n < 0 && errno != EAGAIN && errno != EINTR)
		agent_fail(data, "stdin", strerror(errno));
	if (n < 0)
		return (0);
	return (n);
}

/*
** Called first in every frame. Commands stay in force until the next one, so
** a held fire is renewed here each frame, as if the key were still down:
** fire_shotgun() is what the Up key calls, and try_fire() in update_sim()
** applies the cooldown.
*/
void	agent_read_commands(t_data *data)
{
	static t_cmd_reader	r;
	char				buf[CMD_READ];
	ssize_t				n;
	ssize_t				i;

	n = pull(data, &r, buf);
	i = 0;
	while (i < n)
	{
		feed(data, &r, buf[i]);
		i++;
	}
	if (r.fire)
	{
		data->fire = 1;
		fire_shotgun(data);
	}
}
