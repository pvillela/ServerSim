"""
Test helpers.
"""

import pytest
from hypothesis.strategies import composite, integers, floats, lists, choices

from serversim import *


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
    """ Manual random generation of lists of servers.

    Does not depend on Hypothesis.

    :param env: simpy.Environment.
    :param nServers: number of servers
    :return: random list of servers
    """
    _minHwThreads = 1
    _maxHwThreads = 100
    _minSwThreadsFactor = 1
    _maxSwThreadsFactor = 100
    _minSpeed = 1
    _maxSpeed = 100

    def fServerIter():
        for i in range(0, nServers):
            hwThreads = random.randint(_minHwThreads, _maxHwThreads)
            swThreads = hwThreads * random.randint(_minSwThreadsFactor, _maxSwThreadsFactor)
            speed = random.uniform(_minSpeed, _maxSpeed)
            server = Server(env, hwThreads, swThreads, speed, "Server_" + str(i))
            yield server

    return list(fServerIter())


def gen_core_svc_requesters(env, serverLst, ffServer, svcReqLog, nSvcRqrs):

    _minCompUnits = 1
    _maxCompUnits = 100

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


def defaultFfServer(serverLst):
    def fServer(_svcReqName):
        return random.choice(serverLst)
    return fServer


class CustomGenerationStrategies(object):
    """ Exposes custom Hypothesis generation strategies as methods.

    The strategies are parameterized by the attributes of the object
    instance.
    """

    def __init__(self,
                 minHwThreads=1,
                 maxHwThreads=100,
                 minSwThreadsFactor=1,
                 maxSwThreadsFactor=100,
                 minSpeed=1,
                 maxSpeed=100,
                 minCompUnits=1,
                 maxCompUnits=100,
                 ffServer=defaultFfServer,
                 maxServers=10,
                 maxSvcRqrs=20,
                 svcReqLog=None,
                 testCount=0):
        self.minHwThreads = minHwThreads
        self.maxHwThreads = maxHwThreads
        self.minSwThreadsFactor = minSwThreadsFactor
        self.maxSwThreadsFactor = maxSwThreadsFactor
        self.minSpeed = minSpeed
        self.maxSpeed = maxSpeed
        self.minCompUnits = minCompUnits
        self.maxCompUnits = maxCompUnits
        self.ffServer = ffServer
        self.maxServers = maxServers
        self.maxSvcRqrs = maxSvcRqrs
        if svcReqLog is None:
            svcReqLog = list()
        self.svcReqLog = svcReqLog
        self.testCount = testCount


    def server(self, env):
        @composite
        def servers_strat0(draw, seq):
            hwThreads = draw(integers(self.minHwThreads, self.maxHwThreads))
            swThreads = hwThreads * draw(integers(self.minSwThreadsFactor,
                                                  self.maxSwThreadsFactor))
            speed = draw(floats(self.minSpeed, self.maxSpeed))
            seq[0] += 1
            return Server(env, hwThreads, swThreads, speed,
                          "Server_" + str(seq[0]))

        seq = {0: 0}
        return servers_strat0(seq)


    def svc_rqr(self, env, serverLst):
        @composite
        def svc_rqrs_strat0(draw, serverLst, seq):
            compUnits = draw(floats(self.minCompUnits, self.maxCompUnits))
            fServer = self.ffServer(serverLst)
            seq[0] += 1
            return CoreSvcRequester(env, "Txn_" + str(seq[0]),
                                    cug(compUnits, compUnits / 2), fServer,
                                    self.svcReqLog)

        seq = {0: 0}
        return svc_rqrs_strat0(serverLst, seq)


    def servers_svc_rqrs(self, env):
        @composite
        def servers_svc_rqrs0(draw):
            nServers = draw(integers(1, self.maxServers))
            nSvcRqrs = draw(integers(1, self.maxSvcRqrs))
            serverLst = draw(lists(self.server(env), nServers, None, nServers))
            svcRqrLst = draw(
                lists(self.svc_rqr(env, serverLst), nSvcRqrs, None, nSvcRqrs))
            return (serverLst, svcRqrLst)

        return servers_svc_rqrs0()
