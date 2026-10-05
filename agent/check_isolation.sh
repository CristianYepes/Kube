#!/usr/bin/env bash
# RETIRED 2026-10-06: the game is no longer handed in at 42, so it is out of the
# checkpoints and the game may change on this branch. It still works, and a change to the
# game makes it fail on purpose. It was last run against ad4244a: ALL PASSED, 71 identical
# objects, on the Mac's container and on the owner's Linux.
#
# Isolation guard for spec 002 (AC1): the agent work must never change the 42 deliverable.
#
#   agent/check_isolation.sh            build in the kube-dev container (the Mac)
#   agent/check_isolation.sh --local    build on this machine (native Linux only)
#
# Three parts, each printing PASS or FAIL. The exit code is 1 if any part failed.
#   paths    nothing outside agent/, sources/jev/, specs/ and CLAUDE.md differs from the
#            base or is new. A new untracked file counts: git diff does not list it.
#   objects  make and make bonus give byte-identical obj/ and obj_bonus/ files for the
#            base and for this tree (sha256 of every .o).
#   norm     norminette sources includes libft finds no error.
#
# "The base" is origin/feature/jev-agent: the game after spec 001, and any fix made
# to the game on that branch since. ISOLATION_BASE=<ref> compares against another
# ref, to check before a new base commit has been pushed.
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BASE=${ISOLATION_BASE:-origin/feature/jev-agent}
NAME=kube-dev
# Everything the agent may add or change. Any other path belongs to the deliverable.
OUTSIDE=(-- . ':(exclude)agent' ':(exclude)sources/jev' ':(exclude)specs' ':(exclude)CLAUDE.md')
FAILED=()

note() { echo "     $*"; }
indent() { sed 's/^/     /'; }
section() {
	local name=$1
	shift
	if "$@"; then echo "PASS $name"; else echo "FAIL $name"; FAILED+=("$name"); fi
}

# ------------------------------------------------------------ arguments and where to build
LOCAL=0
case "${1:-}" in
	"") ;;
	--local) LOCAL=1 ;;
	*) echo "usage: agent/check_isolation.sh [--local]" >&2; exit 2 ;;
