/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   agent.h                                            :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: cristian <cristian@student.42.fr>          +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/10/05 18:03:13 by cristian          #+#    #+#             */
/*   Updated: 2026/10/05 18:03:13 by cristian         ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#ifndef AGENT_H
# define AGENT_H
# include "cub3d.h"

/*
** The bridge between cub3D_agent and the Python agent (spec 002).
** One observation line must stay under PIPE_BUF: on Linux a pipe write of at
** most 4096 bytes is all or nothing, so a line is never cut in half.
*/
# define OBS_MAX 4096

/* What agent_print_obs counts across frames (frames start at 1). */
typedef struct s_obs_counts
{
	unsigned int	frame;
	unsigned int	drops;
}					t_obs_counts;

/*
** A command line is "C" and seven flags, 15 characters, so a longer one is
** garbage. At most CMD_READ bytes are read per frame, so a flood of input
** cannot hold a frame back; what is left waits for the next one.
*/
# define CMD_MAX 256
# define CMD_READ 1024

/* What agent_read_commands remembers from one frame to the next. */
typedef struct s_cmd_reader
{
	char			line[CMD_MAX];
	int				len;
	int				overflow;
	int				fire;
	int				checked;
	int				is_tty;
}					t_cmd_reader;

void				agent_init_io(t_data *data);
void				agent_print_obs(t_data *data);
void				agent_read_commands(t_data *data);
void				agent_fail(t_data *data, char *what, char *why);

#endif
