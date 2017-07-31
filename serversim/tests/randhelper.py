"""
Helpers for tests with random generators.
"""

import random

from serversim import Server, CoreSvcRequester
from serversim.randutil import probChooser, rand_int, gen_int, rand_float, \
    gen_float, rand_choice, gen_choice, rand_list, gen_list


random.seed(12345)

###################
# Global

N_EXAMPLES = 100

# end global
###################


def cug(mid, delta):
    """Computation units generator"""
    def f():
        return random.uniform(mid - delta, mid + delta)
    return f


def defaultFfServer(serverLst):
    def fServer(_svcReqName):
        return random.choice(serverLst)
    return fServer


class ServersimRandom(object):
    """Random generation of serversim objects."""

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


    def gen_server(self, env):
        seq = [0]

        def gen_server0(seq):
            hwThreads = rand_int(self.minHwThreads, self.maxHwThreads)
            swThreads = hwThreads * rand_int(self.minSwThreadsFactor,
                                             self.maxSwThreadsFactor)
            speed = rand_float(self.minSpeed, self.maxSpeed)
            seq[0] += 1
            return Server(env, hwThreads, swThreads, speed,
                          "Server_" + str(seq[0]))

        def ret():
            return gen_server0(seq)

        return ret


    def gen_svc_rqr(self, env, serverLst):
        seq = [0]

        def gen_svc_rqr0(seq):
            compUnits = rand_float(self.minCompUnits, self.maxCompUnits)
            fServer = self.ffServer(serverLst)
            seq[0] += 1
            return CoreSvcRequester(env, "Txn_" + str(seq[0]),
                                    cug(compUnits, compUnits / 2), fServer,
                                    self.svcReqLog)

        def ret():
            return gen_svc_rqr0(seq)

        return ret


    def rand_servers_svc_rqrs(self, env):
        nServers = rand_int(1, self.maxServers)
        nSvcRqrs = rand_int(1, self.maxSvcRqrs)
        serverLst = rand_list(self.gen_server(env), nServers, nServers)
        svcRqrLst = rand_list(self.gen_svc_rqr(env, serverLst), nSvcRqrs, nSvcRqrs)
        return (serverLst, svcRqrLst)
