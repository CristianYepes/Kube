"""Spec 003, V3 (AC10): what the view's server serves, to whom, and what it never does."""

import http.client
import json
import socket
import threading
import time
from pathlib import Path

import pytest

from kube_agent import view
from kube_agent.config import RUNS_DIR

FOLDER = sorted((RUNS_DIR / "eval-20261010T122708Z-darwin").glob("*-jev-*"))[0]
FONTS = ("IBMPlexSans-Regular.woff2", "IBMPlexSans-SemiBold.woff2", "IBMPlexMono-Regular.woff2", "IBMPlexMono-SemiBold.woff2")


@pytest.fixture
def served():
    log = view.EventLog()
    server = view.make_server(log, 0)
    thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.02}, daemon=True)
    thread.start()
    yield log, server
    server.shutdown()
    server.server_close()
    thread.join(2)


def get(server, path, method="GET", host=None):
    port = server.server_address[1]
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    headers = {"Host": host if host is not None else f"127.0.0.1:{port}"}
    connection.request(method, path, headers=headers)
    response = connection.getresponse()
    body = response.read()
    headers = dict(response.getheaders())
    connection.close()
    return response.status, headers, body


# --- what it serves --------------------------------------------------------------------------------------------------------


def test_the_page_is_served_at_the_root(served):
    status, headers, body = get(served[1], "/")

    assert status == 200 and headers["Content-Type"] == "text/html; charset=utf-8"
    assert body == (view.PAGE_DIR / "index.html").read_bytes()


@pytest.mark.parametrize("name", FONTS)
def test_each_bundled_font_is_served(served, name):
    status, headers, body = get(served[1], f"/fonts/{name}")

    assert status == 200 and headers["Content-Type"] == "font/woff2"
    assert body == (view.PAGE_DIR / "fonts" / name).read_bytes()


def test_the_conclusion_is_served_as_json(served):
    status, headers, body = get(served[1], "/conclusion")
    card = json.loads(body)

    assert status == 200 and headers["Content-Type"] == "application/json"
    assert set(card) >= {"headline", "lines", "source"} and card["lines"]


def test_events_come_after_the_number_asked_for(served):
    log, server = served
    for t in range(3):
        log.append({"kind": "row", "t": float(t), "tactic": "ENGAGE"})

    assert [event["n"] for event in json.loads(get(server, "/events?after=-1")[2])] == [0, 1, 2]
    assert [event["n"] for event in json.loads(get(server, "/events?after=0")[2])] == [1, 2]
    assert json.loads(get(server, "/events?after=2")[2]) == []
    assert [event["n"] for event in json.loads(get(server, "/events")[2])] == [0, 1, 2]


@pytest.mark.parametrize("query", ["after=abc", "after=", "after=1.5", "after=1&after=2x"])
def test_a_bad_after_is_a_400_and_not_a_crash(served, query):
    assert get(served[1], f"/events?{query}")[0] == 400
    assert get(served[1], "/events?after=-1")[0] == 200  # the server is still there


# --- what it refuses --------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("path", [
    "/fonts/../view.py", "/fonts/%2e%2e/view.py", "/fonts/..%2fview.py", "/fonts/", "/fonts", "/fonts/OFL.txt",
    "/fonts/IBMPlexSans-Regular.woff2.bak", "/fonts/IBMPlexSans-Regular.woff2/", "/fonts//IBMPlexSans-Regular.woff2",
    "/view.py", "/index.html", "/nope", "/..", "//etc/passwd", "/%2e%2e/%2e%2e/etc/passwd", "/events/", "/conclusion/x",
    "/\\x00", "/fonts/IBMPlexSans-Regular.woff2%00.png",
])
def test_anything_that_is_not_one_of_its_own_files_is_a_404(served, path):
    assert get(served[1], path)[0] == 404


