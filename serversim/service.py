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

    #TODO: fix or remove this
    def flatMap(self, f, svcName="flatMap"):
        def fgen(_svcReq):
            yield  self.submit()

            # def __init__(self, env, svcName, fgen, server, inVal, inBlockingCall):

        res = SvcRequest(self._env, svcName, fgen, None, self.inVal, False)

        def cb(val):
            chainedReq = f(self)
            chainedReq.callbacks.append(res.complete)
            chainedReq.submit()

        self.callbacks.append(cb)

        return res


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
    to the caller, while the underlying (wrapped) service request is
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


class Block(SvcRequester):
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
        svcName = "Block(" + svcRequester.svcName + ")"
        SvcRequester.__init__(self, env, svcName)
        self.svcRequester = svcRequester

    def _fgen(self, svcReq):
        enclosedSvcReq = self.svcRequester.makeSvcRequest(svcReq.inVal, True)
        reqThread = None
        if not svcReq.inBlockingCall:
            reqThread = enclosedSvcReq.server.threads.request()
            yield reqThread
        yield enclosedSvcReq.submit()
        if not svcReq.inBlockingCall:
            enclosedSvcReq.server.threads.release(reqThread)
        svcReq.complete(enclosedSvcReq.outVal)


class CallSeq(SvcRequester):
    """ Combines a service requester and a list of service requesters
        to yield a sequential composite service requester.

    The composite service requester produces composite service
    requests.  A composite service request produced by this service
    requester consists of service request produced from the caller
    service requester and a service request from each of the
    service requesters in the callees list.  When the service request
    from the caller completes, it causes each of the callee service
    requests to be submitted in sequence, i.e., each sub-service is
    submitted when the prveious one completes.

    Attributes:
        caller (serversim.SvcRequester): See description in class
            docstring.
        callees (list[serversim.SvcRequester]): See description in class
            docstring.
    """

    def __init__(self, env, svcName, caller, callees):
        """Initializer."""
        SvcRequester.__init__(self, env, svcName)
        self.caller = caller
        self.callees = callees

    def _fgen(self, svcReq):
        """Generator used to submit the request to its associated server."""
        callerSvcReq = self.caller.makeSvcRequest(svcReq.inVal,
                                                  svcReq.inBlockingCall)
        yield callerSvcReq.submit()

        val = callerSvcReq.outVal
        for callee in self.callees:
            # The inBlockingCall argument is False because the callees are
            # separate service requests not a continuation of svcReq on
            # the same server
            calleeSvcReq = callee.makeSvcRequest(val, False)
            yield calleeSvcReq.submit()
            val = calleeSvcReq.outVal

        svcReq.complete(val)


class CallPar(SvcRequester):
    """ Combines a service requester and a list of service requesters
        to yield a parallel composite service requester.

    The composite service requester produces composite service
    requests.  A composite service request produced by this service
    requester consists of service request produced from the caller
    service requester and a service request from each of the
    service requesters in the callees list.  When the service request
    from the caller completes, it causes all of the callee service
    requests to be submitted immediately (in parallel).

    Attributes:
        caller (serversim.SvcRequester): See description in class
            docstring.
        callees (list[serversim.SvcRequester]): See description in class
            docstring.
    """

    def __init__(self, env, svcName, caller, callees, f=None):
        """Initializer."""
        SvcRequester.__init__(self, env, svcName)
        self.caller = caller
        self.callees = callees
        if f is None:
            f = lambda x: x
        self.f = f

    def _fgen(self, svcReq):
        """Generator used to submit the request to its associated server."""
        callerSvcReq = self.caller.makeSvcRequest(svcReq.inVal,
                                                  svcReq.inBlockingCall)
        yield callerSvcReq.submit()

        val = callerSvcReq.outVal

        # The inBlockingCall argument is False because the callees are
        # separate service requests not a continuation of svcReq on
        # the same server
        calleeSvcReqs = [callee.makeSvcRequest(val, False) for callee in
                         self.callees]

        calleeProcs = [sr.submit() for sr in calleeSvcReqs]
        yield Condition(self.env, Condition.all_events, calleeProcs)

        calleeOutVals = [sr.outVal for sr in calleeSvcReqs]
        svcReq.complete(self.f(calleeOutVals))


class Cont(SvcRequester):
    """ Combines two service requesters to yield a composite service
    requester that represents continuation of processing on the same
    target server.

    The composite service requester produces composite service
    requests.  A composite service request produced by this service
    requester consists of service request produced from the caller
    service requester and a service request from the cont service
    requester.  When the service request from the caller completes
    (possibly after triggering sequential or parallel sub-requests
    executing on other servers), it causes the cont service request to
    be submitted to the same target server as the caller request.

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
