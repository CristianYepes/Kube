/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   textures.c                                         :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: rodrigo <rodrigo@student.42.fr>            +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/06/16 12:48:05 by rodrigo           #+#    #+#             */
/*   Updated: 2026/06/17 17:18:58 by rodrigo          ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "cub3d.h"

static void	copy_texture_pixels(int *buffer, t_img tex)
{
	int	x;
	int	y;

	y = 0;
	while (y < TEX_SIZE)
	{
		x = 0;
		while (x < TEX_SIZE)
		{
			buffer[y * TEX_SIZE + x] = *(unsigned int *)(tex.addr
					+ y * tex.size_line + x * (tex.bpp / 8));
			x++;
		}
		y++;
	}
}

int	*xpm_to_int(t_data *data, char *path)
{
	t_img	tex;
	int		*buffer;
	int		w;
	int		h;

	tex.img = mlx_xpm_file_to_image(data->mlx, path, &w, &h);
	if (!tex.img)
		return (NULL);
	tex.addr = mlx_get_data_addr(tex.img,
			&tex.bpp, &tex.size_line, &tex.endian);
	buffer = malloc(sizeof(int) * TEX_SIZE * TEX_SIZE);
	if (!buffer)
	{
		mlx_destroy_image(data->mlx, tex.img);
		return (NULL);
	}
	copy_texture_pixels(buffer, tex);
	mlx_destroy_image(data->mlx, tex.img);
	return (buffer);
}
