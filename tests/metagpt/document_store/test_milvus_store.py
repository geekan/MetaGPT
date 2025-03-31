import random

seed_value = 42
random.seed(seed_value)

vectors = [[random.random() for _ in range(8)] for _ in range(10)]
ids = [f"doc_{i}" for i in range(10)]
metadata = [{"color": "red", "rand_number": i % 10} for i in range(10)]


def assert_almost_equal(actual, expected):
    delta = 1e-10
    if isinstance(expected, list):
        assert len(actual) == len(expected)
        for ac, exp in zip(actual, expected):
            assert abs(ac - exp) <= delta, f"{ac} is not within {delta} of {exp}"
    else:
        assert abs(actual - expected) <= delta, f"{actual} is not within {delta} of {expected}"
