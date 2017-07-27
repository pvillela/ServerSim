"""
Test helpers.
"""

import pytest
from hamcrest import assert_that, close_to, greater_than, less_than, equal_to

import random
import sys
import logging

import simpy

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

_seed = 12345

_indent = " " * 4

# end Parameters
########################


logging.basicConfig(level=logging.INFO,
                    format='%(levelname)-4s %(message)s')

random.seed(_seed)


@pytest.fixture(scope="module")
def fi():
    # fi = open("simout.txt", "w")
    fi = sys.stdout
    yield fi
    if not fi == sys.stdout:
        fi.close()
    print "\n*** Done ***"


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
        print(_indent * 1 + svcReq.svcName + ":")
        print(_indent * 2 + str(svcReq.timeLog))


def dump_servers(serverLst):
    print("\n<< Servers >>")
    for server in serverLst:
        print(_indent * 1 + "Server: %s" % server.name)
        print(_indent * 2 + "maxConcurrency = %s" % server.maxConcurrency)
        print(_indent * 2 + "numThreads = %s" % server.numThreads)
        print(_indent * 2 + "speed = %s" % server.speed)
        print(_indent * 2 + "throughput = %s" % server.throughput)
        print(_indent * 2 + "avgProcessTime = %s" % server.avgProcessTime)
        print(_indent * 2 + "avgQueueTime = %s" % server.avgQueueTime)
        print(_indent * 2 + "avgServiceTime = %s" % server.avgServiceTime)
        print(_indent * 2 + "avgQueueLength = %s" % server.avgQueueLength)
        print(_indent * 2 + "utilization = %s" % server.utilization)
