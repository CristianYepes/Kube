"""The pipe to the game: start it, read its init and obs lines, send C and Q lines.

The protocol is in specs/002-jev-agent/plan.md ("Contracts"). This module only moves lines;
what an observation means is up to features.py.
"""

import asyncio
import json
import shlex
from collections import deque
from collections.abc import AsyncIterator
from pathlib import Path

from kube_agent.config import REPO_ROOT

GAME = "./agent/cub3D_agent"
DOCKER_CONTAINER = "kube-dev"
DOCKER_DISPLAY = ":99"
DOCKER_REPO = "/kube"

START_TIMEOUT = 10.0  # seconds to the init line; the game prints it right after loading the map
CLOSE_TIMEOUT = 5.0  # seconds from Q to the game's exit
TERMINATE_TIMEOUT = 2.0  # seconds from SIGTERM to SIGKILL
STDERR_LINES_KEPT = 20
LINE_PREVIEW = 120  # characters of a bad line quoted in an error


class BridgeError(Exception):
    """The game did not behave as the protocol says, or could not be reached."""


def game_command(runner: str, map_path: str, seed: int) -> list[str]:
    """The command that starts the game. `local` must run with the repo root as its cwd."""
    if runner == "docker":
        return [
            "docker", "exec", "-i", "-e", f"DISPLAY={DOCKER_DISPLAY}", "-w", DOCKER_REPO,
            DOCKER_CONTAINER, GAME, map_path, str(seed),
        ]
    if runner == "local":
        return [GAME, map_path, str(seed)]
    raise ValueError(f"unknown runner {runner!r}: expected 'docker' or 'local'")


class GameBridge:
    """One running game. Use it as `async with GameBridge(command) as game:`."""

    def __init__(
        self,
        command: list[str],
        cwd: Path = REPO_ROOT,
        start_timeout: float = START_TIMEOUT,
        close_timeout: float = CLOSE_TIMEOUT,
    ):
        self._command = command
        self._cwd = cwd
        self._start_timeout = start_timeout
        self._close_timeout = close_timeout
        self._process: asyncio.subprocess.Process | None = None
        self._stderr_task: asyncio.Task | None = None
        self._stderr_tail: deque[str] = deque(maxlen=STDERR_LINES_KEPT)
        self.init: dict | None = None

    @property
    def returncode(self) -> int | None:
        return self._process.returncode if self._process else None

    async def __aenter__(self) -> "GameBridge":
        await self.start()
        return self

    async def __aexit__(self, *exception_info) -> None:
        await self.close()

    async def start(self) -> None:
        """Start the game and read its init line, which lands in `self.init`."""
        self._process = await asyncio.create_subprocess_exec(
            *self._command,
            cwd=self._cwd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        self._stderr_task = asyncio.create_task(self._collect_stderr())
        try:
            self.init = await asyncio.wait_for(self._read_init(), self._start_timeout)
        except TimeoutError:
            await self._terminate()
            raise BridgeError(f"no init line within {self._start_timeout} s ({self._where()})") from None
        except BaseException:
            await self._terminate()
            raise

    async def observations(self) -> AsyncIterator[dict]:
        """Yield each obs line as a dict. It ends when the game's output ends."""
        while (message := await self._read_message()) is not None:
            if message.get("type") != "obs":
                raise BridgeError(f"expected an obs line, got type {message.get('type')!r} ({self._where()})")
            yield message

    async def send(self, line: str) -> None:
        """Send one command line (`C ...` or `Q`)."""
        if "\n" in line:
            raise ValueError(f"command {line!r} has a newline: the game reads one command per line")
        stdin = self._process.stdin
        try:
            stdin.write(f"{line}\n".encode())
            await stdin.drain()
        except (BrokenPipeError, ConnectionResetError) as error:
            raise BridgeError(f"could not send {line!r}: the game is gone ({self._where()})") from error

    async def close(self) -> None:
        """Send Q, read what the game still prints, and wait for it to exit with code 0."""
        process = self._process
        if process.returncode is None:
            try:
                await self.send("Q")
            except BridgeError:
                pass  # it exited on its own between the check and the write: its exit code says why
            process.stdin.close()
            try:
                await asyncio.wait_for(self._drain_and_wait(), self._close_timeout)
            except TimeoutError:
                await self._terminate()
                raise BridgeError(
                    f"game did not exit within {self._close_timeout} s after Q; terminated it ({self._where()})"
                ) from None
        await self._stderr_task
        if process.returncode != 0:
            raise BridgeError(f"game exited with code {process.returncode} ({self._where()})")

    async def _read_init(self) -> dict:
        message = await self._read_message()
        if message is None:
            await self._process.wait()
            await self._stderr_task
            raise BridgeError(f"game exited with code {self._process.returncode} before its init line ({self._where()})")
        if message.get("type") != "init":
            raise BridgeError(f"expected an init line, got type {message.get('type')!r} ({self._where()})")
        return message

    async def _read_message(self) -> dict | None:
        """The next line of stdout parsed as a JSON object, or None when the output ended."""
        raw = await self._process.stdout.readline()
        if not raw:
            return None
        text = raw.decode(errors="replace").rstrip("\n")
        try:
            message = json.loads(text)
        except json.JSONDecodeError:
            raise BridgeError(f"line is not JSON: {text[:LINE_PREVIEW]!r} ({self._where()})") from None
        if not isinstance(message, dict):
            raise BridgeError(f"line is not a JSON object: {text[:LINE_PREVIEW]!r} ({self._where()})")
        return message

    async def _drain_and_wait(self) -> None:
        # If nobody reads, a game blocked on a full pipe could never see Q.
        while await self._process.stdout.read(65536):
            pass
        await self._process.wait()

    async def _collect_stderr(self) -> None:
        async for raw in self._process.stderr:
            self._stderr_tail.append(raw.decode(errors="replace").rstrip())

    async def _terminate(self) -> None:
        # Through `docker exec` this ends the docker client, not the game inside the container;
        # the game then ends by itself when it reads end of input.
        process = self._process
        if process.returncode is None:
            process.terminate()
            try:
                await asyncio.wait_for(process.wait(), TERMINATE_TIMEOUT)
            except TimeoutError:
                process.kill()
                await process.wait()
        await self._stderr_task

    def _where(self) -> str:
        stderr = " | ".join(self._stderr_tail) or "nothing"
        return f"command: {shlex.join(self._command)}; stderr: {stderr}"
