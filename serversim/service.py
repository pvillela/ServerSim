"""
Classes representing computing services that are executed on servers.
"""

import logging
from simpy.events import Condition

debug = logging.debug


class SvcRequest(object):
    """Represents service requests to servers.

    Patterned after completable futures.
    """
    def __init__(self, env, svcName, fgen, server, inVal, inBlockingCall):
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
        self.timeStarted = None
        self.timeCompleted = None

    @property
    def env(self): return self._env

    @property
    def isCompleted(self): return self._isCompleted

    def submit(self):
        """ Submit the request to its associated server, return the
            simpy process corresponding to the request.

        Args:
            inBlockingCall (bool): Indicates whether this request is
                in the scope of a blocking call.
        """
        debug("@@@@ " + self.svcName)
        self.timeStarted = self._env.now
        return self._env.process(self.fgen(self))

    def complete(self, val):
        """Complete the future with value val."""
        assert not self.isCompleted, "Calling complete method on a completed future."
        self._isCompleted = True
        self.outVal = val
        self.timeCompleted = self.env.now
        for cb in self.callbacks:
            cb(val)

    def blocking(self):
        """ Creates a service request with blocking behavior based
            on this service request.

            Note: this method also mutates this object.
        """
        def fgen(svcReq):
            _blockingHelper(self, svcReq)

        svcName = "Blkg(" + self.svcName + ")"
        return SvcRequest(self.env, svcName, fgen, self.server, self.inVal,
                          False)

    def flatMap(self, f, svcName="flatMap"):
        def fgen(svcReq):
            yield  self.submit()
            newReq = f(self)
            yield  newReq.submit()
            svcReq.complete(newReq.outVal)

        return SvcRequest(self._env, svcName, fgen, None, self.inVal, False)


