/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   init_sprites.c                                     :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: rodrigo <rodrigo@student.42.fr>            +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/22 23:31:09 by rodrigo           #+#    #+#             */
/*   Updated: 2026/06/22 23:35:39 by rodrigo          ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "cub3d.h"

int	init_sprites_data(t_data *data)
{
	data->sprite_tex[0] = xpm_to_int(data, "textures/sprites/sprite_0.xpm");
	data->sprite_tex[1] = xpm_to_int(data, "textures/sprites/sprite_1.xpm");
	data->sprite_tex2[0] = xpm_to_int(data, "textures/sprites/sprite2_0.xpm");
	data->sprite_tex2[1] = xpm_to_int(data, "textures/sprites/sprite2_1.xpm");
	data->boss_tex[0] = xpm_to_int(data, "textures/sprites/boss_0.xpm");
	data->boss_tex[1] = xpm_to_int(data, "textures/sprites/boss_1.xpm");
	data->map_sprite_tex = xpm_to_int(data, "textures/sprites/pizarra.xpm");
	if (!data->sprite_tex[0] || !data->sprite_tex[1])
		return (FAILURE);
	if (!data->sprite_tex2[0] || !data->sprite_tex2[1])
		return (FAILURE);
	if (!data->boss_tex[0] || !data->boss_tex[1])
		return (FAILURE);
	if (!data->map_sprite_tex)
		return (FAILURE);
	data->sprite_count = sprites_counter('2', data);
	if (data->sprite_count == 0)
		return (SUCCESS);
	data->sprites = malloc(sizeof(t_sprite) * data->sprite_count);
	if (!data->sprites)
		return (FAILURE);
	init_sprites('2', data);
	return (SUCCESS);
}
