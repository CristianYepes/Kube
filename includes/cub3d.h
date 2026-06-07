/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   cub3d.h                                            :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: cristian <cristian@student.42.fr>          +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/05/24 22:48:50 by cristian          #+#    #+#             */
/*   Updated: 2026/06/07 20:36:03 by cristian         ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#ifndef CUB3D_H
# define CUB3D_H
# include "libft.h"
# include "mlx.h"
# include <errno.h>
# include <fcntl.h>
# include <math.h>
# include <stdio.h>
# include <stdlib.h>
# include <string.h>
# include <unistd.h>

/*Window*/
# define WIN_W 1280
# define WIN_H 720

/*Return codes*/
# define SUCCESS 0
# define FAILURE 1
# define ERR 2
# define BREAK 3
# define CONTINUE 4

/*Line Types*/
# define TYPE_EMPTY 0
# define TYPE_TEXTURE 1
# define TYPE_COLOR 2
# define TYPE_MAP 3

/*Texture Index*/
# define NORTH 0
# define SOUTH 1
# define WEST 2
# define EAST 3

/*Error strings*/
# define ERR_USAGE "Usage: ./cub3D <map.cub>"
# define ERR_FILE_NOT_CUB "Not a .cub file"
# define ERR_EMPTY_FILE "Empty file"
# define ERR_DUPLICATE_TEXTURE "Duplicate Texture"
# define ERR_EMPTY_PATH "Empty path"

typedef struct s_data
{
	char	**file_lines;
	int		file_nb_lines;
	char	*tex_paths[4];
	int		floor_color;
	int		ceiling_color;
	int		id_flags;
}			t_data;
/*ERROR*/
int			err_msg(char *detail, char *str, int code);
/*PARSING*/
int			check_file(char *arg);
int			parse_memory(char *path, t_data *data);
int			get_file_data(t_data *data);
#endif