def _blockingHelper(enclosedSvcReq, svcReq):
    enclosedSvcReq.inBlockingCall = True
    reqThread = None
    if not svcReq.inBlockingCall:
        reqThread = enclosedSvcReq.server.threads.request()
        yield reqThread
    yield enclosedSvcReq.submit()
    if not svcReq.inBlockingCall:
        enclosedSvcReq.server.threads.release(reqThread)
    svcReq.complete(enclosedSvcReq.outVal)


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
        svcName (str): Name of service requester.  Represents the svcName of
            service produced by the requester.
    """

    def __init__(self, env, svcName):
        self.env = env
        self.svcName = svcName

    def _fgen(self, svcReq):
        """ Returns a generator used to submit the service request to its
            associated server.

        Args:
            svcReq (serversim.SvcRequest): A service request produced by
                this factory.
        """
        raise NotImplementedError, "'SvcRequester' is an abstract class."

    def makeSvcRequest(self, inVal=None, inBlockingCall=False):
        """ Produces a SvcRequest object.

        Default implementation, can be overridden.

        Args:
            inVal (any): input value of produced service request.
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

        Returns:
            (serversim.SvcRequest)
        """
        return SvcRequest(self.env, self.svcName, self._fgen, None, inVal,
                          inBlockingCall)


class CoreSvcRequester(SvcRequester):
    """Core srvice requester implementation.

    Typical service requesters are instances of this class or
    composites of such instances.  See the various service
    request combinators in this module.

    Attributes:
        compUnitsGen (() -> Number): Random function that generates
            the number of compute units required to execute a
            service request instance.
        loadBalancer ((str) -> serversim.Server): Function that
            produces a server (possibly round-robin, random, or based
            on server load information) when given a service request
            svcName.
    """
    
    def __init__(self, env, svcName, compUnitsGen, loadBalancer, f=None):
        """Initializer."""
        SvcRequester.__init__(self, env, svcName)
        self.compUnitsGen = compUnitsGen
        self.loadBalancer = loadBalancer
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
        
        # acquire a thread if not in a blocking call
        threadReq = None
        if not inBlockingCall:
            threadReq = server.threads.request()
            yield threadReq
        
        with server.request() as req:
            debug('Request for %s-%s to server %s at %s for %s compute units'
                  % (self.svcName, reqId, server.name, self.env.now, compUnits))
            req.processDuration = \
                server.requestProcessDuration(compUnits)  # ad-hoc attribute
            yield req
        
            debug('Starting to execute request %s-%s at server %s at %s for %s compute units'
                  % (self.svcName, reqId, server.name, self.env.now, compUnits))
            yield self.env.timeout(req.processDuration)
            debug('Completed executing request %s-%s at server %s at %s' \
                  % (self.svcName, reqId, server.name, self.env.now))

        svcReq.complete(self.f(inVal))

        # release thread is appliccable
        if not inBlockingCall:
            server.threads.release(threadReq)
    
    def makeSvcRequest(self, inVal=None, inBlockingCall=False):
        """Overrides default implementation in base class.

        See base class docstring
        """
        server = self.loadBalancer(self.svcName)
        return SvcRequest(self.env, self.svcName, self._fgen, server, inVal,
                          inBlockingCall)


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
    
    def __init__(self, env, svcRequester):
        """Initializer."""
        svcName = "Async(" + svcRequester.svcName + ")"
        SvcRequester.__init__(self, env, svcName)
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

    def __init__(self, env, svcRequester):
        """Initializer."""
        svcName = "Blkg(" + svcRequester.svcName + ")"
        SvcRequester.__init__(self, env, svcName)
        self.svcRequester = svcRequester

    def _fgen(self, svcReq):
        enclosedSvcReq = self.svcRequester.makeSvcRequest(svcReq.inVal, True)
        _blockingHelper(enclosedSvcReq, svcReq)


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
    """

    def __init__(self, env, svcName, svcRequesters):
        """Initializer."""
        assert len(svcRequesters) > 0, "List of service requesters " \
            "must be non-empty"
        SvcRequester.__init__(self, env, svcName)
        headRequester = svcRequesters[0]
        tailRequesters = svcRequesters[1:]
        self.headRequester = headRequester
        self.tailRequesters = tailRequesters

    def _fgen(self, svcReq):
        """Generator used to submit the request to its associated server."""
        headSvcReq = self.headRequester.makeSvcRequest(svcReq.inVal,
                                                         svcReq.inBlockingCall)
        yield headSvcReq.submit()

        val = headSvcReq.outVal
        for requester in self.tailRequesters:
            # The inBlockingCall argument is False because the requests
            # produced by tailRequesters are separate service requests,
            # not continuations of previous requests on the same server.
            request = requester.makeSvcRequest(val, False)
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

    Attributes:
        svcRequesters (list[serversim.SvcRequester]): See class
            docstring.
    """

    def __init__(self, env, svcName, svcRequesters, f=None):
        """Initializer."""
        assert len(svcRequesters) > 0, "List of service requesters " \
                                       "must be non-empty"
        SvcRequester.__init__(self, env, svcName)
        self.svcRequesters = svcRequesters
        if f is None:
            f = lambda x: x
        self.f = f

    def _fgen(self, svcReq):
        """Generator used to submit the request to its associated server."""
        # The inBlockingCall argument is False because the svcRequesters are
        # separate service requests not a continuation of svcReq on
        # the same server
        svcReqs = [requester.makeSvcRequest(svcReq.inVal, False)
                   for requester in self.svcRequesters]

        procs = [sr.submit() for sr in svcReqs]
        yield Condition(self.env, Condition.all_events, procs)

        calleeOutVals = [sr.outVal for sr in svcReqs]
        svcReq.complete(self.f(calleeOutVals))


class Cont(SvcRequester):
    """ Combines two service requesters to yield a composite service
    requester that represents continuation of processing on the same
    target server.

    The composite service requester produces composite service
    requests.  A composite service request produced by this service
    requester consists of service request produced from the headRequester
    service requester and a service request from the cont service
    requester.  When the service request from the headRequester completes
    (possibly after triggering sequential or parallel sub-requests
    executing on other servers), it causes the cont service request to
    be submitted to the same target server as the headRequester request.

    Attributes:
        caller (serversim.SvcRequester): See description in class
            docstring.
        cont (serversim.SvcRequester): See description in class
            docstring.
    """
    
    def __init__(self, env, svcName, caller, cont):
        """Initializer."""
        SvcRequester.__init__(self, env, svcName)
        self.caller = caller
        self.cont = cont
    
    def _fgen(self, svcReq):
        """Generator used to submit the request to its associated server."""
        callerSvcReq = self.caller.makeSvcRequest(svcReq.inVal,
                                                  svcReq.inBlockingCall)
        yield callerSvcReq.submit()

        contSvcReq = self.cont.makeSvcRequest(callerSvcReq.outVal,
                                              svcReq.inBlockingCall)
        contSvcReq.server = callerSvcReq.server
        yield contSvcReq.submit()
