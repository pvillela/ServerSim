"""
Observational tests for CoreSvcRequester
"""

import pytest
from hamcrest import assert_that, close_to, greater_than, less_than, equal_to

import random
import sys
import math
import logging

import simpy

from serversim import *


logging.basicConfig(level=logging.INFO,
                    format='%(levelname)-4s %(message)s')

random.seed(12345)


@pytest.fixture(scope="module")
def fi():
    # fi = open("simout.txt", "w")
    fi = sys.stdout
    yield fi
    if not fi == sys.stdout:
        fi.close()
    print "\n*** Done ***"


def cug(mid, delta):
    """Computation units generator"""
    def f():
        return random.uniform(mid - delta, mid + delta)
    return f


########################
# Parameters

minHwThreads = 1
maxHwThreads = 100
minSwThreadsFactor = 1
maxSwThreadsFactor = 100
minSpeed = 1
maxSpeed = 100

minCompUnits = 1
maxCompUnits = 100

# end Parameters
########################


def gen_servers_and_core_svc_requesters(env, ffServer, svcReqLog, nServers, nSvcRqrs):
    """
    Parameterizadion for:
            compUnits
            svcRqr
            fServer
    """
    def fServerIter():
        for i in range(0, nServers):
            hwThreads = random.randint(minHwThreads, maxHwThreads)
            swThreads = hwThreads * random.randint(minSwThreadsFactor, maxSwThreadsFactor)
            speed = random.uniform(minSpeed, maxSpeed)
            server = Server(env, hwThreads, swThreads, speed, "Server_" + str(i))
            yield server

    serverLst = list(fServerIter())

    def fSvcRqrIter():
        for i in range(0, nSvcRqrs):
            compUnits = random.randint(minCompUnits, maxCompUnits)
            fServer = ffServer(serverLst)
            svcRqr = CoreSvcRequester(env, "txn_" + str(i), cug(compUnits, 0), fServer, svcReqLog)
            yield svcRqr

    svcRqrLst = list(fSvcRqrIter())

    return serverLst, svcRqrLst


@pytest.mark.parametrize("i", range(0, 20))
@pytest.mark.parametrize(
    "nServers, nSvcRqrs", [
        (1, 1),
       (5, 20),
       (5, 100)
    ]
)
def test_core_svc_requester(i, nServers, nSvcRqrs, fi):

    env = simpy.Environment()
    svcReqLog = list()

    def ffServer(serverLst):
        def fServer(_svcReqName):
            return random.choice(serverLst)
        return fServer

    serverLst, svcRqrLst = gen_servers_and_core_svc_requesters(env, ffServer, svcReqLog, nServers, nSvcRqrs)

    for svcRqr in svcRqrLst:
        svcReq = svcRqr.makeSvcRequest(None)
        svcReq.submit()

    simTime = 10000
    print >> fi, "\n\n***** Start Simulation *****"
    print "Simulation: simTime =", simTime
    env.run(until=simTime)

    delta = 0.0001

    indent = " " * 4

    for svcRqr in svcRqrLst:
        server = svcReq.server

        assert_that(svcReq.processTime,
                    close_to(svcReq.compUnits / (server.speed / server.maxConcurrency), delta))

        print >> fi, "\n" + "Service request:"
        print >> fi, indent * 1 + svcReq.svcName + ":"
        print >> fi, indent * 2 + str(svcReq.timeLog)

    for server in serverLst:
        svcReqLog = server.svcReqLog
        nSvcReqs = len(svcReqLog)
        # assert_that(nSvcReqs, greater_than(0))
        if nSvcReqs != 0:
            avgSvcReqProcessTime = \
                sum([svcReq.processTime for svcReq in svcReqLog]) / nSvcReqs
            avgSvcReqHwQueueTime = \
                sum([svcReq.hwQueueTime for svcReq in svcReqLog]) / nSvcReqs
            avgSvcReqServiceTime = \
                sum([svcReq.serviceTime for svcReq in svcReqLog]) / nSvcReqs

            assert_that(avgSvcReqProcessTime, close_to(server.avgProcessTime, delta))
            assert_that(avgSvcReqHwQueueTime, close_to(server.avgQueueTime, delta))
            assert_that(avgSvcReqServiceTime, close_to(server.avgServiceTime, delta))

    for server in serverLst:

        print >> fi, "<< ServerExample >>\n"

        print >> fi, "\n" + "Server:"
        print >> fi, indent*1 + "Server:", server.name
        print >> fi, indent*2 + "maxConcurrency =", server.maxConcurrency
        print >> fi, indent*2 + "numThreads =", server.numThreads
        print >> fi, indent*2 + "speed =", server.speed
        print >> fi, indent*2 + "throughput =", server.throughput
        print >> fi, indent*2 + "avgProcessTime =", server.avgProcessTime
        print >> fi, indent*2 + "avgQueueTime =", server.avgQueueTime
        print >> fi, indent*2 + "avgServiceTime =", server.avgServiceTime
        print >> fi, indent*2 + "avgQueueLength =", server.avgQueueLength
        print >> fi, indent*2 + "utilization =", server.utilization