esac
[ $# -le 1 ] || { echo "usage: agent/check_isolation.sh [--local]" >&2; exit 2; }

if [ "$LOCAL" = 1 ] && [ "$(uname -s)" != Linux ]; then
	echo "check_isolation.sh: --local needs Linux, and this is $(uname -s): the X11 MiniLibX does not link here" >&2
	exit 2
fi
if [ "$LOCAL" = 0 ] && [ "$(docker inspect -f '{{.State.Running}}' "$NAME" 2>/dev/null)" != true ]; then
	echo "check_isolation.sh: container '$NAME' is not running; start it with: colima start && dev/dev.sh up" >&2
	exit 2
fi

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"; [ "$LOCAL" = 1 ] || docker exec "$NAME" rm -rf /tmp/base 2>/dev/null' EXIT
if [ "$LOCAL" = 1 ]; then
	BASE_DIR=$TMP/base
	WORK_DIR=$TMP/work
else
	BASE_DIR=/tmp/base
	WORK_DIR=/kube
fi

# in_env <script> [args]: run a bash script where the game builds (the container or here).
in_env() {
	local script=$1
	shift
	if [ "$LOCAL" = 1 ]; then bash -c "$script" _ "$@"; else docker exec "$NAME" bash -c "$script" _ "$@"; fi
}

# ------------------------------------------------------------------------ part 1: paths
check_paths() {
	local changed new
	git -C "$ROOT" rev-parse --verify --quiet "$BASE^{commit}" >/dev/null \
		|| { note "the base $BASE does not exist here; run: git fetch origin"; return 1; }
	note "base $BASE is $(git -C "$ROOT" rev-parse --short "$BASE")"
	changed=$(git -C "$ROOT" diff --stat "$BASE" "${OUTSIDE[@]}") \
		|| { note "git diff against $BASE failed"; return 1; }
	new=$(git -C "$ROOT" ls-files --others --exclude-standard "${OUTSIDE[@]}") \
		|| { note "git ls-files for untracked files failed"; return 1; }
	[ -z "$changed" ] || { note "changed outside the allowed paths:"; echo "$changed" | head -10 | indent; }
	[ -z "$new" ] || { note "new files outside the allowed paths:"; echo "$new" | head -10 | indent; }
	[ -z "$changed$new" ]
}

# ---------------------------------------------------------------- the trees to be built
# The working tree is what dev/dev.sh sync copies: tracked files, plus untracked ones that
# are not ignored. In the container that is /kube; here it is a copy in $TMP/work.
prepare_worktree() {
	if [ "$LOCAL" = 0 ]; then
		"$ROOT/dev/dev.sh" sync
		return
	fi
	mkdir -p "$WORK_DIR" || return 1
	(cd "$ROOT" && git ls-files -z -c -o --exclude-standard \
		| while IFS= read -r -d '' f; do if [ -e "$f" ]; then printf '%s\0' "$f"; fi; done \
		| tar -c --null -T - -f -) | tar -x -C "$WORK_DIR" || return 1
	if [ -d "$ROOT/minilibx-linux" ]; then cp -a "$ROOT/minilibx-linux" "$WORK_DIR/"; fi
}

extract_base() {
	if [ "$LOCAL" = 1 ]; then
		mkdir -p "$BASE_DIR" && git -C "$ROOT" archive "$BASE" | tar -x -C "$BASE_DIR"
	else
		docker exec "$NAME" rm -rf "$BASE_DIR" && docker exec "$NAME" mkdir -p "$BASE_DIR" \
			&& git -C "$ROOT" archive "$BASE" | docker exec -i "$NAME" tar -x -C "$BASE_DIR"
	fi
}

# build_dir <dir> <log>: make and make bonus, both from scratch. The log is shown on failure.
build_dir() {
	in_env 'cd "$1" && make -s && make -s bonus' "$1" >"$2" 2>&1
}

# hash_dir <dir>: "<sha256>  <path>" for every object, sorted so two trees compare with diff.
# -r: without objects, xargs would run sha256sum on stdin and wait for it.
hash_dir() {
	in_env 'cd "$1" && find obj obj_bonus -name "*.o" -type f -print0 | sort -z | xargs -0 -r sha256sum' "$1"
}

# --------------------------------------------------------------------- part 2: objects
check_objects() {
	local n_base n_work
	[ "$PREPARED" = 1 ] || { note "the working tree could not be copied, so nothing was built:"; tail -3 "$TMP/prepare.log" | indent; return 1; }
	build_dir "$WORK_DIR" "$TMP/build-work.log" \
		|| { note "make failed in this tree ($WORK_DIR):"; tail -5 "$TMP/build-work.log" | indent; return 1; }
	extract_base || { note "git archive of $BASE into $BASE_DIR failed"; return 1; }
	# Reuse the already built MiniLibX instead of cloning it again.
	in_env 'if [ -d "$1/minilibx-linux" ]; then cp -a "$1/minilibx-linux" "$2/"; fi' "$WORK_DIR" "$BASE_DIR" \
		|| { note "could not copy minilibx-linux next to the base"; return 1; }
	build_dir "$BASE_DIR" "$TMP/build-base.log" \
		|| { note "make failed in the base ($BASE_DIR):"; tail -5 "$TMP/build-base.log" | indent; return 1; }
	hash_dir "$WORK_DIR" >"$TMP/work.sha" || { note "could not hash the objects of this tree"; return 1; }
	hash_dir "$BASE_DIR" >"$TMP/base.sha" || { note "could not hash the objects of the base"; return 1; }
	n_base=$(wc -l <"$TMP/base.sha" | tr -d " ")
	n_work=$(wc -l <"$TMP/work.sha" | tr -d " ")
	[ "$n_base" -gt 0 ] || { note "the base build produced no objects, so this check would pass on nothing"; return 1; }
	note "$n_base objects in the base, $n_work in this tree"
	diff "$TMP/base.sha" "$TMP/work.sha" >"$TMP/sha.diff" \
		|| { note "the objects differ (< base, > this tree):"; head -10 "$TMP/sha.diff" | indent; return 1; }
}

# ----------------------------------------------------------------------- part 3: norm
check_norm() {
	local ok_files
	[ "$PREPARED" = 1 ] || { note "the working tree could not be copied, so norminette did not run"; return 1; }
	in_env 'cd "$1" && norminette sources includes libft' "$WORK_DIR" >"$TMP/norm.log" 2>&1 \
		|| { grep -v ': OK!' "$TMP/norm.log" | head -5 | indent; return 1; }
	ok_files=$(grep -c ': OK!' "$TMP/norm.log")
	[ "$ok_files" -gt 0 ] || { note "norminette exited 0 but checked no file"; return 1; }
	note "$ok_files files OK"
}

echo "check_isolation.sh: building $([ "$LOCAL" = 1 ] && echo "on this machine" || echo "in container $NAME")"
section "paths (only agent/, sources/jev/, specs/ and CLAUDE.md differ from the base)" check_paths
if prepare_worktree >"$TMP/prepare.log" 2>&1; then PREPARED=1; else PREPARED=0; fi
section "objects (make and make bonus match the base byte for byte)" check_objects
section "norminette (sources includes libft)" check_norm

echo
if [ ${#FAILED[@]} -eq 0 ]; then echo "ALL PASSED"; exit 0; fi
echo "FAILED: ${#FAILED[@]} part(s)"
exit 1
