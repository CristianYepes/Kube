"""Small statistics for the reports: the order check of T8 now and the final evaluation of T9 later."""

import math

Z95 = 1.96  # the normal quantile of a two-sided 95% interval


def wilson_interval(successes: int, n: int, z: float = Z95) -> tuple[float, float]:
    """The Wilson score interval of a proportion. Unlike the plain one it stays honest for a small n
    and for a rate near 0 or 1: 20 wins out of 20 does not prove a win rate of 100%."""
    if n < 1 or not 0 <= successes <= n:
        raise ValueError(f"successes must be between 0 and n (n at least 1), got {successes} of {n}")
    rate = successes / n
    denominator = 1 + z * z / n
    centre = (rate + z * z / (2 * n)) / denominator
    half_width = z * math.sqrt(rate * (1 - rate) / n + z * z / (4 * n * n)) / denominator
    return max(0.0, centre - half_width), min(1.0, centre + half_width)
