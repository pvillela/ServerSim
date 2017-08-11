"""
Extension of simpy.Resource to collect basic metrics.
"""

from typing import List, Optional, TYPE_CHECKING

import simpy
import simpy.resources.resource as simpyrr

if TYPE_CHECKING:
    from .service import SvcRequest


class MeasuredResource(simpy.Resource):
    """ A simpy.Resource that collects basic metrics.

    Attributes:
        << See __init__. >>
        << Additional attributes: >>

        releases: Number of requests that finished utilization of
            this resource.
        cum_queue_time: Cumulative queuing time for all requests.
        cum_service_time: Cumulative end-to-end time for all requests.
        svc_req_log (List[SvcRequest): Service request log.
        queue_length (int): Resource queue length.
        in_use_count (int): Number of requests actively using the resource
            (not waiting in queue).
    """
    
    def __init__(self, env, capacity):
        # type: (simpy.Environment, float) -> None
        """ Initializer.

        Args:
            env: SimPy Environment.
            capacity: The resource's capacity.
        """
        simpy.Resource.__init__(self, env, capacity)
        self.env = env  # type: simpy.Environment
        self.releases = 0  # type: int
        self.cum_queue_time = 0  # type: float
        self.cum_service_time = 0  # type: float
        self.queue_length = 0  # type: int
        self.in_use_count = 0  # type: int

    def request(self):
        # type: (Optional[SvcRequest]) -> simpyrr.Request
        """Overrides parent class method to support metrics."""

        submission_time = self.env.now
        self.queue_length += 1

        def cb(_evt):
            # type: (simpyrr.Request) -> None
            self.cum_queue_time += self.env.now - submission_time
            self.queue_length -= 1
            self.in_use_count += 1

        req = simpy.Resource.request(self)
        req.submission_time = submission_time  # ad-hoc attribute
        req.callbacks.append(cb)
        return req

    def release(self, req):
        # type: (simpyrr.Request) -> simpyrr.Release
        """Overrides parent class method to support metrics."""
        self.releases += 1
        self.in_use_count -= 1
        self.cum_service_time += self.env.now - req.__dict__["submission_time"]
        return simpy.Resource.release(self, req)
        
    @property
    def throughput(self):
        # type: () -> float
        """Returns the throughput of this resource up until now."""
        return self.releases / self.env.now
    
    @property
    def avg_queue_time(self):
        # type: () -> float
        """Returns the average queuing time per release."""
        return self.cum_queue_time / self.releases if self.releases != 0 else 0
    
    @property
    def avg_service_time(self):
        # type: () -> float
        """Returns the average service time per release."""
        return (self.cum_service_time / self.releases
                if self.releases != 0 else 0)
    
    @property
    def avg_use_time(self):
        # type: () -> float
        """Returns the average use time per release."""
        return self.avg_service_time - self.avg_queue_time

    @property
    def avg_queue_length(self):
        # type: () -> float
        """Average queue length.

        Returns the time-average length of queue of requests waiting to
        be granted by this resource, per resource releases, using Little's
        formula.
        """
        return self.throughput * self.avg_queue_time

    @property
    def utilization(self):
        # type: () -> float
        """Return the fraction of capacity used."""
        return ((self.cum_service_time - self.cum_queue_time)
                / (self.capacity * self.env.now))
