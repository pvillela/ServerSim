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

from testhelper import fi, dump_servers, dump_svc_reqs
from hyphelper import ServersimHypStrategies


pytestmark = pytest.mark.skip("Disable Hypothesis tests.")


@pytest.mark.parametrize(
    "maxServers, maxSvcRqrs, maxSvcReqs, dump", [
        # (1, 1, 100, False),
        # (5, 20, 100, True),
        (10, 20, 1000, False)
    ]
)
def test_core_svc_requester_hy(fi, maxServers, maxSvcRqrs, maxSvcReqs, dump):

    sst = ServersimHypStrategies(
        maxServers=maxServers,
        maxSvcRqrs=maxSvcRqrs,
    )

    testCountCell = [0]

    @given(data())
    def t_core_svc_requester(data):
        """
        Scenario: A core service request's process time on a server
            The process time is request.compUnits / (server.speed /
                server.max_concurrency).

        Scenario: Server average time stats
            Server stats are aggregates of service request stats for all core
                service requests that have completed processing on the server:

                The server's average processing time is the average of the
                    processing time over all core service requests processed
                    on the server.
                The server's average (_hardware thread) queue time is the average
                    of the (_hardware thread) queue time over all core service
                    requests processed on the server.
                The server's average service time is the average of the service
                    time over all core service requests processed on the server.
        """

        draw = data.draw
        env = simpy.Environment()
        testCountCell[0] += 1
        testCount = testCountCell[0]
        serverLst, svcRqrLst = draw(sst.servers_svc_rqrs(env))
        nSvcReqs = draw(integers(1, maxSvcReqs))
        svcReqLog = sst.svcReqLog
        nServers = len(serverLst)
        nSvcRqrs = len(svcRqrLst)

        print("\n\n@@@@@@@@ Start test :", testCount, ", nServers:", nServers,
              ", nSvcRqrs:", nSvcRqrs, "nSvcReqs:", nSvcReqs, file=fi)

        for i in range(nSvcReqs):
            # svcRqr = choice(svcRqrLst)  # this is expensive, replaced below
            j = random.randint(0, len(svcRqrLst) - 1)
            svcRqr = svcRqrLst[j]
            svcReq = svcRqr.make_svc_request(None)
            # print(">>> submitting", svcRqr.svc_name, file=fi)
            svcReq.submit()

        simTime = 1000000000
        print("\n\n***** Start Simulation (%s, %s, %s)-%s *****" % (
            nServers, nSvcRqrs, dump, testCount), file=fi)
        print("Simulation: simTime = %s" % simTime, file=fi)
        env.run(until=simTime)

        delta = 0.0001

        if dump: dump_svc_reqs(svcReqLog)

        # Scenario: A core service request's process time on a server
        #     The process time is request.compUnits / (server.speed /
        #         server.max_concurrency).
        for svcReq in svcReqLog:
            server = svcReq.server
            assert_that(svcReq.process_time,
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
        #         The server's average (_hardware thread) queue time is the average
        #             of the (_hardware thread) queue time over all core service
        #             requests processed on the server.
        #         The server's average service time is the average of the service
        #             time over all core service requests processed on the server.
        for server in serverLst:
            print(">>>", server.name, "hwThreads=", server.maxConcurrency,
                  "_threads=", server.numThreads, "speed=", server.speed, file=fi)
            svcReqLog = server.svc_req_log
            nSvcReqs = len(svcReqLog)
            print("nSvcReqs", nSvcReqs, file=fi)
            if nSvcReqs != 0:
                print("svcReq processTimes",
                      [(svcReq.svcName, svcReq.process_time) for svcReq in
                       svcReqLog], file=fi)
                print("svcReq hwQueueTimes",
                      [(svcReq.svcName, svcReq.hw_queue_time) for svcReq in
                       svcReqLog], file=fi)
                print("svcReq serviceTimes",
                      [(svcReq.svcName, svcReq.service_time) for svcReq in
                       svcReqLog], file=fi)
                avgSvcReqProcessTime = \
                    sum([svcReq.process_time for svcReq in svcReqLog]) / nSvcReqs
                avgSvcReqHwQueueTime = \
                    sum([svcReq.hw_queue_time for svcReq in svcReqLog]) / nSvcReqs
                avgSvcReqServiceTime = \
                    sum([svcReq.service_time for svcReq in svcReqLog]) / nSvcReqs
                print("Before assertions", file=fi)
                print(avgSvcReqProcessTime, server.avg_process_time, file=fi)
                print(avgSvcReqHwQueueTime, server.avg_hw_queue_time, file=fi)
                print(avgSvcReqServiceTime, server.avg_service_time, file=fi)
                assert_that(avgSvcReqProcessTime,
                            close_to(server.avg_process_time, delta))
                assert_that(avgSvcReqHwQueueTime,
                            close_to(server.avg_hw_queue_time, delta))
                assert_that(avgSvcReqServiceTime,
                            close_to(server.avg_service_time, delta))

        print("@@@@@@@@ End test: " + str(testCount) + " ended: " + str(env.now),
              file=fi)

    t_core_svc_requester()
