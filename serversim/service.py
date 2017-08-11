"""
Classes representing computing services that are executed on servers.
"""

from typing import Callable, Any, Iterator, Optional, List, Mapping, \
    Sequence, Tuple
import logging

import simpy
import simpy.events as simpye

from .server import Server


debug = logging.debug


class SvcRequest(object):
    """A request for execution of computation units on one or more servers.

    A service request submission is implemented as a SimPy Process.

    A service request can be a composite of sub-requests.
    However, that composition is not explicit in terms of
    composite service request object instances using a composite pattern.
    Such a composition is implemented through the *gen* attribute of the
    service request, which is a generator.  That generator can yield service
    request submissions for other service requests.

    By default, a service request is non-blocking, i.e., a thread is
    held on the target server only while the service request itself
    is executing; the thread is relinquished when the request
    finishes executing and it passes control to its sub-requests.

    Attributes:
        << See __init__ arguments. >>
        << Additional attributes: >>

        out_val (Any): Output value produced from in_val by the service
            execution.
        id (int): The unique numerical ID of this request.
        time_log (List[Tuple[str, float]]): List of tag-time pairs
            representing significant occurrences for this request.
        time_dict (Mapping[str, float]): Dictionary with contents of *time_log*,
            for easier access to information.
    """
    def __init__(self, env, parent, svc_name, gen, server, in_val,
                 in_blocking_call=False):
        # type: (simpy.Environment, Optional[SvcRequest], str, Callable[[SvcRequest], Iterator[simpy.Event]], Optional[Server], Any, bool) -> None
        """Initializer.

        Args:
            env: The SimPy Environment.
            parent: The immediately containing service request, in case this
                is part of a composite service request.  None othersise.
            svc_name: Name of the service this request is associated with.
            gen: Generator which defines the behavior of this request.  The
                generator produces an iterator which yields simpy.Event
                instances.  The submit() method wratps the iterator in a
                simpy.Process object to schedule the request for execution
                by SimPy..
            server: The target server.  May be None for composite service
                requests, i.e., those not produced by CoreSvcRequester.
            in_val: Optional input value of the request.
            in_blocking_call: Indicates whether this request is
                in the scope of a blocking call.  When this parameter
                is true, the service request will hold a software
                thread on the target server while the service
                request itself and any of its sub-requests (calls
                to other servers) are executing.  Otherwise, the
                call is non-blocking, so a thread is held on the
                target server only while the service request itself
                is executing; the thread is relinquished when
                this request finishes executing and it passes control
                to its sub-requests.
        """
        self._env = env
        self.parent = parent
        self.svc_name = svc_name
        self.gen = gen
        self.server = server
        self.in_blocking_call = in_blocking_call
        self.in_val = in_val
        self.out_val = None
        self.id = id(self)
        self._is_completed = False
        self.time_log = list()
        self.time_dict = dict()

    @property
    def env(self):
        # type: () -> simpy.Environment
        return self._env

    @property
    def is_completed(self):
        # type: () -> bool
        return self._is_completed

    def submit(self):
        # type: () -> simpy.Process
        """Submit the request, return the simpy process corresponding to
        the request.
        """
        debug("@@@@ " + self.svc_name)
        self.log_time("submitted")
        return self._env.process(self.gen(self))

    def complete(self, val):
        # type: (Any) -> None
        """Complete the request with value val."""
        assert not self.is_completed, "Calling complete method on a " \
                                      "completed request."
        self._is_completed = True
        self.out_val = val
        self.log_time("completed")

    def log_time(self, label):
        # type: (str) -> None
        """Log the current time with the given label."""
        now = self._env.now
        self.time_log.append((label, now))
        self.time_dict[label] = now

    @property
    def process_time(self):
        # type: () -> Optional[float]
        """The time it took to process this request on its target server."""
        k1 = "hw_thread_acquired"
        k2 = "hw_thread_released"
        if k1 in self.time_dict and k2 in self.time_dict:
            return self.time_dict[k2] - self.time_dict[k1]
        else:
            return None

    @property
    def hw_queue_time(self):
        # type: () -> Optional[float]
        """The time this request waited in the hardware thread queue."""
        k1 = "hw_thread_requested"
        k2 = "hw_thread_acquired"
        if k1 in self.time_dict and k2 in self.time_dict:
            return self.time_dict[k2] - self.time_dict[k1]
        else:
            return None

    @property
    def sw_queue_time(self):
        # type: () -> Optional[float]
        """The time this request waited in the software thread queue."""
        k1 = "hw_thread_requested"
        k2 = "hw_thread_acquired"
        if k1 in self.time_dict and k2 in self.time_dict:
            return self.time_dict[k2] - self.time_dict[k1]
        else:
            return None

    @property
    def service_time(self):
        # type: () -> Optional[float]
        """The time it took to complete this request end-to-end."""
        k1 = "submitted"
        k2 = "completed"
        if k1 in self.time_dict and k2 in self.time_dict:
            return self.time_dict[k2] - self.time_dict[k1]
        else:
            return None


