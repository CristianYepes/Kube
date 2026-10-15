#!/usr/bin/env bash
# Build and test cub3D inside a Linux container (macOS cannot link X11 MiniLibX).
#
#   dev/dev.sh up      build the image, start the container and its virtual display
#   dev/dev.sh sync    mirror the working tree into the container
#   dev/dev.sh build   sync, then make && make bonus
#   dev/dev.sh check   build, then run tests/check.sh
#   dev/dev.sh down    remove the container
#
# The tree is copied, not bind-mounted: Colima only shares $HOME with its VM, so
# mounts from elsewhere show up empty. minilibx-linux/ is kept between syncs so
# the library is not cloned again every time.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
IMAGE=kube-dev
NAME=kube-dev

need_docker() {
	docker info >/dev/null 2>&1 || {
		echo "dev.sh: Docker is not reachable; start it with: colima start" >&2
		exit 1
	}
}

need_container() {
	[ "$(docker inspect -f '{{.State.Running}}' "$NAME" 2>/dev/null)" = true ] || {
		echo "dev.sh: container '$NAME' is not running; run: dev/dev.sh up" >&2
		exit 1
	}
}

up() {
	docker build -q -t "$IMAGE" "$ROOT/dev" >/dev/null
	docker rm -f "$NAME" >/dev/null 2>&1 || true
	docker run -d --init --name "$NAME" "$IMAGE" sleep infinity >/dev/null
	docker exec -d "$NAME" Xvfb :99 -screen 0 1280x720x24
	echo "dev.sh: container '$NAME' is up (display :99)"
}

sync_tree() {
	need_container
	docker exec "$NAME" find /kube -mindepth 1 -maxdepth 1 \
		! -name minilibx-linux -exec rm -rf {} +
	# Tracked and untracked-but-not-ignored files that exist on disk.
	(cd "$ROOT" && git ls-files -z -c -o --exclude-standard \
		| while IFS= read -r -d '' f; do if [ -e "$f" ]; then printf '%s\0' "$f"; fi; done \
		| COPYFILE_DISABLE=1 tar -c --no-xattrs --no-mac-metadata --null -T - -f -) \
		| docker exec -i "$NAME" tar -x -C /kube
}

build() {
	sync_tree
	docker exec "$NAME" bash -c 'make -s && make -s bonus'
}

check() {
	build
	docker exec -e DISPLAY=:99 "$NAME" bash tests/check.sh
}

down() {
	docker rm -f "$NAME" >/dev/null 2>&1 && echo "dev.sh: container '$NAME' removed" || true
}

need_docker
case "${1:-}" in
	up) up ;;
	sync) sync_tree ;;
	build) build ;;
	check) check ;;
	down) down ;;
	*) sed -n '2,9p' "$0" | sed 's/^# \{0,1\}//'; exit 2 ;;
esac
