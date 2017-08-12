"""
Classes representing computer servers.
"""

from typing import TYPE_CHECKING, Optional, List, Tuple

import simpy
import simpy.resources.resource as simpyrr

from .measuredresource import MeasuredResource

if TYPE_CHECKING:
    from .service import SvcRequest


class Server(object):
    """Represents a server.
    
    A server can take a finite number of connections and
    support arbitrary service request types.
    
    Attributes:
        << See __init__. >>
    """
    
    def __init__(self, env, max_concurrency, num_threads, speed, name,
                 hw_svc_req_log=None, sw_svc_req_log=None):
        # type: (simpy.Environment, int, int, float, str, Optional[List[Tuple[str, str, SvcRequest]]], Optional[List[Tuple[str, str, SvcRequest]]]) -> None
        """Initializer.

        Args:
            env: SimPy Environment
            max_concurrency: The maximum of _hardware threads for the server.
            num_threads: The maximum number of software threads for the server.
            speed: Aggregate server speed across all _hardware threads.
            name: The server's name.
            hw_svc_req_log: If not None, a list where hardware
                service requests will be logged.  Each log entry is a
                triple ("hw", name, svc_req), where name is this server's
                name and svc_req is the current service request asking for
                hardware resources.
            sw_svc_req_log: If not None, a list where software thread
                service requests will be logged.  Each log entry is a
                triple ("sw", name, svc_req), where name is this server's
                name and svc_req is the current service request asking for a
                software thread.
        """
        self.env = env
        self.max_concurrency = max_concurrency
        self.num_threads = num_threads
        self.speed = speed  # aggregate server speed across all hardware threads
        self.name = name
        self.hw_svc_req_log = hw_svc_req_log
        self.sw_svc_req_log = sw_svc_req_log
        self._hardware = MeasuredResource(env, max_concurrency)
        self._threads = MeasuredResource(env, num_threads)

    def process_duration(self, comp_units):
        # type: (float) -> float
        """The time required to process a request of comp_units compute units.
        """
        return comp_units / (self.speed / self.max_concurrency)

    def hw_request(self, svc_req=None):
        # type: (Optional[SvcRequest]) -> simpyrr.Request
        """Request a hardware thread for svc_req."""
        if self.hw_svc_req_log is not None and svc_req is not None:
            self.hw_svc_req_log.append(("hw", self.name, svc_req))
        return self._hardware.request()

    def hw_release(self, req):
        # type: (simpyrr.Request) -> simpyrr.Release
        """Release the hardware thread request req."""
        return self._hardware.release(req)

    def thread_request(self, svc_req=None):
        # type: (Optional[SvcRequest]) -> simpyrr.Request
        """Request a software thread for svc_req."""
        if self.sw_svc_req_log is not None and svc_req is not None:
            self.sw_svc_req_log.append(("sw", self.name, svc_req))
        return self._threads.request()

    def thread_release(self, req):
        # type: (simpyrr.Request) -> simpyrr.Release
        """Release the software thread request req."""
        return self._threads.release(req)

    @property
    def svc_req_log(self):
        # type: () -> Optional[List[SvcRequest]]
        """Return the hardware service request log."""
        return self.hw_svc_req_log

    @property
    def thread_req_log(self):
        # type: () -> Optional[List[SvcRequest]]
        """Return the software thread service request log."""
        return self.sw_svc_req_log

    @property
    def throughput(self):
        # type: () -> float
        """Returns the throughput of this resource up until now."""
        return self._hardware.throughput

    @property
    def avg_hw_queue_time(self):
        # type: () -> float
        """Returns the average queuing time per release."""
        return self._hardware.avg_queue_time

    @property
    def avg_process_time(self):
        # type: () -> float
        """Returns the average processing time per release."""
        return self._hardware.avg_use_time

    @property
    def avg_hw_queue_length(self):
        # type: () -> float
        """Average _hardware queue length.

        Returns the time-average length of queue of requests waiting to
        be granted by this resource, per resource releases, using Little's
        formula.
        """
        return self._hardware.avg_queue_length

    @property
    def hw_queue_length(self):
        # type: () -> float
        """Current number of HW requests in queue."""
        return self._hardware.queue_length

    @property
    def hw_in_process_count(self):
        # type: () -> int
        """Current number of HW requests in process."""
        return self._hardware.in_use_count

    @property
    def utilization(self):
        # type: () -> float
        """Return the fraction of capacity used."""
        return self._hardware.utilization

    @property
    def avg_thread_queue_time(self):
        # type: () -> float
        """The average thread queuing time per software thread release."""
        return self._threads.avg_queue_time

    @property
    def avg_thread_use_time(self):
        # type: () -> float
        """The average thread use time per software thread release."""
        return self._threads.avg_use_time

    @property
    def avg_service_time(self):
        # type: () -> float
        """The average thread service (wait + use) time per  software
        thread release.
        """
        return self._threads.avg_service_time

    @property
    def avg_thread_queue_length(self):
        # type: () -> float
        """The time-average length of the queue of requests to be
        granted a software thread,

        Based on number of thread releases, using Little's formula.
        """
        return self._threads.avg_queue_length

    @property
    def thread_queue_length(self):
        # type: () -> int
        """Current number of thread requests in queue."""
        return self._threads.queue_length

    @property
    def thread_in_use_count(self):
        # type: () -> int
        """Current number of requests using _threads."""
        return self._threads.in_use_count

    @property
    def thread_utilization(self):
        # type: () -> float
        """The fraction of thread capacity used."""
        return self._threads.utilization
