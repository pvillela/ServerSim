"""
Tests for CoreSvcRequester
"""

from __future__ import print_function

import random

import simpy
import pytest
from hamcrest import assert_that, close_to #, greater_than, less_than, equal_to
from hypothesis import given
from hypothesis.strategies import data, choices, lists, integers

from helper import fi, dump_servers, dump_svc_reqs, servers_svc_rqrs_st


####################
# Module globals

_testCount = 0

# end module globals
####################


@given(data())
def t_core_svc_requester(fi, maxServers, maxSvcRqrs, maxSvcReqs, dump, data):
    """
    Scenario: A core service request's process time on a server
        The process time is request.compUnits / (server.speed /
            server.maxConcurrency).

    Scenario: Server average time stats
        Server stats are aggregates of service request stats for all core
            service requests that have completed processing on the server:

            The server's average processing time is the average of the
                processing time over all core service requests processed
                on the server.
            The server's average (hardware thread) queue time is the average
                of the (hardware thread) queue time over all core service
                requests processed on the server.
            The server's average service time is the average of the service
                time over all core service requests processed on the server.
    """

    global _testCount

    draw = data.draw
    choice = draw(choices())

    env = simpy.Environment()
    svcReqLog = list()

    serverLst, svcRqrLst = draw(
        servers_svc_rqrs_st(env, maxServers, maxSvcRqrs, {0:svcReqLog}))
    nServers = len(serverLst)
    nSvcRqrs = len(svcRqrLst)
    nSvcReqs = draw(integers(1, maxSvcReqs))

    _testCount = _testCount + 1

    print("\n\n@@@@@@@@ Start test :", _testCount, ", nServers:", nServers,
          ", nSvcRqrs:", nSvcRqrs, "nSvcReqs:", nSvcReqs, file=fi)

    for i in range(nSvcReqs):
        # svcRqr = choice(svcRqrLst)  # this is expensive, replaced below
        j = random.randint(0, len(svcRqrLst) - 1)
        svcRqr = svcRqrLst[j]
        svcReq = svcRqr.makeSvcRequest(None)
        # print(">>> submitting", svcRqr.svcName, file=fi)
        svcReq.submit()

    simTime = 1000000000
    print("\n\n***** Start Simulation (%s, %s, %s)-%s *****" % (
        nServers, nSvcRqrs, dump, _testCount), file=fi)
    print("Simulation: simTime = %s" % simTime, file=fi)
    env.run(until=simTime)

    delta = 0.0001

    if dump: dump_svc_reqs(svcReqLog)

    # Scenario: A core service request's process time on a server
    #     The process time is request.compUnits / (server.speed /
    #         server.maxConcurrency).
    for svcReq in svcReqLog:
        server = svcReq.server
        assert_that(svcReq.processTime,
                    close_to(svcReq.compUnits / (
                    server.speed / server.maxConcurrency), delta))

    if dump: dump_servers(serverLst)

    # Scenario: Server average time stats
    #     Server stats are aggregates of service request stats for all core
    #         service requests that have completed processing on the server:
    #
    #         The server's average processing time is the average of the
    #             processing time over all core service requests processed
    #             on the server.
    #         The server's average (hardware thread) queue time is the average
    #             of the (hardware thread) queue time over all core service
    #             requests processed on the server.
    #         The server's average service time is the average of the service
    #             time over all core service requests processed on the server.
    for server in serverLst:
        print(">>>", server.name, "hwThreads=", server.maxConcurrency,
              "_threads=", server.numThreads, "speed=", server.speed, file=fi)
        svcReqLog = server.svcReqLog
        nSvcReqs = len(svcReqLog)
        print("nSvcReqs", nSvcReqs, file=fi)
        if nSvcReqs != 0:
            print("svcReq processTimes",
                  [(svcReq.svcName, svcReq.processTime) for svcReq in
                   svcReqLog], file=fi)
            print("svcReq hwQueueTimes",
                  [(svcReq.svcName, svcReq.hwQueueTime) for svcReq in
                   svcReqLog], file=fi)
            print("svcReq serviceTimes",
                  [(svcReq.svcName, svcReq.serviceTime) for svcReq in
                   svcReqLog], file=fi)
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
            assert_that(avgSvcReqProcessTime,
                        close_to(server.avgProcessTime, delta))
            assert_that(avgSvcReqHwQueueTime,
                        close_to(server.avgHwQueueTime, delta))
            assert_that(avgSvcReqServiceTime,
                        close_to(server.avgServiceTime, delta))

    print("@@@@@@@@ End test: " + str(_testCount) + " ended: " + str(env.now),
          file=fi)


@pytest.mark.parametrize(
    "maxServers, maxSvcRqrs, maxSvcReqs, dump", [
        # (1, 1, 100, False),
        # (5, 20, 100, True),
        (10, 20, 2000, False)
    ]
)
def test_core_svc_requester1(fi, maxServers, maxSvcRqrs, maxSvcReqs, dump):
    t_core_svc_requester(fi, maxServers, maxSvcRqrs, maxSvcReqs, dump)
