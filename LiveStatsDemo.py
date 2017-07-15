from livestats import livestats
from math import sqrt
import random

test = livestats.LiveStats([0.25, 0.5, 0.75])

data = iter(random.random, 1)

for x in xrange(3):
    for y in xrange(1000000):
        test.add(data.next()*100)
    
    print "Average {}, stddev {}, quantiles {}".format(test.mean(), \
            sqrt(test.variance()), test.quantiles())
