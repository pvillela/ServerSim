"""
Classes representing computing services that are executed on servers.
"""

import logging
from simpy.events import Condition

debug = logging.debug


class SvcRequest(object):
    """Represents service requests to servers.

    Inspired by completable futures.

    Attributes:
        inBlockingCall (bool): Indicates whether this request is
            in the scope of a blocking call.  When this parameter
            is true, the service request will hold a software
            thread on the target server while the service
            request itself and any of its sub-requests (calls
            to other servers) are executing.  Otherwise, the
            call is non-blocking, so a thread is held on the
            target server only while the service request itself
            is executing; the thread is relinquished when
            this request finishes executing and it passes contol
            to its sub-requests.

    """
    def __init__(self, env, svcName, fgen, server, inVal, inBlockingCall=False):
        """Initializer."""
        self._env = env
        self.svcName = svcName
        self.fgen = fgen
        self.server = server
        self.inBlockingCall = inBlockingCall
        self.inVal = inVal
        self.outVal = None
        self.id = id(self)
        self.callbacks = []
        self._isCompleted = False
        self.timeLog = list()
        self.timeDict = dict()

    # def __repr__(self):
    #     return type(self).__name__ + repr(self.__dict__)

    @property
    def env(self): return self._env

    @property
    def isCompleted(self): return self._isCompleted

    def submit(self):
        """ Submit the request to its associated server, return the
            simpy process corresponding to the request.
        """
        debug("@@@@ " + self.svcName)
        self._logTime("submitted")
        return self._env.process(self.fgen(self))

    def complete(self, val):
        """Complete the future with value val."""
        assert not self.isCompleted, "Calling complete method on a completed " \
                                     "request."
        self._isCompleted = True
        self.outVal = val
        self._logTime("completed")
        for cb in self.callbacks:
            cb(val)

    def _logTime(self, label):
        now = self._env.now
        self.timeLog.append((label, now))
        self.timeDict[label] = now

    @property
    def processTime(self):
        return self.timeDict["hw_thread_released"] - self.timeDict["hw_thread_acquired"]

    @property
    def hwQueueTime(self):
        return self.timeDict["hw_thread_acquired"] - self.timeDict["hw_thread_requested"]

    @property
    def serviceTime(self):
        return self.timeDict["completed"] - self.timeDict["submitted"]


class SvcRequester(object):
    """Base class of service requesters.

    A service request is a request for execution of computation units
    on one or more servers.  A service request can be a composite of
    sub-requests.  A service request is implemented as a SimPy Process.

    A service requester is a service request factory.
    A service requester can be a composite of sub-requesters.

    By default, a service request is non-blocking, i.e., a thread is
    held on the target server only while the service request itself
    is executing; the thread is relinquished when the request
    finishes executing and it passes contol to its sub-requests.

    Attributes:
        env: SimPy Envirornment.
        svcName (str): Name of service requester.  Represents the
            svcName of service produced by the requester.
        log (list[serversim.SvcRequest]): List that accumulates service
            requests produced by this factory.
    """

    def __init__(self, env, svcName, log=None):
        self.env = env
        self.svcName = svcName
        self.log = log

    def __repr__(self):
        return type(self).__name__ + repr(self.__dict__)

    def _fgen(self, svcReq):
        """ Returns a generator used to submit the service request to its
            associated server.

        Args:
            svcReq (serversim.SvcRequest): A service request produced by
                this factory.
        """
        raise NotImplementedError("'SvcRequester' is an abstract class.")

    def _addToLog(self, svcReq):
        if self.log is not None:
            self.log.append(svcReq)

    def makeSvcRequest(self, inVal=None, inBlockingCall=False):
        """ Produces a SvcRequest object.

        Default implementation, can be overridden.

        Args:
            inVal (any): input value of produced service request.

        Returns:
            (serversim.SvcRequest)
        """
        res = SvcRequest(self.env, self.svcName, self._fgen, None, inVal,
                         inBlockingCall)
        self._addToLog(res)
        return res


