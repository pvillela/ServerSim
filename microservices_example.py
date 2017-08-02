"""
Comparison of microservice deployment alternatives.
"""

from __future__ import print_function

import random
import math

import simpy

from serversim import *


#fi = open("simout.txt", "w")
fi = sys.stdout


def microservices_example(weight1, weight2, serverRange1, serverRange2):

    def cug(mid, delta):
        """Computation units geneartor"""
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

    try:

        random.seed(12345)

        nUsers = 700
        simtime = 500
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

        grp = UserGroup(env, nUsers, "UserTypeX", weightedTxns, minThinkTime, maxThinkTime)
        grp.activateUsers()

        print("\n\n***** Start Simulation (", weight1, "/", weight2, "/", serverRange1[0], serverRange1[-1],
              "/", serverRange2[0], serverRange2[-1], ") *****", file=fi)
        print("Simulation: nUsers =", nUsers, "; simTime =", simtime, file=fi)

        env.run(until=simtime)

        print("<< ServerExample >>\n", file=fi)

        indent = " " * 4

        # print parameters
        print("\n" + "simtime =", simtime, file=fi)

        print("\n" + "Servers:", file=fi)
        for svr in servers:
            print(indent*1 + "Server:", svr.name, file=fi)
            print(indent*2 + "maxConcurrency =", svr.maxConcurrency, file=fi)
            print(indent*2 + "numThreads =", svr.numThreads, file=fi)
            print(indent*2 + "speed =", svr.speed, file=fi)
            print(indent*2 + "avgProcessTime =", svr.avgProcessTime, file=fi)
            print(indent*2 + "avgHwQueueTime =", svr.avgHwQueueTime, file=fi)
            print(indent*2 + "avgThreadQueueTime =", svr.avgThreadQueueTime, file=fi)
            print(indent*2 + "avgServiceTime =", svr.avgServiceTime, file=fi)
            print(indent*2 + "avgHwQueueLength =", svr.avgHwQueueLength, file=fi)
            print(indent*2 + "avgThreadQueueLength =", svr.avgThreadQueueLength, file=fi)
            print(indent*2 + "hwQueueLength =", svr.hwQueueLength, file=fi)
            print(indent*2 + "hwInProcessCount =", svr.hwInProcessCount, file=fi)
            print(indent*2 + "threadQueueLength =", svr.threadQueueLength, file=fi)
            print(indent*2 + "threadInUseCount =", svr.threadInUseCount, file=fi)
            print(indent*2 + "utilization =", svr.utilization, file=fi)
            print(indent*2 + "throughput =", svr.throughput, file=fi)

        print(indent*1 + "Group:", grp.name, file=fi)
        print(indent*2 + "numUsers =", grp.numUsers, file=fi)
        print(indent*2 + "minThinkTime =", grp.minThinkTime, file=fi)
        print(indent*2 + "maxThinkTime =", grp.maxThinkTime, file=fi)
        print(indent*2 + "respondedRequestCount =", grp.respondedRequestCount(None), file=fi)
        print(indent*2 + "unrespondedRequestCount =", grp.unrespondedRequestCount(None), file=fi)
        print(indent*2 + "avgResponseTime =", grp.avgResponseTime(None), file=fi)
        print(indent*2 + "stdDevResponseTime =", grp.stdDevResponseTime(None), file=fi)
        print(indent*2 + "throughput =", grp.throughput(None), file=fi)

        for txn in grp._txns:
            print(indent*2 + txn.svcName + ":", file=fi)
            print(indent*3 + "respondedRequestCount =", grp.respondedRequestCount(txn), file=fi)
            print(indent*3 + "unrespondedRequestCount =", grp.unrespondedRequestCount(txn), file=fi)
            print(indent*3 + "avgResponseTime =", grp.avgResponseTime(txn), file=fi)
            print(indent*3 + "stdDevResponseTime =", grp.stdDevResponseTime(txn), file=fi)
            print(indent*3 + "throughput =", grp.throughput(txn), file=fi)

    finally:
        if not fi == sys.stdout:
            fi.close()
        print("\n*** Done ***", file=fi)


if __name__ == "__main__":
    print("\n\n\n@@@@@@@@@ Start comparative simulations @@@@@@@@@@")
    microservices_example(weight1=2, weight2=1, serverRange1=range(0, 10), serverRange2=range(0, 10))
    microservices_example(weight1=2, weight2=1, serverRange1=range(0, 8), serverRange2=range(8, 10))
    microservices_example(weight1=5, weight2=1, serverRange1=range(0, 10), serverRange2=range(0, 10))
    microservices_example(weight1=5, weight2=1, serverRange1=range(0, 8), serverRange2=range(8, 10))
