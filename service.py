"""
Classes representing computing services that are executed in servers.
"""

import logging
from simpy.events import Condition

debug = logging.debug


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
        name (str): Name of service requester.  Represents the type of
            service produced by the requester.
    """

    def __init__(self, env, name):
        self.env = env
        self.name = name
    
    def preSubmit(self, reqId=None, inBlockingCall=False, server=None):
        """ Returns a generator to create a service request and a
            its target server.

        Abstract method in base class.

        The returned generator can be used to produce a SimPy Process
        which will represent the service request.

        Args:
            reqId (any): Identifier for the service request instance.
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
            server (serversim.Service): The server targeted by the
                request.  The server is typically determined by the
                service requester using a load-balancer, a function
                that takes a service type and returns a server..

        Returns:
            (generator, serversim.Service)
        """
        raise NotImplementedError, "'SvcRequester' is an abstract class."
    
    def submit(self, reqId=None, inBlockingCall=False):
        """ Submit the request to its associated server, return the
            simpy process corresponding to the request.

        Args:
            inBlockingCall (bool): Indicates whether this request is
                in the scope of a blocking call.
        """
        debug("@@@@ " + self.name)
        gen = self.preSubmit(reqId, inBlockingCall)[0]
        return self.env.process(gen)


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
            type.
        nextReqId (int): next request id.  Incremented to create a
            unique request id for a service request if an explicit id
            is not provided to the submit method.
    """
    
    def __init__(self, env, name, compUnitsGen, loadBalancer):
        """Initializer."""
        SvcRequester.__init__(self, env, name)
        self.compUnitsGen = compUnitsGen
        self.loadBalancer = loadBalancer
        self.nextReqId = 1
    
    def _submit(self, server, reqId=None, inBlockingCall=False):
        """Generator used to submit the request to its associated server."""
        if reqId is None:
            reqId = self.nextReqId
            self.nextReqId += 1
        compUnits = self.compUnitsGen()
        
        # acquire a thread if not in a blocking call
        threadReq = None
        if not inBlockingCall:
            threadReq = server.threads.request()
            yield threadReq
        
        with server.request() as req:
            debug('Request submitted for %s-%s to server %s at %s for %s compute units' 
                % (self.name, reqId, server.name, self.env.now, compUnits))
            req.processDuration = \
                server.requestProcessDuration(compUnits)  # ad-hoc attribute
            yield req
        
            debug('Starting to execute request %s-%s at server %s at %s for %s compute units'
                % (self.name, reqId, server.name, self.env.now, compUnits))
            yield self.env.timeout(req.processDuration)
            debug('Completed executing request %s-%s at server %s at %s' \
                % (self.name, reqId, server.name, self.env.now))
       
        # release thread is appliccable
        if not inBlockingCall:
            server.threads.release(threadReq)
    
    def preSubmit(self, reqId=None, inBlockingCall=False, server=None):
        """See base class docstring"""
        if server is None:
            server = self.loadBalancer(self.name)
        return (self._submit(server, reqId, inBlockingCall), server)


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
        name = "Async(" + svcRequester.name + ")"
        SvcRequester.__init__(self, env, name)
        self.svcRequester = svcRequester
    
    def _submit(self, reqId=None):
        """Generator used to submit the request to its associated server."""
        self.svcRequester.submit(reqId, False)
        yield self.env.timeout(0)
    
    def preSubmit(self, reqId=None, inBlockingCall=False, server=None):
        """See base class docstring."""
        if server is not None:
            raise ValueError("server can't be set for this method in this class")
        return (self._submit(reqId), None)


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
        name = "Block(" + svcRequester.name + ")"
        SvcRequester.__init__(self, env, name)
        self.svcRequester = svcRequester
    
    def preSubmit(self, reqId=None, inBlockingCall=False, server=None):
        """See base class docstring."""
        if server is not None:
            raise ValueError("server can't be set for this method in this class")

        gen, server = self.svcRequester.preSubmit(None, True)

        def _submit():
            reqThread = server.threads.request()
            yield reqThread
            yield self.env.process(gen)
            server.threads.release(reqThread)
        
        return (_submit(), server)


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

    def __init__(self, env, name, caller, callees):
        """Initializer."""
        SvcRequester.__init__(self, env, name)
        self.caller = caller
        self.callees = callees
    
    def preSubmit(self, reqId=None, inBlockingCall=False, server=None):
        """See base class docstring."""
        gen, server = self.caller.preSubmit(None, inBlockingCall, server)
        gens = [callee.preSubmit(None, False)[0] for callee in self.callees]

        def _submit():
            """Generator used to submit the request to its associated server."""
            yield self.env.process(gen)
            for g in gens:
                yield self.env.process(g)
        
        return (_submit(), server)


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

    def __init__(self, env, name, caller, callees):
        """Initializer."""
        SvcRequester.__init__(self, env, name)
        self.caller = caller
        self.callees = callees
    
    def preSubmit(self, reqId=None, inBlockingCall=False, server=None):
        """See base class docstring."""
        gen, server = self.caller.preSubmit(None, inBlockingCall, server)
        gens = [callee.preSubmit(None, False)[0] for callee in self.callees]

        def _submit():
            """Generator used to submit the request to its associated server."""
            yield self.env.process(gen)
            yield Condition(self.env, Condition.all_events, gens)
        
        return (_submit(), server)


class Cont(SvcRequester):
    """ Combines two service requesters to yield a composit service
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
    
    def __init__(self, env, name, caller, cont):
        """Initializer."""
        SvcRequester.__init__(self, env, name)
        self.caller = caller
        self.cont = cont
    
    def preSubmit(self, reqId=None, inBlockingCall=False, server=None):
        """See base class docstring."""
        gen1, server = self.caller.preSubmit(None, inBlockingCall, server)
        gen2 = self.cont.preSubmit(None, inBlockingCall, server)[0]

        def _submit():
            """Generator used to submit the request to its associated server."""
            yield self.env.process(gen1)
            yield self.env.process(gen2)
        
        return (_submit(), server)
