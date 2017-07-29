"""
Observational tests for CoreSvcRequester
"""

import random

import simpy
import pytest
from hamcrest import assert_that, close_to, greater_than, less_than, equal_to

# from serversim import *
from helper import gen_servers, gen_core_svc_requesters, dump_servers, \
    dump_svc_reqs


def t_core_svc_requester(i, nServers, nSvcRqrs, dump):

    env = simpy.Environment()
    svcReqLog = list()

    def ffServer(serverLst):
        def fServer(_svcReqName):
            return random.choice(serverLst)
        return fServer

    serverLst = gen_servers(env, nServers)
    svcRqrLst = gen_core_svc_requesters(env, serverLst, ffServer, svcReqLog, nSvcRqrs)

    for svcRqr in svcRqrLst:
        svcReq = svcRqr.makeSvcRequest(None)
        svcReq.submit()

    simTime = 10000
    print("\n\n***** Start Simulation (%s, %s, %s)-%s *****" % (nServers, nSvcRqrs, dump, i))
    print("Simulation: simTime = %s" %  simTime)
    env.run(until=simTime)

    delta = 0.0001

    if dump: dump_svc_reqs(svcReqLog)

    for svcReq in svcReqLog:
        server = svcReq.server
        assert_that(svcReq.processTime,
                    close_to(svcReq.compUnits / (server.speed / server.maxConcurrency), delta))

    if dump: dump_servers(serverLst)

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
            assert_that(avgSvcReqHwQueueTime, close_to(server.avgHwQueueTime, delta))
            assert_that(avgSvcReqServiceTime, close_to(server.avgServiceTime, delta))


@pytest.mark.parametrize("i", range(20))
@pytest.mark.parametrize(
    "nServers, nSvcRqrs, dump", [
        (1, 1, True),
        (5, 20, True),
        # (5, 100, False)
    ]
)
def test_core_svc_requester1(i, nServers, nSvcRqrs, dump):
    t_core_svc_requester(i, nServers, nSvcRqrs, dump)


@pytest.mark.parametrize("i", range(10))
@pytest.mark.parametrize(
    "nServers, nSvcRqrs, dump", [
        # (1, 1, True),
        # (5, 20, True),
        (5, 100, False)
    ]
)
def test_core_svc_requester2(i, nServers, nSvcRqrs, dump):
    t_core_svc_requester(i, nServers, nSvcRqrs, dump)
