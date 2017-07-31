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
        print(indent * 2 + "maxConcurrency = %s" % server.maxConcurrency)
        print(indent * 2 + "numThreads = %s" % server.numThreads)
        print(indent * 2 + "speed = %s" % server.speed)
        print(indent * 2 + "throughput = %s" % server.throughput)
        print(indent * 2 + "avgProcessTime = %s" % server.avgProcessTime)
        print(indent * 2 + "avgHwQueueTime = %s" % server.avgHwQueueTime)
        print(indent * 2 + "avgServiceTime = %s" % server.avgServiceTime)
        print(indent * 2 + "avgHwQueueLength = %s" % server.avgHwQueueLength)
        print(indent * 2 + "utilization = %s" % server.utilization)
