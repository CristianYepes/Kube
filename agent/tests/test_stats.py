import pytest

from kube_agent.stats import wilson_interval


def test_the_libros_result_47_of_50_is_84_to_98_percent():
    # The only published number this function is checked against (tasks.md, T9): 47/50 in `libros`.
    low, high = wilson_interval(47, 50)

    assert (round(low, 2), round(high, 2)) == (0.84, 0.98)


def test_the_interval_contains_the_observed_rate():
    for successes in range(0, 21):
        low, high = wilson_interval(successes, 20)
        assert low <= successes / 20 <= high


def test_all_wins_still_leaves_room_below_and_no_wins_leaves_room_above():
    low, high = wilson_interval(20, 20)
    assert high == pytest.approx(1.0) and low < 0.9  # 20 of 20 does not prove a rate of 100%

    low, high = wilson_interval(0, 20)
    assert low == pytest.approx(0.0) and high > 0.1


def test_the_interval_never_leaves_0_to_1():
    # Floating-point error alone puts the raw formula a hair outside the range: -2.8e-17 for 0 of 5, and
    # 1.0000000000000002 for 5 of 5.
    assert wilson_interval(0, 5)[0] == 0.0
    assert wilson_interval(5, 5)[1] == 1.0


def test_more_data_makes_the_interval_narrower():
    narrow = wilson_interval(500, 1000)
    wide = wilson_interval(5, 10)

    assert narrow[1] - narrow[0] < wide[1] - wide[0]


@pytest.mark.parametrize("successes, n", [(0, 0), (-1, 10), (11, 10)])
def test_impossible_counts_are_refused(successes, n):
    with pytest.raises(ValueError, match="successes"):
        wilson_interval(successes, n)
