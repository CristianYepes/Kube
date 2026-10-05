/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   agent_io.c                                         :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: cristian <cristian@student.42.fr>          +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/10/05 18:03:22 by cristian          #+#    #+#             */
/*   Updated: 2026/10/05 18:03:22 by cristian         ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "agent.h"

/*
** The init line, once: the map as the game stores it (spaces already turned
** into walls), its size and the seed. A map row has no quote or backslash.
*/
static void	print_init(t_data *data)
{
	int	row;

	printf("{\"type\":\"init\",\"map\":[");
	row = 0;
	while (row < data->map_height)
	{
		if (row > 0)
			printf(",");
		printf("\"%s\"", data->map[row]);
		row++;
	}
	printf("],\"width\":%d,\"height\":%d,\"seed\":%u}\n",
		data->map_width, data->map_height, data->seed);
}

/* An I/O error ends the run loudly and with a failure code, never silently. */
void	agent_fail(t_data *data, char *what, char *why)
{
	err_msg(what, why, FAILURE);
	destroy_game(data);
	free_parsing(data);
	exit(FAILURE);
}

/*
** The init line goes out while stdout is still blocking, so a long map is not
** cut. Then stdout turns non-blocking: a slow reader costs observation lines
** (counted as drops) and never stalls the game. A terminal is left alone,
** because the flag would stay on it after the game exits.
*/
void	agent_init_io(t_data *data)
{
	int	flags;

	print_init(data);
	if (fflush(stdout) == EOF || ferror(stdout))
		agent_fail(data, "stdout", strerror(errno));
	if (isatty(STDOUT_FILENO))
		return ;
	flags = fcntl(STDOUT_FILENO, F_GETFL);
	if (flags == -1
		|| fcntl(STDOUT_FILENO, F_SETFL, flags | O_NONBLOCK) == -1)
		agent_fail(data, "stdout", strerror(errno));
}
