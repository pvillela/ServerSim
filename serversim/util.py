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