class SvcRequester(object):
    """Base class of service requesters.

    A service requester represents a service.  In this framework,
    a service requester is a factory for service requests.

    A service requester can be a composite of sub-requesters, thus
    representing a composite service.

    Attributes:
        << See __init__ args below. >>
    """

    def __init__(self, env, svc_name, log=None):
        # type: (simpy.Environment, str, Optional[List[Tuple[str, SvcRequest]]]) -> None
        """Initializer.

        Args:
            env: The SimPy Environment.
            svc_name: Name of the service.
            log: Optional list to collect all service request objects
                produced by this service requester.
        """
        self.env = env
        self.svc_name = svc_name
        self.log = log

    def __repr__(self):
        """Printable representation of this object."""
        return type(self).__name__ + repr(self.__dict__)

    def _gen(self, svc_req):
        # type: (SvcRequest) -> Iterator[simpy.Event]
        """Generator that will be part of each produced service request.

        See also documentation for SvcRequest.

        Args:
            svc_req (serversim.SvcRequest): A service request produced by
                this factory.
        """
        raise NotImplementedError("'SvcRequester' is an abstract class.")

    def _add_to_log(self, svc_req):
        # type: (SvcRequest) -> None
        """Add a service request to the service request log."""
        if self.log is not None:
            self.log.append((self.svc_name, svc_req))

    def make_svc_request(self, parent, in_val=None, in_blocking_call=False):
        # type: (Optional[SvcRequest], Any, bool) -> SvcRequest
        """ Produce a SvcRequest object.

        Default implementation, can be overridden.

        Args:
            parent: The parent service request of the produced service
                request if it is part of a composite service request,
                None otherwise.
            in_val: Sets this as the input value of produced service request.
            in_blocking_call: Sets this as the in_blocking_call attribute
                of the produced service request.

        Returns:
            A service request.
        """
        res = SvcRequest(self.env, parent, self.svc_name, self._gen, None,
                         in_val, in_blocking_call)
        self._add_to_log(res)
        return res


