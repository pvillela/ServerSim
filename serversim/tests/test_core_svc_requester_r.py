"""
Manual random tests for CoreSvcRequester
"""

from __future__ import print_function

import random
import sys

import simpy
import pytest
from hamcrest import assert_that, close_to #, greater_than, less_than, equal_to

from serversim.randutil import prob_chooser, rand_int, gen_int, rand_float, \
    gen_float, rand_choice, gen_choice, rand_list, gen_list
from testhelper import fi, dump_servers, dump_svc_reqs
from randhelper import ServersimRandom, repeat, inject_servers_svcrqrs


# @pytest.mark.parametrize(
    # "maxServers, maxSvcRqrs, maxSvcReqs, dump", [
    #     # (1, 1, 100, False),
    #     # (5, 20, 100, True),
    #     (10, 20, 1000, False)
    # ]
    # "dump", [False]
# )
@inject_servers_svcrqrs(fi=fi(), dump=False)
def test_a_core_service_requests_process_time_on_a_server_r(
        test_count,
        env,
        serverLst,
        svcRqrLst,
        nSvcReqs,
        svcReqLog,
        nServers,
        nSvcRqrs,
        fi,
        dump=False
    ):

    func_name = sys._getframe().f_code.co_name

    print("\n\n@@@@@@@@ Start", func_name, "-", test_count, "- nServers:", nServers,
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
        nServers, nSvcRqrs, dump, test_count), file=fi)
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

    print("@@@@@@@@ End test: " + str(test_count) + " ended: " + str(env.now),
          file=fi)
