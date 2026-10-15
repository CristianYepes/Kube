# Linux build and test environment for cub3D.
# The project targets Linux (X11 MiniLibX), so on macOS it is built and tested
# here instead. Xvfb gives the game a display without a screen; xdotool, xwd and
# ImageMagick drive it and capture it; valgrind and norminette check it.
FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential git ca-certificates \
      libx11-dev libxext-dev libbsd-dev zlib1g-dev \
      xvfb x11-apps imagemagick xdotool valgrind \
      python3-pip \
    && rm -rf /var/lib/apt/lists/* \
    && pip3 install --no-cache-dir norminette==3.3.60
WORKDIR /kube
