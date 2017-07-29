"""
Observational tests for CoreSvcRequester
"""

from __future__ import print_function

import logging

import simpy
import pytest
from hamcrest import assert_that, close_to, greater_than, less_than, equal_to
from hypothesis import given, example, settings, Verbosity
from hypothesis.strategies import data, choices, lists, integers

# from serversim import *
from helper import fi, dump_servers, dump_svc_reqs, servers_strat, svc_rqrs_strat


_testCount = 0

# @pytest.mark.parametrize(
#     "nServers, nSvcRqrs, dump", [
#         (1, 1, True),
#         # (5, 20, False),
#         # (5, 100, False)
#     ]
# )
@given(data())
# def test_core_svc_requester(data):
# def t_core_svc_requester(fi, nServers, nSvcRqrs, dump, data):
def t_core_svc_requester(fi, maxServers, maxSvcRqrs, dump, data):

    global _testCount

    draw = data.draw

    nServers = draw(integers(1, maxServers))
    nSvcRqrs = draw(integers(1, maxSvcRqrs))

    def ffServer(serverLst):
        def fServer(_svcReqName):
            choice = draw(choices())
            return choice(serverLst)
        return fServer

    env = simpy.Environment()
    svcReqLog = list()

    _testCount = _testCount + 1
    testCount = _testCount

    print("\n\n@@@@@@@@ Start test :", testCount, ", nServers:", nServers, ", nSvcRqrs:", nSvcRqrs, file=fi)
    serverLst = draw(lists(servers_strat(env), nServers, None, nServers))
    print("Drew serverLst")
    # print(">>> " + str(serverLst), file=fi)

    svcRqrLst = draw(lists(svc_rqrs_strat(env, serverLst, ffServer, {0:svcReqLog}), nSvcRqrs, None, nSvcRqrs))
    print("Drew svcRqrLst")
    # print(">>> " + str(svcRqrLst), file=fi)

    for svcRqr in svcRqrLst:
        # print(">>> submitting " + str(svcRqr), file=fi)
        svcReq = svcRqr.makeSvcRequest(None)
        svcReq.submit()

    simTime = 1000000000
    print("\n\n***** Start Simulation (%s, %s, %s)-%s *****" % (nServers, nSvcRqrs, dump, testCount), file=fi)
    print("Simulation: simTime = %s" %  simTime, file=fi)
    env.run(until=simTime)

    delta = 0.0001

    if dump: dump_svc_reqs(svcReqLog)

    for svcReq in svcReqLog:
        server = svcReq.server
        assert_that(svcReq.processTime,
                    close_to(svcReq.compUnits / (server.speed / server.maxConcurrency), delta))

    if dump: dump_servers(serverLst)

    for server in serverLst:
        print(">>>", server.name, "hwThreads=", server.maxConcurrency, "_threads=", server.numThreads, "speed=", server.speed, file=fi)
        svcReqLog = server.svcReqLog
        nSvcReqs = len(svcReqLog)
        print("nSvcReqs", nSvcReqs, file=fi)
        # assert_that(nSvcReqs, greater_than(0))
        if nSvcReqs != 0:
            print("svcReq processTimes", [(svcReq.svcName, svcReq.processTime) for svcReq in svcReqLog], file=fi)
            print("svcReq hwQueueTimes", [(svcReq.svcName, svcReq.hwQueueTime) for svcReq in svcReqLog], file=fi)
            print("svcReq serviceTimes", [(svcReq.svcName, svcReq.serviceTime) for svcReq in svcReqLog], file=fi)
            avgSvcReqProcessTime = \
                sum([svcReq.processTime for svcReq in svcReqLog]) / nSvcReqs
            avgSvcReqHwQueueTime = \
                sum([svcReq.hwQueueTime for svcReq in svcReqLog]) / nSvcReqs
            avgSvcReqServiceTime = \
                sum([svcReq.serviceTime for svcReq in svcReqLog]) / nSvcReqs
            print("Before assertions", file=fi)
            print(avgSvcReqProcessTime, server.avgProcessTime, file=fi)
            print(avgSvcReqHwQueueTime, server.avgHwQueueTime, file=fi)
            print(avgSvcReqServiceTime, server.avgServiceTime, file=fi)
            assert_that(avgSvcReqProcessTime, close_to(server.avgProcessTime, delta))
            assert_that(avgSvcReqHwQueueTime, close_to(server.avgHwQueueTime, delta))
            assert_that(avgSvcReqServiceTime, close_to(server.avgServiceTime, delta))

    print("@@@@@@@@ End test: " + str(testCount) + " ended: " + str(env.now), file=fi)


# @pytest.mark.parametrize(
#     "nServers, nSvcRqrs, dump", [
#         # (1, 1, False),
#         # (5, 20, True),
#         (5, 100, False)
#     ]
# )
# def test_core_svc_requester1(fi, nServers, nSvcRqrs, dump):
#     t_core_svc_requester(fi, nServers, nSvcRqrs, dump)


@pytest.mark.parametrize(
    "maxServers, maxSvcRqrs, dump", [
        # (1, 1, False),
        # (5, 20, True),
        (10, 2000, False)
    ]
)
def test_core_svc_requester1(fi, maxServers, maxSvcRqrs, dump):
    t_core_svc_requester(fi, maxServers, maxSvcRqrs, dump)


# @given(nServers=integers(5, 5), nSvcRqrs=integers(100, 100))
# @pytest.mark.parametrize("dump", [False])
# def test_core_svc_requester2(fi, nServers, nSvcRqrs, dump):
#     t_core_svc_requester(fi, nServers, nSvcRqrs, dump)
