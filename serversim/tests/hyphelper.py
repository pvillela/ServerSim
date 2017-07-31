"""
Helpers for tests with Hypothesis framework.
"""

from hypothesis import settings
from hypothesis.strategies import composite, integers, floats, lists

from serversim import Server, CoreSvcRequester

from randhelper import cug, defaultFfServer


settings.register_profile("pv", settings(
    timeout = -1,
    database_file = None,
    derandomize = True,
    max_examples = 100,  # default = 200
    # verbosity = Verbosity.verbose  # useless
))

settings.load_profile("pv")


class ServersimHypStrategies(object):
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
                 svcReqLog=None):
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
