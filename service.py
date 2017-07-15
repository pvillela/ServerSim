import logging
from simpy.events import Condition

debug = logging.debug

class SvcRequester(object):
    """
    Base class of union type of service requesters.
    """

    def __init__(self, env, name):
        self.env = env
        self.name = name
    
    def preSubmit(self, reqId=None, inBlockingCall=False, server=None):
        raise NotImplementedError, "'SvcRequester' is an abstract class."
    
    def submit(self, reqId=None, inBlockingCall=False):
        """
        Submit the request to its associated server, return the simpy process.
        """
        debug("@@@@ " + self.name)
        gen = self.preSubmit(reqId, inBlockingCall)[0]
        return self.env.process(gen)


class CoreSvcRequester(SvcRequester):
    """
    Factory for creation of service requests.
    """
    
    def __init__(self, env, name, compUnitsGen, loadBalancer):
        """
        Initializer.
        
        @env: SimPy Environment
        @param name: name of the kind of service request prodced by the 
            factory.
        @param compUnitsGen: random number generation function for the number
            of computation units required to execute a service request
            instance.
        """
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
        if server is None:
            server = self.loadBalancer(self.name)
        return (self._submit(server, reqId, inBlockingCall), server)


class Async(SvcRequester):
    
    def __init__(self, env, svcRequester):
        name = "Async(" + svcRequester.name + ")"
        SvcRequester.__init__(self, env, name)
        self.svcRequester = svcRequester
    
    def _submit(self, reqId=None):
        self.svcRequester.submit(reqId, False)
        yield self.env.timeout(0)
    
    def preSubmit(self, reqId=None, inBlockingCall=False, server=None):
        if server is not None:
            raise ValueError("server can't be set for this method in this class")
        return (self._submit(reqId), None)


class Block(SvcRequester):
    
    def __init__(self, env, svcRequester):
        name = "Block(" + svcRequester.name + ")"
        SvcRequester.__init__(self, env, name)
        self.svcRequester = svcRequester
    
    def preSubmit(self, reqId=None, inBlockingCall=False, server=None):
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
    
    def __init__(self, env, name, caller, callees):
        SvcRequester.__init__(self, env, name)
        self.caller = caller
        self.callees = callees
    
    def preSubmit(self, reqId=None, inBlockingCall=False, server=None):
        gen, server = self.caller.preSubmit(None, inBlockingCall, server)
        gens = [callee.preSubmit(None, False)[0] for callee in self.callees]

        def _submit():
            yield self.env.process(gen)
            for g in gens:
                yield self.env.process(g)
        
        return (_submit(), server)


class CallPar(SvcRequester):
    
    def __init__(self, env, name, caller, callees):
        SvcRequester.__init__(self, env, name)
        self.caller = caller
        self.callees = callees
    
    def preSubmit(self, reqId=None, inBlockingCall=False, server=None):
        gen, server = self.caller.preSubmit(None, inBlockingCall, server)
        gens = [callee.preSubmit(None, False)[0] for callee in self.callees]

        def _submit():
            yield self.env.process(gen)
            yield Condition(self.env, Condition.all_events, gens)
        
        return (_submit(), server)


class Cont(SvcRequester):
    
    def __init__(self, env, name, caller, cont):
        SvcRequester.__init__(self, env, name)
        self.caller = caller
        self.cont = cont
    
    def preSubmit(self, reqId=None, inBlockingCall=False, server=None):
        gen1, server = self.caller.preSubmit(None, inBlockingCall, server)
        gen2 = self.cont.preSubmit(None, inBlockingCall, server)[0]

        def _submit():
            yield self.env.process(gen1)
            yield self.env.process(gen2)
        
        return (_submit(), server)
