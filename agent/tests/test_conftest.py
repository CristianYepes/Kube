import os

from kube_agent.jev_client import KEY_VARIABLE


def test_no_test_can_see_a_real_key():
    # conftest.py removes it from the environment, so an accidental real call cannot be paid for.
    assert KEY_VARIABLE not in os.environ
