/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   agent_main.c                                       :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: cristian <cristian@student.42.fr>          +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/10/05 17:50:03 by cristian          #+#    #+#             */
/*   Updated: 2026/10/05 17:50:03 by cristian         ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "agent.h"

/*
** Replaces sources/main.c in cub3D_agent. It mirrors main() at the base
** (0ac5649), plus a second argument, the seed that fixes where the zombies
** spawn, and agent_init_io() before the loop. ft_atoi does not detect
** overflow, so the seed has at most 9 digits.
*/

static int	is_seed(const char *s)
{
	int	i;

	i = 0;
	while (s[i] >= '0' && s[i] <= '9')
		i++;
	return (i > 0 && i <= 9 && s[i] == '\0');
}

int	main(int argc, char *argv[])
{
	t_data	data;

	data = (t_data){0};
	if (argc != 3)
		return (err_msg(NULL, "Usage: ./cub3D_agent <map.cub> <seed>",
				FAILURE));
	if (!is_seed(argv[2]))
		return (err_msg(argv[2], "seed must be a number, 0 to 999999999",
				FAILURE));
	if (check_file(argv[1]) == FAILURE)
		return (FAILURE);
	if (parsing(argv[1], &data) == FAILURE)
		return (FAILURE);
	if (init_game(&data) != SUCCESS)
	{
		free_parsing(&data);
		return (FAILURE);
	}
	data.seed = (unsigned int)ft_atoi(argv[2]);
	agent_init_io(&data);
	loop(&data);
	return (SUCCESS);
}
