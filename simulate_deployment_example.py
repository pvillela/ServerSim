from __future__ import print_function

from typing import List, Tuple, Sequence

from collections import namedtuple
import random

import simpy

from serversim import *


def simulate_deployment_example(num_users, weight1, weight2, server_range1,
                                server_range2):
    # type: (int, float, float, Sequence[int], Sequence[int]) -> Result

    Result = namedtuple("Result", ["num_users", "weight1", "weight2", "server_range1",
                         "server_range2", "servers", "grp"])

    def cug(mid, delta):
        """Computation units generator"""
        def f():
            return random.uniform(mid - delta, mid + delta)
        return f

    def ld_bal(svc_name):
        """Application server load-balancer."""
        if svc_name == "svc_1":
            svr = random.choice(servers1)
        elif svc_name == "svc_2":
            svr = random.choice(servers2)
        else:
            assert False, "Invalid service type."
        return svr

    simtime = 200
    hw_threads = 10
    sw_threads = 20
    speed = 20
    svc_1_comp_units = 2.0
    svc_2_comp_units = 1.0
    quantiles = (0.5, 0.95, 0.99)

    env = simpy.Environment()

    n_servers = max(server_range1[-1] + 1, server_range2[-1] + 1)
    servers = [Server(env, hw_threads, sw_threads, speed, "AppServer_%s" % i)
               for i in range(n_servers)]
    servers1 = [servers[i] for i in server_range1]
    servers2 = [servers[i] for i in server_range2]

    svc_1 = CoreSvcRequester(env, "svc_1", cug(svc_1_comp_units,
                                               svc_1_comp_units*.9), ld_bal)
    svc_2 = CoreSvcRequester(env, "svc_2", cug(svc_2_comp_units,
                                               svc_2_comp_units*.9), ld_bal)

    weighted_txns = [(svc_1, weight1),
                     (svc_2, weight2)
                     ]

    min_think_time = 2.0  # .5 # 4
    max_think_time = 10.0  # 1.5 # 20
    svc_req_log = []  # type: List[Tuple[str, SvcRequest]]

    grp = UserGroup(env, num_users, "UserTypeX", weighted_txns, min_think_time,
                    max_think_time, quantiles, svc_req_log)
    grp.activate_users()

    env.run(until=simtime)

    return Result(num_users=num_users, weight1=weight1, weight2=weight2,
            server_range1=server_range1, server_range2=server_range2,
            servers=servers, grp=grp)
