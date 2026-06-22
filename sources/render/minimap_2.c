/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   minimap_2.c                                        :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: rodrigo <rodrigo@student.42.fr>            +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/22 19:26:46 by rodrigo           #+#    #+#             */
/*   Updated: 2026/06/22 20:54:21 by rodrigo          ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "cub3d.h"



void    draw_map2(t_data *data)
{
    char **map;
    int y;
    int x;
    int start_y;
    int start_x;
    
    map = data->map;
    start_y = (int)data->player.pos_y - 4;
    start_x = (int)data->player.pos_x - 4;
    y = start_y;
    draw_player(88, 88, 5, data);
    while (y <= start_y +8)
    {
        x = start_x;
        while (x <= start_x +8)
        {
            if (y >= 0 && y < data->map_height && x >= 0 && x < data->map_width)
            {
                if (map[y][x] == '1')
                    draw_square((x - start_x) * 20, (y - start_y) * 20, 20,data);
            }
            x++;
        }
        y++;
    }
}