class CoreSvcRequester(SvcRequester):
    """Core srvice requester implementation.

    Typical service requesters are instances of this class or
    composites of such instances.  See the various service
    request combinators in this module.

    Attributes:
        << See __init__. >>
    """
    
    def __init__(self, env, svc_name, fcompunits, fserver, log=None,
                 f=None):
        # type: (simpy.Environment, str, Callable[[], float], Callable[[str], Server], Optional[List[SvcRequest]], Callable[[Any], Any]) -> None
        """Initializer.

        Args:
            env: See base class.
            svc_name: See base class.
            fcompunits: A (possibly randodm) function that
                generates the number of compute units required to execute a
                service request instance produced by this object.
            fserver: Function that produces a server (possibly round-robin,
                random, or based on server load information) when given a
                service request name.  Models a load-balancer.
            log: See base class.
            f: An optional function that is applied to a service request's
                in_val to produce its out_val.  If f is None, the constant
                function that always returns None is used.
        """
        SvcRequester.__init__(self, env, svc_name, log)
        self.fcompunits = fcompunits
        self.fserver = fserver
        if f is None:
            def f(_x): return None
        self.f = f

    def _gen(self, svc_req):
        # type: (SvcRequest) -> Iterator[simpy.Event]
        """Generator that will be part of each produced service request.

        See base class.
        """
        server = svc_req.server
        in_blocking_call = svc_req.in_blocking_call
        req_id = svc_req.id
        in_val = svc_req.in_val

        comp_units = self.fcompunits()
        svc_req.compUnits = comp_units  # ad-hoc attribute
        
        # acquire a thread if not in a blocking call
        thread_req = None
        if not in_blocking_call:
            svc_req.log_time("sw_thread_requested")
            thread_req = server.thread_request(svc_req)
            yield thread_req
            svc_req.log_time("sw_thread_acquired")

        hw_req = server.hw_request(svc_req)
        debug('Request for %s-%s to server %s at %s for %s compute units'
              % (self.svc_name, req_id, server.name, self.env.now, comp_units))
        hw_req.process_duration = \
            server.process_duration(comp_units)  # ad-hoc attribute
        svc_req.log_time("hw_thread_requested")
        yield hw_req
        svc_req.log_time("hw_thread_acquired")

        debug('Starting to execute request %s-%s at server %s at %s for %s '
              'compute units'
              % (self.svc_name, req_id, server.name, self.env.now, comp_units))
        yield self.env.timeout(hw_req.process_duration)
        server.hw_release(hw_req)
        svc_req.log_time("hw_thread_released")
        debug('Completed executing request %s-%s at server %s at %s'
              % (self.svc_name, req_id, server.name, self.env.now))

        svc_req.complete(self.f(in_val))

        # release thread is appliccable
        if not in_blocking_call:
            server.thread_release(thread_req)
            svc_req.log_time("sw_thread_released")

    def make_svc_request(self, parent, in_val=None, in_blocking_call=False):
        # type: (Optional[SvcRequest], Any, bool) -> SvcRequest
        """Overrides default implementation in base class.

        See base class docstring
        """
        server = self.fserver(self.svc_name)
        res = super(CoreSvcRequester, self).make_svc_request(parent, in_val,
                                                             in_blocking_call)
        res.server = server
        return res


class Async(SvcRequester):
    """Wraps a service requester to produce asynchronous service requests.

    An asynchronous service request completes and returns immediately
    to the head_requester, while the underlying (wrapped) service request is
    scheduled for execution on its target server.

    Attributes:
        << See __init__. >>
    """
    
    def __init__(self, env, svc_requester, log=None):
        # type: (simpy.Environment, SvcRequester, Optional[List[SvcRequest]]) -> None
        """Initializer.

        Args:
            env: See base class.
            svc_requester: The underlying service requester that is wrapped
                by this one.
            log: See base class.
        """
        svc_name = "Async(" + svc_requester.svc_name + ")"
        SvcRequester.__init__(self, env, svc_name, log)
        self.svc_requester = svc_requester

    def _gen(self, svc_req):
        # type: (SvcRequest) -> Iterator[simpy.Event]
        """Generator that will be part of each produced service request.

        See base class.
        """
        enclosed_svc_req = self.svc_requester.make_svc_request(
            None, svc_req.in_val, False)
        enclosed_svc_req.submit()
        svc_req.complete(None)
        yield self.env.timeout(0)


