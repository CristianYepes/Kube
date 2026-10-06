"""Shared pytest setup."""

import pytest


@pytest.fixture(autouse=True)
def no_real_key_in_tests(monkeypatch):
    """No test may be able to spend money: the OpenRouter key is removed from the environment.

    A test that needs a key passes one explicitly (`JevClient.from_environment(environ=...)`), and
    every client in a test talks to an httpx2.MockTransport.
    """
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
