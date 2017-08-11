# We start by importing the required libraries, as well as the __future__
# import for compatibility between Python 2.7 and Python 3.x.

from __future__ import print_function

import random
import simpy
from serversim import *


def deployment_example(numUsers, weight1, weight2, serverRange1, serverRange2):

    def cug(mid, delta):
        """Computation units generator"""
        def f():
            return random.uniform(mid - delta, mid + delta)
        return f

    def ldBal(svcType):
        """Application server load-balancer."""
        if svcType == "svc_1":
            server = random.choice(servers1)
        elif svcType == "svc_2":
            server = random.choice(servers2)
        else:
            assert False, "Invalid service type."
        return server

    # numUsers = 700
    simtime = 200
    hwThreads = 10
    swThreads = 20
    speed = 20
    svc_1_comp_units = 2.0
    svc_2_comp_units = 1.0

    env = simpy.Environment()

    nServers = max(serverRange1[-1]+1, serverRange2[-1]+1)
    servers = [Server(env, hwThreads, swThreads, speed, "AppServer_%s" % i) for i in range(nServers)]
    servers1 = [servers[i] for i in serverRange1]
    servers2 = [servers[i] for i in serverRange2]

    svc_1 = CoreSvcRequester(env, "svc_1", cug(svc_1_comp_units, svc_1_comp_units*.9), ldBal)
    svc_2 = CoreSvcRequester(env, "svc_2", cug(svc_2_comp_units, svc_2_comp_units*.9), ldBal)

    weightedTxns = [(svc_1, weight1),
                    (svc_2, weight2)
                   ]

    minThinkTime = 2.0 # .5 # 4
    maxThinkTime = 10.0 # 1.5 # 20

    grp = UserGroup(env, numUsers, "UserTypeX", weightedTxns, minThinkTime, maxThinkTime)
    grp.activate_users()

    env.run(until=simtime)
    
    return {"num_users":numUsers, "weight1":weight1, "weight2":weight2,
            "serverRange1":serverRange1, "serverRange2":serverRange2, 
            "servers":servers, "grp":grp}