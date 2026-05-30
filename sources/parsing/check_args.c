/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   check_args.c                                       :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: cristian <cristian@student.42.fr>          +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/05/30 21:22:16 by cristian          #+#    #+#             */
/*   Updated: 2026/05/30 23:52:52 by cristian         ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "cub3d.h"

static int	is_cub_file(char *arg)
{
	int	len;
	int	result;

	len = ft_strlen(arg);
	if (len < 4)
		return (FAILURE);
	result = ft_strncmp(arg + len - 4, ".cub", 4);
	if (result == 0)
		return (SUCCESS);
	return (FAILURE);
}

static int	is_readable_file(char *arg)
{
	int		fd;
	int		saved_errno;
	char	buf;

	saved_errno = 0;
	buf = 0;
	fd = open(arg, O_RDONLY);
	if (fd == -1)
		return (err_msg(arg, strerror(errno), FAILURE));
	if (read(fd, &buf, 1) == -1 && errno == EISDIR)
	{
		saved_errno = errno;
		close(fd);
		return (err_msg(arg, strerror(saved_errno), FAILURE));
	}
	close(fd);
	return (SUCCESS);
}

int	check_file(char *arg)
{
	if (is_readable_file(arg) == FAILURE)
		return (FAILURE);
	if (is_cub_file(arg) == FAILURE)
		return (err_msg(arg, ERR_FILE_NOT_CUB, FAILURE));
	return (SUCCESS);
}