@pytest.mark.parametrize("method", ["POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
def test_only_get_is_allowed(served, method):
    status, headers, _ = get(served[1], "/events", method=method)
    assert status == 405 and headers["Allow"] == "GET"


def test_a_request_for_another_host_name_is_refused(served):
    """DNS rebinding: a page on another site whose name points to 127.0.0.1 must not read the run."""
    server = served[1]
    port = server.server_address[1]
    assert get(server, "/events", host="evil.example")[0] == 404
    assert get(server, "/events", host=f"evil.example:{port}")[0] == 404
    assert get(server, "/events", host=f"127.0.0.1:{port + 1}")[0] == 404
    assert get(server, "/events", host=f"localhost:{port}")[0] == 200
    assert get(server, "/events", host=f"127.0.0.1:{port}")[0] == 200


def test_a_request_with_no_host_is_refused(served):
    port = served[1].server_address[1]
    with socket.create_connection(("127.0.0.1", port), timeout=5) as connection:
        connection.sendall(b"GET /events HTTP/1.0\r\n\r\n")
        reply = connection.recv(4096)
    assert reply.startswith(b"HTTP/1.0 404") or reply.startswith(b"HTTP/1.1 404")


def test_every_answer_carries_the_security_headers(served):
    for path in ("/", "/events", "/conclusion", f"/fonts/{FONTS[0]}", "/nope"):
        _, headers, _ = get(served[1], path)
        assert headers["X-Content-Type-Options"] == "nosniff", path
        assert headers["Referrer-Policy"] == "no-referrer", path
        assert headers["Content-Security-Policy"] == view.CONTENT_SECURITY_POLICY, path
        assert headers["Cache-Control"] == "no-store", path
    policy = view.CONTENT_SECURITY_POLICY
    assert "default-src 'none'" in policy and "connect-src 'self'" in policy and "frame-ancestors 'none'" in policy
    assert "http" not in policy  # no other origin is allowed anything


def test_the_server_does_not_say_which_python_it_runs_on(served):
    assert get(served[1], "/")[1]["Server"] == "kube-view"


# --- where it listens ---------------------------------------------------------------------------------------------------------


def test_it_listens_on_the_loopback_address_only(served):
    assert served[1].server_address[0] == "127.0.0.1"


def test_a_port_that_is_taken_is_an_error_that_names_the_port(served):
    taken = served[1].server_address[1]
    with pytest.raises(OSError) as error:
        view.make_server(view.EventLog(), taken)
    assert str(taken) in str(error.value)


# --- what it never does -------------------------------------------------------------------------------------------------------


def test_the_module_has_no_outgoing_network_and_does_not_read_the_environment():
    source = Path(view.__file__).read_text()
    for forbidden in ("urllib.request", "http.client", "create_connection", "import requests", "import httpx", "typesafe_sdk",
                      "os.environ", "getenv", "OPENROUTER", "libros", "dotenv"):
        assert forbidden not in source, forbidden
    assert ".env" not in source.replace("environment", "")  # the key file's name


# --- running it ------------------------------------------------------------------------------------------------------------------


def test_serve_replays_a_folder_over_http_and_stops_when_asked():
    holder, said = {}, []
    thread = threading.Thread(target=lambda: holder.update(code=view.serve(0, FOLDER, 1.0, on_ready=lambda s: holder.update(server=s),
                                                                          say=said.append)), daemon=True)
    thread.start()
    for _ in range(100):
        if "server" in holder:
            break
        time.sleep(0.02)
    time.sleep(1.4)  # the replay releases the first second of game time, at its real speed
    events = json.loads(get(holder["server"], "/events?after=-1")[2])
    holder["server"].shutdown()
    thread.join(3)

    assert holder["code"] == 0 and not thread.is_alive()
    assert "127.0.0.1" in said[0] and "full screen (F11)" in said[0] and "100% zoom" in said[0]  # what the owner must do before recording
    assert events[0]["kind"] == "run" and events[0]["mode"] == "replay"
    assert max(event.get("answered_at") or event.get("t") or 0.0 for event in events) <= 1.0
    assert not any(event["kind"] == "end" for event in events)


def test_a_worker_that_fails_stops_the_server_and_says_so(tmp_path, monkeypatch):
    def broken(*args, **kwargs):
        raise RuntimeError("the folder vanished")

    monkeypatch.setattr(view, "follow", broken)
    said, holder = [], {}
    thread = threading.Thread(target=lambda: holder.update(
        code=view.serve(0, None, None, runs_dir=tmp_path, say=said.append, on_ready=lambda server: holder.update(server=server))),
        daemon=True)
    thread.start()
    thread.join(3)
    stuck = thread.is_alive()
    if stuck:  # do not leave the server running if the check failed
        holder["server"].shutdown()
        thread.join(3)

    assert not stuck, "the server went on serving after its worker failed"
    assert holder["code"] == 1
    assert any("RuntimeError" in line and "the folder vanished" in line for line in said)


def test_a_folder_that_is_not_a_run_is_refused_before_anything_is_started(tmp_path):
    with pytest.raises(ValueError, match="not the name of a run folder"):
        view.serve(0, tmp_path, None, say=lambda message: None)
