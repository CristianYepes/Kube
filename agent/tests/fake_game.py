"""Stands in for cub3D_agent in the bridge tests: no X server, no game.

usage: fake_game.py FIXTURE ECHO MODE

It prints the recorded FIXTURE line by line, then copies every line it reads on stdin to ECHO
until it reads Q or the input ends, as the real game does. It also writes its working
directory to ECHO.cwd. MODE makes it misbehave:

  normal           as described above
  no-output        prints nothing on stdout, says "boom" on stderr and exits 1
  garbage          prints a line that is not JSON
  not-init         starts with an obs line, the second line of the fixture
  not-object       prints a JSON line that is a list
  bad-type         prints the init line, then a line of an unknown type
  dies-after-init  prints the init line, says "crashed" on stderr and exits 3
  stubborn         prints the fixture, then ignores Q and the end of input and sleeps
  hang             prints nothing and sleeps
  ends-early       prints the init line and 19 observations, then exits with code 0
  paced            as normal, but 2 ms between observations, so game time and the time a request takes
                   move together, as they do in the real game
"""

import os
import sys
import time
from pathlib import Path

fixture_path, echo_path, mode = sys.argv[1:4]
Path(echo_path + ".cwd").write_text(os.getcwd())
fixture_lines = Path(fixture_path).read_text().splitlines()


def say(line):
    print(line, flush=True)


if mode == "hang":
    time.sleep(60)
if mode == "ends-early":
    for line in fixture_lines[:20]:
        say(line)
    sys.exit(0)
if mode == "no-output":
    print("boom", file=sys.stderr, flush=True)
    sys.exit(1)
if mode == "garbage":
    say("this is not json")
elif mode == "not-init":
    say(fixture_lines[1])
elif mode == "not-object":
    say("[1, 2]")
elif mode == "bad-type":
    say(fixture_lines[0])
    say('{"type":"weird"}')
elif mode == "dies-after-init":
    say(fixture_lines[0])
    print("crashed", file=sys.stderr, flush=True)
    sys.exit(3)
else:
    for line in fixture_lines:
        say(line)
        if mode == "paced":
            time.sleep(0.002)

if mode == "stubborn":
    time.sleep(60)

with open(echo_path, "w") as echo:
    for line in sys.stdin:
        echo.write(line)
        echo.flush()
        if line.strip() == "Q":
            break
