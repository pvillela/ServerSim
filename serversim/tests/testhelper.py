"""
Helpers for tests.
"""

import pytest

from serversim import const, indent


@pytest.fixture(scope="module")
def fi():
    return const.logfile


@pytest.fixture(scope="module")
def logfile():
    return const.logfile


def dump_svc_reqs(svcReqLog):
    print("\n<< Service requests >>")
    for svcReq in svcReqLog:
        print(indent * 1 + svcReq.svcName + ":")
        print(indent * 2 + str(svcReq.timeLog))


def dump_servers(serverLst):
    print("\n<< Servers >>")
    for server in serverLst:
        print(indent * 1 + "Server: %s" % server.name)
        print(indent * 2 + "max_concurrency = %s" % server.maxConcurrency)
        print(indent * 2 + "num_threads = %s" % server.numThreads)
        print(indent * 2 + "speed = %s" % server.speed)
        print(indent * 2 + "throughput = %s" % server.throughput)
        print(indent * 2 + "avg_process_time = %s" % server.avg_process_time)
        print(indent * 2 + "avg_hw_queue_time = %s" % server.avg_hw_queue_time)
        print(indent * 2 + "avg_service_time = %s" % server.avg_service_time)
        print(indent * 2 + "avg_hw_queue_length = %s" % server.avg_hw_queue_length)
        print(indent * 2 + "utilization = %s" % server.utilization)
