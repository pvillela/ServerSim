"""
Simple example.
"""

from __future__ import print_function

import random
import math

import simpy

from serversim import *


def simple_serversim_example():

    logging.basicConfig(level=logging.INFO,
                        format='%(levelname)-4s %(message)s')

    #fi = open("simout.txt", "w")
    fi = sys.stdout


    def cug(mid, delta):
        """Computation units geneartor"""
        def f():
            return random.uniform(mid - delta, mid + delta)
        return f


    def appLdBal(_svcType):
        """Application server load-balancer."""
        return appServer


    def dbLdBal(_svcType):
        """Database server load-balancer."""
        return dbServer


    try:
        for nUsers in (400,):  # (40, 100, 200, 300, 400):
            for simTime in (100,):  # (1000,):

                env = simpy.Environment()
                random.seed(12345)

                appServer = Server(env, 20, 40, 100, "AppServer")
                dbServer = Server(env, 10, 20, 200, "DbServer")

                servers = (appServer, dbServer)  # to facilitate printing of inputs

                txn_1 = CoreSvcRequester(env, "txn_1", cug(2, 1), appLdBal)
                txn_2_2 = CoreSvcRequester(env, "txn_2_2", cug(12, 6), dbLdBal)
                txn_2_3 = CoreSvcRequester(env, "txn_2_3", cug(16, 8), dbLdBal)
                txn_2_3a = Async(env, txn_2_3)
                txn_2_0 = CoreSvcRequester(env, "txn_2_0", cug(3, 1.5), appLdBal)
                txn_2_1 = Seq(env, "txn_2_1", [txn_2_0, txn_2_3a, txn_2_2])

                weightedTxns = [(txn_1, 3),
                                (txn_2_1, 1)
                               ]

                minThinkTime = 5
                maxThinkTime = 35

                userGroup = UserGroup(env, nUsers, "UserTypeX", weightedTxns, minThinkTime, maxThinkTime)
                userGroups = (userGroup,)  # to facilitate printing of inputs

                userGroup.activateUsers()

                maxSimtime = simTime

                print("\n\n***** Start Simulation *****", file=fi)
                print("Simulation: nUsers =", nUsers, "; simTime =", simTime, file=fi)

                env.run(until=maxSimtime)

                print("<< ServerExample >>\n", file=fi)

                indent = " " * 4

                # print parameters
                print("\n" + "maxSimtime =", maxSimtime, file=fi)

                print("\n" + "Servers:", file=fi)
                for svr in servers:
                    print(indent*1 + "Server:", svr.name, file=fi)
                    print(indent*2 + "maxConcurrency =", svr.maxConcurrency, file=fi)
                    print(indent*2 + "numThreads =", svr.numThreads, file=fi)
                    print(indent*2 + "speed =", svr.speed, file=fi)
                    print(indent*2 + "throughput =", svr.throughput, file=fi)
                    print(indent*2 + "avgProcessTime =", svr.avgProcessTime, file=fi)
                    print(indent*2 + "avgQueueTime =", svr.avgHwQueueTime, file=fi)
                    print(indent*2 + "avgServiceTime =", svr.avgServiceTime, file=fi)
                    print(indent*2 + "avgQueueLength =", svr.avgHwQueueLength, file=fi)
                    print(indent*2 + "utilization =", svr.utilization, file=fi)

                print("\n" + "User Groups:", file=fi)
                for grp in userGroups:
                    print(indent*1 + "Group:", grp.name, file=fi)
                    print(indent*2 + "numUsers =", grp.numUsers, file=fi)
                    print(indent*2 + "minThinkTime =", grp.minThinkTime, file=fi)
                    print(indent*2 + "maxThinkTime =", grp.maxThinkTime, file=fi)
                    print(indent*2 + "request count =",
                        grp._overallTally.num(), file=fi)
                    print(indent*2 + "avg response time =",
                        grp._overallTally.mean(), file=fi)

                    for txn in grp._txns:
                        print(indent*2 + txn.svcName + ":", file=fi)
                        print(indent*3 + "count =", grp._tallyDict[txn].num(), file=fi)
                        print(indent*3 + "avg response time =", grp._tallyDict[txn].mean(), file=fi)
                        print(indent*3 + "std dev of response time =",
                            math.sqrt(abs(grp._tallyDict[txn].variance())), file=fi)

    finally:
        if not fi == sys.stdout:
            fi.close()
        print("\n*** Done ***", file=fi)


if __name__ == "__main__":
    simple_serversim_example()
