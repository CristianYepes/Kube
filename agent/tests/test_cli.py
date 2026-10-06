import pytest

from kube_agent.cli import build_parser, main
from kube_agent.config import DEFAULT_MAP

SUBCOMMANDS = ["run", "eval", "spend", "latency", "order-check"]


def test_help_lists_every_subcommand(capsys):
    with pytest.raises(SystemExit) as exit_info:
        main(["--help"])

    assert exit_info.value.code == 0
    help_text = capsys.readouterr().out
    for name in SUBCOMMANDS:
        assert name in help_text


@pytest.mark.parametrize("name", SUBCOMMANDS)
def test_a_stub_says_so_and_fails(name, capsys):
    # A skeleton must never look like a success: exit code 1, message on stderr.
    assert main([name]) == 1
    assert f"kube-agent {name}: not implemented yet" in capsys.readouterr().err


def test_no_subcommand_is_a_usage_error(capsys):
    with pytest.raises(SystemExit) as exit_info:
        main([])

    assert exit_info.value.code == 2


@pytest.mark.parametrize("name", ["run", "eval"])
def test_run_and_eval_take_the_map_option(name):
    assert build_parser().parse_args([name]).map == DEFAULT_MAP
    assert build_parser().parse_args([name, "--map", "x.cub"]).map == "x.cub"