class Blkg(SvcRequester):
    """Wraps a service requester to produce blocking service requests.

    A blocking service request will hold a software thread on the
    target server until the service request itself and all of its
    non-asynchronous sub-requests complete.

    Attributes:
        << See __init__. >>
    """

    def __init__(self, env, svc_requester, log=None):
        # type: (simpy.Environment, SvcRequester, Optional[List[Tuple[str, SvcRequest]]]) -> None
        """Initializer.

        Args:
            env: See base class.
            svc_requester: The underlying service requester that is wrapped
                by this one.
            log: See base class.
        """
        svc_name = "Blkg(" + svc_requester.svc_name + ")"
        SvcRequester.__init__(self, env, svc_name, log)
        self.svc_requester = svc_requester

    def _gen(self, svc_req):
        # type: (SvcRequest) -> Iterator[simpy.Event]
        """Generator that will be part of each produced service request.

        See base class.
        """
        enclosed_svc_req = svc_req.__dict__["enclosed_svc_req"]
        enclosed_svc_req.server = svc_req.server
        req_thread = None
        if not svc_req.in_blocking_call:
            assert enclosed_svc_req.server is not None, \
                "Blkg at top level may only wrap a SvcRequest " \
                "with a non-null server."
            req_thread = enclosed_svc_req.server.thread_request(svc_req)
            svc_req.log_time("sw_thread_requested")
            yield req_thread
            svc_req.log_time("sw_thread_acquired")
        yield enclosed_svc_req.submit()
        if not svc_req.in_blocking_call:
            enclosed_svc_req.server.thread_release(req_thread)
            svc_req.log_time("sw_thread_released")
        svc_req.complete(enclosed_svc_req.out_val)

    def make_svc_request(self, parent, in_val=None, in_blocking_call=False):
        # type: (Optional[SvcRequest], Any, bool) -> SvcRequest
        """Overrides default implementation in base class.

        See base class docstring
        """
        svc_req = super(Blkg, self).make_svc_request(parent, in_val,
                                                     in_blocking_call)
        enclosed_svc_req = self.svc_requester.make_svc_request(
            svc_req, in_val, in_blocking_call)
        svc_req.server = enclosed_svc_req.server
        svc_req.enclosed_svc_req = enclosed_svc_req  # ad-hoc attribute
        return svc_req


class Seq(SvcRequester):
    """Combines a non-empty list of service requesters to yield a
    sequential composite service requester.

    This composite service requester produces composite service
    requests.  A composite service request produced by this service
    requester consists of a service request from each of the
    provided service requesters.  Each of the service requests is
    submitted in sequence, i.e., each service request is
    submitted when the previous one completes.

    Attributes:
        << See __init__. >>
        << Modified as follows: >>

        head_requester: The head of the __init__ parameter svc_requesters.
        tail_requesters: The tail of the __init__ parameter svc_requesters.

        << Note: svc_requesters is not an attribute. >>
    """

    def __init__(self, env, svc_name, svc_requesters, cont=False, log=None):
        # type: (simpy.Environment, str, Sequence[SvcRequester], bool, Optional[List[SvcRequest]]) -> None
        """Initializer.

        Args:
            env: See base class.
            svc_name: See base class.
            svc_requesters: See class docstring.
            cont: If true, the sequence executes as continuations
                of the first request, all on the same server.  Otherwise,
                each request can execute on a different server.
            log: See base class.
        """
        assert len(svc_requesters) > 0, "List of service requesters " \
            "must be non-empty"
        SvcRequester.__init__(self, env, svc_name, log)
        head_requester = svc_requesters[0]
        tail_requesters = svc_requesters[1:]
        self.head_requester = head_requester
        self.tail_requesters = tail_requesters
        self.cont = cont

    def _gen(self, svc_req):
        # type: (SvcRequest) -> Iterator[simpy.Event]
        """Generator that will be part of each produced service request.

        See base class.
        """
        head_svc_req = svc_req.__dict__["head_svc_req"]
        head_svc_req.server = svc_req.server
        yield head_svc_req.submit()

        val = head_svc_req.out_val

        # Below, the in_blocking_call argument is False when the requests
        # produced by tail_requesters are separate service requests,
        # not continuations of previous requests on the same server.
        others_in_blocking_call = \
            svc_req.in_blocking_call if self.cont else False

        for requester in self.tail_requesters:
            request = requester.make_svc_request(svc_req, val,
                                                 others_in_blocking_call)
            if self.cont:
                request.server = svc_req.server
            yield request.submit()
            val = request.out_val

        svc_req.complete(val)

    def make_svc_request(self, parent, in_val=None, in_blocking_call=False):
        # type: (Optional[SvcRequest], Any, bool) -> SvcRequest
        """Overrides default implementation in base class.

        See base class docstring
        """
        svc_req = super(Seq, self).make_svc_request(parent, in_val,
                                                    in_blocking_call)
        head_svc_req = self.head_requester.make_svc_request(
            svc_req, in_val, in_blocking_call)
        svc_req.server = head_svc_req.server
        svc_req.head_svc_req = head_svc_req  # ad-hoc attribute
        return svc_req