class CoreSvcRequester(SvcRequester):
    """Core srvice requester implementation.

    Typical service requesters are instances of this class or
    composites of such instances.  See the various service
    request combinators in this module.

    Attributes:
        compUnitsGen (() -> Number): A (possibly randodm) function that
            generates the number of compute units required to execute a
            service request instance.
        fServer ((str) -> serversim.Server): Function that
            produces a server (possibly round-robin, random, or based
            on server load information) when given a service request
            name.  Models a load-balancer.
        f ((any) -> any): A function that is applied to a service
            request's inVal to produce its outVal.
    """
    
    def __init__(self, env, svcName, compUnitsGen, fServer, log=None,
                 f=None):
        """Initializer."""
        SvcRequester.__init__(self, env, svcName, log)
        self.compUnitsGen = compUnitsGen
        self.fServer = fServer
        if f is None:
            f = lambda x: None
        self.f = f

    def _fgen(self, svcReq):
        """
        Returns a generator used to submit the service request to its
        associated server.
        """
        server = svcReq.server
        inBlockingCall = svcReq.inBlockingCall
        reqId = svcReq.id
        inVal = svcReq.inVal

        compUnits = self.compUnitsGen()
        svcReq.compUnits = compUnits  # ad-hoc attribute
        
        # acquire a thread if not in a blocking call
        threadReq = None
        if not inBlockingCall:
            svcReq._logTime("sw_thread_requested")
            threadReq = server.threadRequest(svcReq)
            yield threadReq
            svcReq._logTime("sw_thread_acquired")

        hwReq = server.hwRequest(svcReq)
        debug('Request for %s-%s to server %s at %s for %s compute units'
              % (self.svcName, reqId, server.name, self.env.now, compUnits))
        hwReq.processDuration = \
            server.processDuration(compUnits)  # ad-hoc attribute
        svcReq._logTime("hw_thread_requested")
        yield hwReq
        svcReq._logTime("hw_thread_acquired")

        debug('Starting to execute request %s-%s at server %s at %s for %s compute units'
              % (self.svcName, reqId, server.name, self.env.now, compUnits))
        yield self.env.timeout(hwReq.processDuration)
        server.hwRelease(hwReq)
        svcReq._logTime("hw_thread_released")
        debug('Completed executing request %s-%s at server %s at %s' \
              % (self.svcName, reqId, server.name, self.env.now))

        svcReq.complete(self.f(inVal))

        # release thread is appliccable
        if not inBlockingCall:
            server.threadRelease(threadReq)
            svcReq._logTime("sw_thread_released")

    def makeSvcRequest(self, inVal=None, inBlockingCall=False):
        """Overrides default implementation in base class.

        See base class docstring
        """
        server = self.fServer(self.svcName)
        res = super(CoreSvcRequester, self).makeSvcRequest(inVal, inBlockingCall)
        res.server = server
        return res


class Async(SvcRequester):
    """ Wraps a service requester to produce asynchronous service
        requests.

    An asynchronous service request completes and returns immediately
    to the headRequester, while the underlying (wrapped) service request is
    scheduled for execution on its target server.

    Attributes:
        svcRequester (serversim.SvcRequester): The underlying service
            requester.
    """
    
    def __init__(self, env, svcRequester, log=None):
        """Initializer."""
        svcName = "Async(" + svcRequester.svcName + ")"
        SvcRequester.__init__(self, env, svcName, log)
        self.svcRequester = svcRequester

    def _fgen(self, svcReq):
        enclosedSvcReq = self.svcRequester.makeSvcRequest(svcReq.inVal, False)
        enclosedSvcReq.submit()
        svcReq.complete(None)
        yield self.env.timeout(0)


class Blkg(SvcRequester):
    """ Wraps a service requester to produce blocking service
        requests.

    A blocking service request will hold a software thread on the
    target server until the service request itself and all of its
    non-asynchronous sub-requests complete.

    Attributes:
        svcRequester (serversim.SvcRequester): The underlying service
            requester.
    """

    def __init__(self, env, svcRequester, log=None):
        """Initializer."""
        svcName = "Blkg(" + svcRequester.svcName + ")"
        SvcRequester.__init__(self, env, svcName, log)
        self.svcRequester = svcRequester

    def _fgen(self, svcReq):
        enclosedSvcReq = self.svcRequester.makeSvcRequest(svcReq.inVal, True)
        reqThread = None
        if not svcReq.inBlockingCall:
            reqThread = enclosedSvcReq.server.threads.request(svcReq)
            svcReq._logTime("sw_thread_requested")
            yield reqThread
            svcReq._logTime("sw_thread_acquired")
        yield enclosedSvcReq.submit()
        if not svcReq.inBlockingCall:
            enclosedSvcReq.server.threads.release(reqThread)
            svcReq._logTime("sw_thread_released")
        svcReq.complete(enclosedSvcReq.outVal)


