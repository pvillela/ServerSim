"""
Utilities for random generation and choice of values.
"""

import random

from .util import curried_nullary


def probChooser(*weightedItems):
    """
    Returns a function that randomly chooses an item from a list of
    item-value pairs,  with a probability proportional to the values
    (weights) associated with the items. The weights do not need to
    add up to 1.

    Args:
        weightedItems (list[(any, number)]): item-weight associations to be picked from.
    
    Returns:
        () -> any: a function which randomly picks a key in weightedItems with a 
            probability proportional to the associated values.
    """
    items = [z[0] for z in weightedItems]
    rawFreqs = [z[1] for z in weightedItems]
    sumRawFreqs = float(sum(rawFreqs))
    freqs = [x / sumRawFreqs for x in rawFreqs]
    
    cumFreqs = []
    cum = 0
    for x in freqs:
        cum += x
        cumFreqs.append(cum)
    cumFreqs[len(freqs)-1] = 1.0  # eliminate possible rounding error
    
    def ret():
        randomNum = random.random()
        for i in range(0, len(weightedItems)):
            if cumFreqs[i] > randomNum:  # Random.random() is in [0.0, 1.0)
                return items[i]
    
    return ret


rand_int = random.randint

gen_int = curried_nullary(rand_int)

rand_float = random.uniform

gen_float = curried_nullary(rand_float)

rand_choice = random.choice

gen_choice = curried_nullary(rand_choice)

def rand_list(g, minLen, maxLen):
    size = random.randint(minLen, maxLen)
    return [g() for _i in range(size)]

gen_list = curried_nullary(rand_list)