class Par(SvcRequester):
    """Combines a non-empty list of service requesters to yield a
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
        << See __init__. >>
    """

    def __init__(self, env, svc_name, svc_requesters, f=None, cont=False,
                 log=None):
        # type: (simpy.Environment, str, Sequence[SvcRequester], Callable[[Any], Any], bool, Optional[List[SvcRequest]]) -> None
        """Initializer.

        Args:
            env: See base class.
            svc_name: See base class.
            svc_requesters: See class docstring.
            f: Optional function that takes the outputs of all the component
                service requests and produces the overall output
                for the composite.  If None then the constant function
                that always produces None is used.
            cont: If true, all the requests execute on the same server.
                Otherwise, each request can execute on a different server.
                When cont is True, the server is the container service
                request's server if not None, otherwise the server is
                picked from the first service request in the list of
                generated service requests.
            log: See base class.
        """
        assert len(svc_requesters) > 0, "List of service requesters " \
                                        "must be non-empty"
        SvcRequester.__init__(self, env, svc_name, log)
        self.svc_requesters = svc_requesters
        if f is None:
            def f(_x): return None
        self.f = f
        self.cont = cont

    def _gen(self, svc_req):
        # type: (SvcRequest) -> Iterator[simpy.Event]
        """Generator that will be part of each produced service request.

        See base class.
        """

        # With parallel calls, in_blocking_call is always False.
        svc_reqs = [requester.make_svc_request(svc_req, svc_req.in_val, False)
                    for requester in self.svc_requesters]
        if self.cont:
            server = svc_req.server if not None else svc_reqs[0].server
            for req in svc_reqs:  # may need to reassign even for svc_reqs[0]
                req.server = server
        procs = [req.submit() for req in svc_reqs]

        yield simpye.Condition(self.env, simpye.Condition.all_events, procs)

        out_vals = [req.out_val for req in svc_reqs]
        svc_req.complete(self.f(out_vals))


class Fmap(SvcRequester):
    """
    FlatMap combinator for service requesters.
    """
    def __init__(self, env, svc_name, base_requester, frequester, cont=False,
                 log=None):
        SvcRequester.__init__(self, env, svc_name, log)
        self.base_requester = base_requester
        self.frequester = frequester
        self.cont = cont

    def _gen(self, svc_req):
        # type: (SvcRequest) -> Iterator[simpy.Event]
        """Generator that will be part of each produced service request.

        See base class.
        """
        base_req = self.base_requester.make_svc_request(
            svc_req, svc_req.in_val, svc_req.in_blocking_call)
        yield base_req.submit()
        new_req = self.frequester(base_req.outVal)
        if self.cont:
            new_req.server = svc_req.server
            new_req.inBlockingCall = svc_req.in_blocking_call
        yield new_req.submit()
        svc_req.complete(new_req.outVal)
