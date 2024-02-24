from collections.abc import Callable


def find_first_match(condition: Callable[..., bool]) -> int:
    """
    :param condition: Condition that number needs to match.
                      The condition is assumed to be valid for all integers staring
                      from an initial value.
    :return: First integer for which condition is valid.
    """

    # exponential increase for logarithmic search
    upper_bound = 1
    while not condition(upper_bound):
        upper_bound *= 2

    # first match = [lower_bound + 1, upper_bound]
    # narrow down range of first match until one value left
    lower_bound = upper_bound // 2
    while lower_bound + 1 < upper_bound:
        middle = (upper_bound + lower_bound) // 2
        if condition(middle):
            upper_bound = middle
        else:
            lower_bound = middle

    return upper_bound
