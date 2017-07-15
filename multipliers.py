"""
See http://python-guide-pt-br.readthedocs.io/en/latest/writing/gotchas/
"""

def bad():

    def create_multipliers():
        return [lambda x : i * x for i in range(5)]

    for multiplier in create_multipliers():
        print multiplier(2)


def good():

    def create_multipliers():
        def _f(i):
            j = i
            return lambda  x: j * x

        return [_f(i) for i in range(5)]

    for multiplier in create_multipliers():
        print multiplier(2)

bad()

print("---")

good()