class Seq(SvcRequester):
    """ Combines a non-empty list of service requesters to yield a
        sequential composite service requester.

    This composite service requester produces composite service
    requests.  A composite service request produced by this service
    requester consists of a service request from each of the
    provided service requesters.  Each of the service requests is
    submitted in sequence, i.e., each service request is
    submitted when the previous one completes.

    Attributes:
        svcRequesters (list[serversim.SvcRequester]): See class
            docstring.
        cont (bool): If true, the sequence executes as continuations
            of the first request, all on the same server.  Otherwise,
            each request can execute on a different server.
    """

    def __init__(self, env, svcName, svcRequesters, cont=False, log=None):
        """Initializer."""
        assert len(svcRequesters) > 0, "List of service requesters " \
            "must be non-empty"
        SvcRequester.__init__(self, env, svcName, log)
        headRequester = svcRequesters[0]
        tailRequesters = svcRequesters[1:]
        self.headRequester = headRequester
        self.tailRequesters = tailRequesters
        self.cont = cont

    def _fgen(self, svcReq):
        """Generator used to submit the request to its associated server."""
        headSvcReq = self.headRequester.makeSvcRequest(svcReq.inVal,
                                                       svcReq.inBlockingCall)
        yield headSvcReq.submit()

        val = headSvcReq.outVal

        # Below, the inBlockingCall argument is False when the requests
        # produced by tailRequesters are separate service requests,
        # not continuations of previous requests on the same server.
        othersInBlockingCall = svcReq.inBlockingCall if self.cont else False

        for requester in self.tailRequesters:
            request = requester.makeSvcRequest(val, othersInBlockingCall)
            if self.cont:
                request.server = svcReq.server
            yield request.submit()
            val = request.outVal

        svcReq.complete(val)


class Par(SvcRequester):
    """ Combines a non-empty list of service requesters to yield a
        parallel composite service requester.

    This composite service requester produces composite service
    requests.  A composite service request produced by this service
    requester consists of a service request from each of the
    provided service requesters.  All of the service requests are
    submitted concurrently.

    When the attribute cont is True, this represents multi-threaded
    execution of requests on the same server.  Otherwise, each
    service request can execute on a different server.

    Attributes:
        svcRequesters (list[serversim.SvcRequester]): See class
            docstring.
        cont (bool): If true, all the requests executes on the same server.
            Otherwise, each request can execute on a different server.
            When cont is True, the server is the container service
            request's server if not None, otherwise the server is
            picked from the first service request in the list of
            generated service requests.
    """

    def __init__(self, env, svcName, svcRequesters, f=None, cont=False,
                 log=None):
        """Initializer."""
        assert len(svcRequesters) > 0, "List of service requesters " \
                                       "must be non-empty"
        SvcRequester.__init__(self, env, svcName, log)
        self.svcRequesters = svcRequesters
        if f is None:
            f = lambda x: x
        self.f = f
        self.cont = cont

    def _fgen(self, svcReq):
        """Generator used to submit the request to its associated server."""

        # Below, the inBlockingCall argument is False when the requests
        # run on separate servers.
        inBlockingCall = svcReq.inBlockingCall if self.cont else False

        svcReqs = [requester.makeSvcRequest(svcReq.inVal, inBlockingCall)
                   for requester in self.svcRequesters]
        if self.cont:
            server = svcReq.server if not None else svcReqs[0].server
            for req in svcReqs[1:]:
                req.server = server
        procs = [req.submit() for req in svcReqs]

        yield Condition(self.env, Condition.all_events, procs)

        outValls = [req.outVal for req in svcReqs]
        svcReq.complete(self.f(outValls))


class Fmap(SvcRequester):
    def __init__(self, env, svcName, baseRequester, fRequester, cont=False,
                 log=None):
        SvcRequester.__init__(self, env, svcName, log)
        self.baseRequester = baseRequester
        self.fRequester = fRequester
        self.cont = cont

    def _fgen(self, svcReq):
        baseReq = self.baseRequester.makeSvcRequest(svcReq.inVal,
                                                    svcReq.inBlockingCall)
        yield  baseReq.submit()
        newReq = self.fRequester(baseReq.outVal)
        if self.cont:
            newReq.server = svcReq.server
            newReq.inBlockingCall = svcReq.inBlockingCall
        yield  newReq.submit()
        svcReq.complete(newReq.outVal)
