/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   free_bonus.c                                       :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: cristian <cristian@student.42.fr>          +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/24 12:00:00 by cristian          #+#    #+#             */
/*   Updated: 2026/06/24 12:00:00 by cristian         ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "cub3d.h"

void	free_sprites(t_data *data)
{
	int	i;

	i = 0;
	while (i < 2)
	{
		if (data->sprite_tex[i])
			free(data->sprite_tex[i]);
		if (data->sprite_tex2[i])
			free(data->sprite_tex2[i]);
		i++;
	}
	if (data->sprites)
		free(data->sprites);
}

void	free_shotgun(t_data *data)
{
	int	i;

	i = 0;
	while (i < GUN_FRAMES)
	{
		if (data->gun_tex[i])
			free(data->gun_tex[i]);
		i++;
	}
}
