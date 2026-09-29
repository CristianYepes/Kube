#!/usr/bin/env bash
# Acceptance checks of specs/001-game-ready, one section per criterion.
# Runs on Linux from the repo root's parent layout (dev/dev.sh check does it in
# the container). Needs an X display (e.g. Xvfb :99), xdotool, valgrind and
# norminette. Prints PASS/FAIL per section; exits 1 if any section failed.
set -uo pipefail
cd "$(dirname "$0")/.."
: "${DISPLAY:?check.sh needs an X display, e.g. Xvfb :99 and DISPLAY=:99}"
shopt -s nullglob

TMP=$(mktemp -d)
trap 'pkill -f "$TMP" 2>/dev/null; rm -rf "$TMP"' EXIT
BASELINE=tests/baseline-main-34f4aff.txt
FAILED=()

note() { echo "     $*"; }
section() {
	local name=$1
	shift
	if "$@"; then echo "PASS $name"; else echo "FAIL $name"; FAILED+=("$name"); fi
}
# Within a relative tolerance: within <value> <expected> <fraction>.
within() { awk -v v="$1" -v e="$2" -v f="$3" 'BEGIN { d = v - e; if (d < 0) d = -d; exit !(d <= f * (e < 0 ? -e : e)) }'; }

# ---------------------------------------------------------------- build (AC6)
check_build() {
	local ok=0 before after out pinned
	make -s >/dev/null 2>&1 && make -s bonus >/dev/null 2>&1 || { note "make or make bonus failed"; return 1; }
	before=$(stat -c '%Y %n' cub3D cub3D_bonus libft/libft.a minilibx-linux/libmlx.a)
	sleep 1
	# Whether MiniLibX re-runs depends on its directory's mtime, which any new
	# entry in it bumps; sampling missed it once. Bump it on purpose, so the
	# check does not depend on timing: a correct Makefile ignores the directory.
	touch minilibx-linux
	out=$({ make; make bonus; } 2>&1)
	after=$(stat -c '%Y %n' cub3D cub3D_bonus libft/libft.a minilibx-linux/libmlx.a)
	[ "$before" = "$after" ] || { note "a second make rebuilt something"; ok=1; }
	grep -qi configure <<<"$out" && { note "a second make re-ran MiniLibX's configure"; ok=1; }
	pinned=$(sed -n 's/^MLX_COMMIT[[:space:]]*=[[:space:]]*//p' Makefile)
	if [ -z "$pinned" ]; then
		note "the Makefile pins no MLX_COMMIT"; ok=1
	elif [ "$(git -C minilibx-linux rev-parse --short=7 HEAD)" != "${pinned:0:7}" ]; then
		note "minilibx-linux is not at the pinned commit $pinned"; ok=1
	fi
	touch libft/ft_strlen.c
	grep -q "Linking cub3D" <<<"$(make 2>&1)" || { note "a changed libft did not relink cub3D"; ok=1; }
	make -s bonus >/dev/null 2>&1
	{ make -s fclean && make -s bonus && make -s; } >/dev/null 2>&1 || { note "fclean then rebuild failed"; ok=1; }
	return $ok
}

# ----------------------------------------------------------- norminette (AC7)
check_norm() {
	norminette sources includes libft >"$TMP/norm" 2>&1 || { grep -v ': OK!' "$TMP/norm" | head -5; return 1; }
}

