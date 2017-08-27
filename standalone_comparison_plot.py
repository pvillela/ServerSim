import random

from simulate_deployment_scenario import simulate_deployment_scenario
from report_resp_times import *


def simulate():
    random.seed(123456)

    rand_state = random.getstate()
    sc1 = simulate_deployment_scenario(num_users=720, weight1=2, weight2=1,
                                       server_range1=range(0, 10), server_range2=range(0, 10))

    random.setstate(rand_state)
    sc2 = simulate_deployment_scenario(num_users=720, weight1=2, weight2=1,
                                       server_range1=range(0, 8), server_range2=range(8, 10))

    return sc1, sc2


sc1, sc2 = simulate()  # to faciliate tweaking display in ipython

compare_scenarios(sc1, sc2)
