"""
Simple test of SimComponents
"""

import random
import sys
import math
import logging

import simpy

from simcomponents import *


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
            txn_2_1 = CallSeq(env, "txn_2_1", txn_2_0, [txn_2_3a, txn_2_2])

            weightedTxns = [(txn_1, 3),
                            (txn_2_1, 1)
                           ]

            minThinkTime = 5
            maxThinkTime = 35

            userGroup = UserGroup(env, nUsers, "UserTypeX", weightedTxns, minThinkTime, maxThinkTime)
            userGroups = (userGroup,)  # to facilitate printing of inputs

            userGroup.activateUsers()

            maxSimtime = simTime

            print >> fi, "\n\n***** Start Simulation *****"
            print "Simulation: nUsers =", nUsers, "; simTime =", simTime

            env.run(until=maxSimtime)

            print >> fi, "<< ServerExample >>\n"

            indent = " " * 4

            # print parameters
            print >> fi, "\n" + "maxSimtime =", maxSimtime

            print >> fi, "\n" + "Servers:"
            for svr in servers:
                print >> fi, indent*1 + "Server:", svr.name
                print >> fi, indent*2 + "maxConcurrency =", svr.maxConcurrency
                print >> fi, indent*2 + "numThreads =", svr.numThreads
                print >> fi, indent*2 + "speed =", svr.speed
                print >> fi, indent*2 + "throughput =", svr.throughput
                print >> fi, indent*2 + "avgProcessTime =", svr.avgProcessTime
                print >> fi, indent*2 + "avgQueueTime =", svr.avgQueueTime
                print >> fi, indent*2 + "avgServiceTime =", svr.avgServiceTime
                print >> fi, indent*2 + "avgQueueLength =", svr.avgQueueLength
                print >> fi, indent*2 + "utilization =", svr.utilization

            print >> fi, "\n" + "User Groups:"
            for grp in userGroups:
                print >> fi, indent*1 + "Group:", grp.name
                print >> fi, indent*2 + "numUsers =", grp.numUsers
                print >> fi, indent*2 + "minThinkTime =", grp.minThinkTime
                print >> fi, indent*2 + "maxThinkTime =", grp.maxThinkTime
                print >> fi, indent*2 + "request count =", \
                    grp._overallTally.num()
                print >> fi, indent*2 + "avg response time =", \
                    grp._overallTally.mean()

                for txn in grp._txns:
                    print >> fi, indent*2 + txn.name + ":"
                    print >> fi, indent*3 + "count =", grp._tallyDict[txn].num()
                    print >> fi, indent*3 + "avg response time =", grp._tallyDict[txn].mean()
                    print >> fi, indent*3 + "std dev of response time =", \
                        math.sqrt(abs(grp._tallyDict[txn].variance()))

finally:
    if not fi == sys.stdout:
        fi.close()
    print "\n*** Done ***"