# ------------------------------------------------------------ maps (AC3, AC7)
# Prints "<rc>\t<line 1>\t<line 2>". rc 124 means still running after 3 s: accepted.
map_result() {
	local out rc
	out=$(timeout 3 "./$1" "$2" 2>&1)
	rc=$?
	printf '%s\t%s\t%s\n' "$rc" "$(sed -n 1p <<<"$out")" "$(sed -n 2p <<<"$out")"
}
check_maps() {
	local ok=0 m b r
	for m in maps/good/*.cub; do
		for b in cub3D cub3D_bonus; do
			r=$(map_result "$b" "$m")
			[ "${r%%$'\t'*}" = 124 ] || { note "$b should accept $m: $r"; ok=1; }
		done
	done
	for m in maps/bonus/*.cub; do
		r=$(map_result cub3D_bonus "$m")
		[ "${r%%$'\t'*}" = 124 ] || { note "cub3D_bonus should accept $m: $r"; ok=1; }
		r=$(map_result cub3D "$m")
		[ "$r" = $'1\tError\tInvalid character in map' ] || { note "cub3D should reject $m as an invalid character: $r"; ok=1; }
	done
	for m in maps/bad/*.cub; do
		for b in cub3D cub3D_bonus; do
			r=$(map_result "$b" "$m")
			[[ "$r" == $'1\tError\t'* ]] || { note "$b should reject $m: $r"; ok=1; }
		done
	done
	[ -d maps/bonus ] || { note "maps/bonus/ does not exist"; ok=1; }
	return $ok
}
check_messages() {
	local ok=0 map msg r
	[ -f "$BASELINE" ] || { note "missing $BASELINE"; return 1; }
	while IFS=$'\t' read -r kind map msg; do
		[ "$kind" = msg ] && [ -f "maps/bad/$map" ] || continue
		r=$(map_result cub3D "maps/bad/$map")
		[ "${r##*$'\t'}" = "$msg" ] || { note "$map: '${r##*$'\t'}', baseline '$msg'"; ok=1; }
	done <"$BASELINE"
	return $ok
}

# ------------------------------------------------------------- valgrind (AC2)
# vg <binary> <map> <wait>: wait > 0 means the game opens, runs, and exits by ESC.
vg() {
	local log="$TMP/vg-$1-$(basename "$2").log" pid
	valgrind --leak-check=full --show-leak-kinds=all "./$1" "$2" >"$log" 2>&1 &
	pid=$!
	if [ "$3" -gt 0 ]; then
		xdotool search --sync --name '^cub3D$' >/dev/null 2>&1
		sleep "$3"
		xdotool search --name '^cub3D$' windowfocus --sync key Escape >/dev/null 2>&1
	fi
	wait "$pid"
	if grep -q "in use at exit: 0 bytes in 0 blocks" "$log" && grep -q "ERROR SUMMARY: 0 errors" "$log"; then
		return 0
	fi
	note "$1 $2: $(grep -E 'in use at exit|ERROR SUMMARY' "$log" | sed 's/==[0-9]*== *//' | tr '\n' ' ')"
	return 1
}
check_valgrind() {
	local ok=0
	vg cub3D maps/good/valid_ids.cub 3 || ok=1
	vg cub3D_bonus maps/good/valid_ids.cub 3 || ok=1
	vg cub3D maps/bad/wall_hole.cub 0 || ok=1        # error before the display opens
	vg cub3D maps/bad/tex_wrong_size.cub 0 || ok=1   # error after the display opens
	return $ok
}

# ------------------------------------------------- movement and fps (AC1, AC7)
# A copy of the tree whose game_loop prints the player's pose every frame:
# "P <epoch seconds> <x> <y> <dir_x> <dir_y>". Built in $TMP, never in the tree.
build_probe() {
	[ -x "$TMP/probe/cub3D_bonus" ] && return 0
	cp -a . "$TMP/probe"
	sed -i 's|mlx_put_image_to_window(data->mlx, data->win, data->img.img, 0, 0);|{ struct timeval pv; gettimeofday(\&pv, NULL); fprintf(stderr, "P %ld.%06ld %.6f %.6f %.6f %.6f\\n", (long)pv.tv_sec, (long)pv.tv_usec, data->player.pos_x, data->player.pos_y, data->player.dir_x, data->player.dir_y); } &|' \
		"$TMP/probe/sources/render/game_loop.c"
	make -s -C "$TMP/probe" >/dev/null 2>&1 && make -s -C "$TMP/probe" bonus >/dev/null 2>&1
}
now() { date +%s.%N; }
# pose <log> <time>: the last pose printed at or before <time>.
pose() { awk -v t="$2" '$1 == "P" && $2 <= t { l = $0 } END { print l }' "$1"; }
dist() { awk -v a="$1" -v b="$2" 'BEGIN { split(a, p); split(b, q); print sqrt((q[3]-p[3])^2 + (q[4]-p[4])^2) }'; }
turn() { awk -v a="$1" -v b="$2" 'BEGIN { split(a, p); split(b, q); d = atan2(q[6], q[5]) - atan2(p[6], p[5]); pi = atan2(0, -1); while (d > pi) d -= 2*pi; while (d < -pi) d += 2*pi; print (d < 0 ? -d : d) }'; }
fps() { awk -v a="$2" -v b="$3" '$1 == "P" && $2 >= a && $2 <= b { n++ } END { printf "%.0f", n / (b - a) }' "$1"; }

