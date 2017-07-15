"""
Extension of simpy.Resource to collect basic metrics.
"""

import simpy


class MeasuredResource(simpy.Resource):
    """ A simpy.Resource that collects basic metrics.

    Attributes:
        env: SimPy Environment.
        capacity: The resource's capacity.
        completions: Number of requests that completed utilization of this resource.
        cumQueueTime: Cumulative queuing time for all requests.
        cumServiceTime: Cumulative end-to-end time for all requests.
    """
    
    def __init__(self, env, capacity):
        """ Initializer."""
        simpy.Resource.__init__(self, env, capacity)
        self.env = env
        self.completions = 0
        self.cumQueueTime = 0
        self.cumServiceTime = 0
    
    def request(self):
        """Overrides parent class method to support metrics."""

        submissionTime = self.env.now

        def cb(evt):
            evt.resource.cumQueueTime += self.env.now - submissionTime
        
        req = simpy.Resource.request(self)
        req.submissionTime = submissionTime  # ad-hoc attribute
        req.callbacks.append(cb)
        return req
    
    def release(self, req):
        """Overrides parent class method to support metrics."""
        self.completions += 1
        self.cumServiceTime += self.env.now - req.submissionTime
        return simpy.Resource.release(self, req)
        
    @property
    def throughput(self):
        """Returns the throughput of this resource up until now."""
        return self.completions * 1.0 / self.env.now
    
    @property
    def avgQueueTime(self):
        """Returns the average queuing time per completion."""
        return self.cumQueueTime / self.completions
    
    @property
    def avgServiceTime(self):
        """Returns the average service time per completion."""
        return self.cumServiceTime / self.completions
    
    @property
    def avgUseTime(self):
        """Returns the average use time per completion."""
        return self.avgServiceTime - self.avgQueueTime

    @property
    def avgQueueLength(self):
        """Average queue length.

        Returns the time-average length of queue of requests waiting to
        be granted by this resource, for completed requests, using Little's
        formula.
        """
        return self.throughput * self.avgQueueTime

    @property
    def utilization(self):
        """Return the fraction of capacity used."""
        return (self.cumServiceTime - self.cumQueueTime) / (self.capacity * self.env.now)