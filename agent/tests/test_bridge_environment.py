"""What environment the game, or the docker client that starts it, is given (AC: the key goes no further).

A child process inherits the whole environment unless it is told otherwise, and this process holds
the OpenRouter key while it plays. These tests are about names only: no real key is used anywhere.
"""

import pytest

from kube_agent.bridge import child_environment
from kube_agent.jev_client import KEY_VARIABLE

CREDENTIAL_NAMES = [
    KEY_VARIABLE,
    "TYPESAFE_API_KEY",
    "GITHUB_TOKEN",
    "AWS_SECRET_ACCESS_KEY",
    "GITHUB_CLIENT_SECRET",  # SECRET and nothing else: AWS_SECRET_ACCESS_KEY is also caught by KEY
    "DB_PASSWORD",
    "MYSQL_PASSWD",
    "GOOGLE_APPLICATION_CREDENTIALS",
    "openrouter_api_key",  # the case of a name is not a way round the rule
    "SOME_API_KEY_OLD",  # nor is the word being in the middle
]
ORDINARY_NAMES = ["PATH", "HOME", "DISPLAY", "XAUTHORITY", "DOCKER_HOST", "LANG"]
# XAUTHORITY is on that list on purpose: the game needs it to open a window on a real display, so
# the rule must not catch every name with "AUTH" in it.


def test_the_name_of_the_jev_key_is_dropped_whatever_the_pattern_says():
    environment = child_environment({KEY_VARIABLE: "not-a-real-key", "PATH": "/usr/bin"})

    assert KEY_VARIABLE not in environment
    assert environment == {"PATH": "/usr/bin"}


@pytest.mark.parametrize("name", CREDENTIAL_NAMES)
def test_a_name_that_looks_like_a_credential_is_dropped(name):
    assert name not in child_environment({name: "x", "PATH": "/usr/bin"})


@pytest.mark.parametrize("name", ORDINARY_NAMES)
def test_an_ordinary_name_is_kept_with_its_value(name):
    assert child_environment({name: "the value"}) == {name: "the value"}


def test_the_environment_it_is_given_is_not_changed():
    given = {KEY_VARIABLE: "not-a-real-key", "PATH": "/usr/bin"}

    child_environment(given)

    assert given == {KEY_VARIABLE: "not-a-real-key", "PATH": "/usr/bin"}


def test_without_an_argument_it_cleans_this_process_environment(monkeypatch):
    monkeypatch.setenv("TEST_ONLY_API_KEY", "not-a-real-key")
    monkeypatch.setenv("TEST_ONLY_VISIBLE", "kept")

    environment = child_environment()

    assert "TEST_ONLY_API_KEY" not in environment
    assert environment["TEST_ONLY_VISIBLE"] == "kept"
