"""
Utilities to support service simulation framework.
"""

from random import random


def probChooser(weightedItems):
    """
    Returns a function that randomly chooses an item from the keys of a dictionary
    with a probability proportional to the values (weights) associated with the keys.  
    The weights do not need to add up to 1.

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
        randomNum = random()
        for i in range(0, len(weightedItems)):
            if cumFreqs[i] > randomNum:  # Random.random() is in [0.0, 1.0)
                return items[i]
    
    return ret
