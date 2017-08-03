"""
General utilities
"""


def nullary(func, *args, **kwargs):
    """Wrap an effectful function in a nullary function."""
    def ret():
        return func(*args, **kwargs)
    return ret


def curried_nullary(func):
    """Curried verion of nullary."""
    def ret(*args, **kwargs):
        return nullary(func, *args, **kwargs)
    return ret


def index_bisect(lst, x):
    if not lst:
        return None
    elif len(lst) == 1:
        return 0 if lst[0] <= x else None
    else:
        i_mid = len(lst) / 2
        if x >= lst[i_mid]:
            return index_bisect(lst[i_mid:], x) + i_mid
        else:
            return index_bisect(lst[:i_mid], x)


def bisect_search(lst, x):
    """
    Assumes lst is an ordered list and returns a pair.  The first
    component of the pair is the last index i such lst[i] <= x.
    If there is no such index, the first component is None.  The
    second component is lst[i] or None, accordingly.
    """
    idx = index_bisect(lst, x)
    return (idx, lst[idx]) if idx is not None else (None, None)


def step_function(pairs):
    """
    Returns a step function based on the list of (x, y) pairs.
    """
    xs = [p[0] for p in pairs]
    ys = [p[1] for p in pairs]
    def f(x):
        idx = index_bisect(xs, x)
        return ys[idx] if idx is not None else None
    return f
