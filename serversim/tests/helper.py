"""
Test helpers.
"""

import pytest
from hypothesis.strategies import composite, integers, floats, lists, choices

from serversim import *


########################
# Module global parameters

_minHwThreads = 1
_maxHwThreads = 100
_minSwThreadsFactor = 1
_maxSwThreadsFactor = 100
_minSpeed = 1
_maxSpeed = 100

_minCompUnits = 1
_maxCompUnits = 100

# end Parameters
########################


@pytest.fixture(scope="module")
def fi():
    return const.logfile


@pytest.fixture(scope="module")
def logfile():
    return const.logfile


def cug(mid, delta):
    """Computation units generator"""
    def f():
        return random.uniform(mid - delta, mid + delta)
    return f


def gen_servers(env, nServers):

    def fServerIter():
        for i in range(0, nServers):
            hwThreads = random.randint(_minHwThreads, _maxHwThreads)
            swThreads = hwThreads * random.randint(_minSwThreadsFactor, _maxSwThreadsFactor)
            speed = random.uniform(_minSpeed, _maxSpeed)
            server = Server(env, hwThreads, swThreads, speed, "Server_" + str(i))
            yield server

    return list(fServerIter())


def gen_core_svc_requesters(env, serverLst, ffServer, svcReqLog, nSvcRqrs):

    def fSvcRqrIter():
        for i in range(0, nSvcRqrs):
            compUnits = random.randint(_minCompUnits, _maxCompUnits)
            fServer = ffServer(serverLst)
            svcRqr = CoreSvcRequester(env, "txn_" + str(i), cug(compUnits, 0), fServer, svcReqLog)
            yield svcRqr

    return list(fSvcRqrIter())


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


def server_st(env):
    @composite
    def servers_strat0(draw, env, seq):
        hwThreads = draw(integers(_minHwThreads, _maxHwThreads))
        swThreads = hwThreads * draw(integers(_minSwThreadsFactor,
                                              _maxSwThreadsFactor))
        speed = draw(floats(_minSpeed, _maxSpeed))
        seq[0] += 1
        return Server(env, hwThreads, swThreads, speed, "Server_" + str(seq[0]))

    seq = {0:0}
    return servers_strat0(env, seq)


def svc_rqr_st(env, serverLst, ffServer, svcReqLogDict):
    @composite
    def svc_rqrs_strat0(draw, env, serverLst, ffServer, svcReqLogDict, seq):
        compUnits = draw(floats(_minCompUnits, _maxCompUnits))
        fServer = ffServer(serverLst)
        seq[0] += 1
        svcReqLog = svcReqLogDict[0]
        return CoreSvcRequester(env, "Txn_" + str(seq[0]), cug(compUnits, compUnits/2), fServer, svcReqLog)

    seq = {0:0}
    return svc_rqrs_strat0(env, serverLst, ffServer, svcReqLogDict, seq)


@composite
def servers_svc_rqrs_st(draw, env, maxServers, maxSvcRqrs, svcReqLogDict):

    svcReqLog = svcReqLogDict[0]

    choice = draw(choices())
    nServers = draw(integers(1, maxServers))
    nSvcRqrs = draw(integers(1, maxSvcRqrs))

    def ffServer(serverLst):
        def fServer(_svcReqName):
            return choice(serverLst)
        return fServer

    serverLst = draw(lists(server_st(env), nServers, None, nServers))
    svcRqrLst = draw(lists(svc_rqr_st(env, serverLst, ffServer, {0:svcReqLog}), nSvcRqrs, None, nSvcRqrs))

    return (serverLst, svcRqrLst)
