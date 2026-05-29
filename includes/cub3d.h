/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   cub3d.h                                            :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: cristian <cristian@student.42.fr>          +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/05/24 22:48:50 by cristian          #+#    #+#             */
/*   Updated: 2026/05/29 18:07:09 by cristian         ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#ifndef CUB3D_H
# define CUB3D_H
# include <fcntl.h>
# include <math.h>
# include <stdio.h>
# include <stdlib.h>
# include <string.h>
# include <unistd.h>
# include <errno.h>
# include "libft.h"
# include "mlx.h"

/*Window*/
# define WIN_W 1280
# define WIN_H 720

/*Return codes*/
# define SUCCESS 0
# define FAILURE 1
# define ERR 2
# define BREAK 3
# define CONTINUE 4

/*Error strings*/
# define ERR_USAGE "Usage: ./cub3D <map.cub>"

int	err_msg(char *detail, char *str, int code);
#endif