# probe_run <binary> <map> key <key> <seconds> | mouse | idle <seconds>
# Runs one probe in the probe copy (same layout, so relative map paths work)
# and prints the measure: cells moved, radians turned, or frames per second.
probe_run() {
	local log="$TMP/probe-$RANDOM.log" pid w t0 t1 r
	(cd "$TMP/probe" && exec "./$1" "$2" 2>"$log") &
	pid=$!
	w=$(xdotool search --sync --name '^cub3D$' | head -1)
	xdotool windowfocus --sync "$w"
	sleep 1
	case $3 in
		key) t0=$(now); xdotool keydown "$4"; sleep "$5"; xdotool keyup "$4"; sleep 0.3; t1=$(now)
			[ "$4" = w ] && r=$(dist "$(pose "$log" "$t0")" "$(pose "$log" "$t1")") \
				|| r=$(turn "$(pose "$log" "$t0")" "$(pose "$log" "$t1")") ;;
		mouse) xdotool mousemove --window "$w" 640 360; sleep 0.5; t0=$(now)
			xdotool mousemove --window "$w" 740 360; sleep 0.5; t1=$(now)
			r=$(turn "$(pose "$log" "$t0")" "$(pose "$log" "$t1")") ;;
		idle) t0=$(now); sleep "$4"; t1=$(now); r=$(fps "$log" "$t0" "$t1") ;;
	esac
	kill "$pid" 2>/dev/null; wait "$pid" 2>/dev/null
	echo "$r"
}
probe_maps() {
	# A short corridor (fast to render) and the long test_map (slow), both
	# facing east along free cells.
	printf 'NO ./files/wall_bunker_ns.xpm\nSO ./files/wall_bunker_ns.xpm\nWE ./files/wall_bunker_ew.xpm\nEA ./files/wall_bunker_ew.xpm\nF 120,120,115\nC 40,40,45\n\n1111111111111111\n1E00000000000001\n1111111111111111\n' >"$TMP/corridor.cub"
	sed 's/0N0/0E0/' maps/good/test_map.cub >"$TMP/long.cub"
}
check_movement() {
	local ok=0 b m d small long r
	build_probe || { note "probe build failed"; return 1; }
	probe_maps
	for b in cub3D cub3D_bonus; do
		# 2 s of W at 1.2 cells/s is 2.4 cells.
		small=$(probe_run "$b" "$TMP/corridor.cub" key w 2)
		long=$(probe_run "$b" "$TMP/long.cub" key w 2)
		note "$b W 2 s: corridor $small cells, test_map $long cells (expected 2.4)"
		within "$small" 2.4 0.10 && within "$long" 2.4 0.10 || ok=1
		# 1 s of Left at 1.8 rad/s is 1.8 rad (kept under pi: turn() is modulo 2 pi).
		r=$(probe_run "$b" "$TMP/corridor.cub" key Left 1)
		note "$b Left 1 s: $r rad (expected 1.8)"
		within "$r" 1.8 0.10 || ok=1
	done
	r=$(probe_run cub3D_bonus "$TMP/corridor.cub" mouse)
	note "cub3D_bonus mouse 100 px: $r rad (expected 0.03)"
	within "$r" 0.03 0.10 || ok=1
	return $ok
}
check_fps() {
	local m base r
	build_probe || { note "probe build failed"; return 1; }
	m=$(ls maps/*/subject_map.cub | head -1)
	base=$(awk -F'\t' '$1 == "fps" && $2 == "subject_map_bonus" { print $3 }' "$BASELINE")
	r=$(probe_run cub3D_bonus "$m" idle 5)
	note "cub3D_bonus $m idle: $r fps (baseline ${base:-none})"
	[ -n "$base" ] && within "$r" "$base" 0.15
}

# ---------------------------------------------------- dead code, assets (AC5)
check_dead_code() {
	local ok=0 s n f
	for s in BREAK CONTINUE DEATH_TIME E_DEAD render_weapon anim_timer frame_idx; do
		n=$(grep -rw "$s" sources includes | wc -l)
		[ "$n" = 0 ] || { note "$s is still referenced ($n)"; ok=1; }
	done
	for f in $(find . -name '*.xpm' -not -path './minilibx-linux/*' -not -path './obj*'); do
		grep -rqF "$(basename "$f")" maps sources includes || { note "orphan asset: $f"; ok=1; }
	done
	return $ok
}

# --------------------------------------------------------------- README (AC4)
check_readme() {
	local ok=0 p c
	for p in $(grep -oE 'maps/[A-Za-z0-9_./-]+\.cub' README.md | sort -u); do
		[ -f "$p" ] || { note "README runs $p, which does not exist"; ok=1; }
	done
	for c in 'W/A/S/D' 'Left/Right arrows' 'ESC' '| E |' '| M |' '| R |' 'Up arrow' 'Mouse' 'click'; do
		grep -qF -- "$c" README.md || { note "controls table lacks '$c'"; ok=1; }
	done
	return $ok
}

# ---------------------------------------------------------------- smoke (AC7)
check_smoke() {
	local m pid i
	m=$(ls maps/*/subject_map.cub | head -1)
	./cub3D_bonus "$m" >/dev/null 2>&1 &
	pid=$!
	xdotool search --sync --name '^cub3D$' windowfocus --sync >/dev/null 2>&1
	for i in $(seq 1 20); do
		xdotool keydown w Left Up; sleep 0.5; xdotool keyup w Left Up; sleep 2.5
	done
	kill -0 "$pid" 2>/dev/null || { note "cub3D_bonus died during 60 s of play"; return 1; }
	kill "$pid"; wait "$pid" 2>/dev/null
	return 0
}

section "build and no relink (AC6)" check_build
section "norminette (AC7)" check_norm
section "map matrix (AC3)" check_maps
section "error messages vs baseline (AC7)" check_messages
section "valgrind without suppressions (AC2)" check_valgrind
section "movement by time (AC1)" check_movement
section "fps vs baseline (AC7)" check_fps
section "dead code and orphan assets (AC5)" check_dead_code
section "README (AC4)" check_readme
section "60 s bonus smoke run (AC7)" check_smoke

echo
if [ ${#FAILED[@]} -eq 0 ]; then echo "ALL PASSED"; exit 0; fi
echo "FAILED: ${#FAILED[@]} section(s)"
exit 1
