"""
Utilities for random generation and choice of values.
"""

import random
from typing import Tuple, TypeVar, Callable

from .util import curried_nullary


T = TypeVar('T')


def prob_chooser(*weighted_items):
    # type: (*Tuple[T, float]) -> Callable[[], T]
    """
    Returns a function that randomly chooses an item from a list of
    item-value pairs.

    The choice probability is proportional to the values
    (weights) associated with the items. The weights do not need to
    add up to 1.

    Args:
        *weighted_items: item-weight associations to be picked from.
    
    Returns:
        a function that randomly picks a key in weighted_items with a
            probability proportional to the associated values.
    """
    items = [z[0] for z in weighted_items]
    raw_freqs = [z[1] for z in weighted_items]
    sum_raw_freqs = float(sum(raw_freqs))
    freqs = [x / sum_raw_freqs for x in raw_freqs]
    
    cum_freqs = []
    cum = 0
    for x in freqs:
        cum += x
        cum_freqs.append(cum)
    cum_freqs[len(freqs)-1] = 1.0  # eliminate possible rounding error
    
    def ret():
        random_num = random.random()
        for i in range(0, len(weighted_items)):
            if cum_freqs[i] > random_num:  # Random.random() is in [0.0, 1.0)
                return items[i]
    
    return ret


rand_int = random.randint

gen_int = curried_nullary(rand_int)

rand_float = random.uniform

gen_float = curried_nullary(rand_float)

rand_choice = random.choice

gen_choice = curried_nullary(rand_choice)


def rand_list(g, min_len, max_len):
    size = random.randint(min_len, max_len)
    return [g() for _ in range(size)]


gen_list = curried_nullary(rand_list)
