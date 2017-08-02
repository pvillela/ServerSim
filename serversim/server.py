"""
Classes representing computer servers.
"""

from . import MeasuredResource


class Server(object):
    """
    Represents a server.  
    
    A server can take a finite number of connections and
    support arbitrary service request types.
    
    Attributes:
        env: SimPy Environment
        maxConcurrency: The maximum of _hardware threads for the server.
        numThreads: The maximum number of software threads for the server.
        _threads: Simpy Resource representing the server's software threads.
        speed: Aggregate server speed across all _hardware threads.
        name: The server's name.
    """
    
    def __init__(self, env, maxConcurrency, numThreads, speed, name):
        """Initializer."""
        self.env = env
        self.maxConcurrency = maxConcurrency
        self.numThreads = numThreads
        self.speed = speed  # aggregate server speed across all _hardware _threads
        self.name = name
        self._hardware = MeasuredResource(env, maxConcurrency)
        self._threads = MeasuredResource(env, numThreads)

    def processDuration(self, compUnits):
        """
        The time required to process a request of compUnits compute units.
        """
        return compUnits / (self.speed / self.maxConcurrency)

    def hwRequest(self, svcReq=None):
        return self._hardware.request(svcReq)

    def hwRelease(self, req):
        return self._hardware.release(req)

    def threadRequest(self, svcReq=None):
        return self._threads.request(svcReq)

    def threadRelease(self, req):
        return self._threads.release(req)

    @property
    def svcReqLog(self):
        return self._hardware.svcReqLog

    @property
    def threadReqLog(self):
        return self._threads.svcReqLog

    @property
    def throughput(self):
        """Returns the throughput of this resource up until now."""
        return self._hardware.throughput

    @property
    def avgHwQueueTime(self):
        """Returns the average queuing time per release."""
        return self._hardware.avgQueueTime

    @property
    def avgProcessTime(self):
        """Returns the average processing time per release."""
        return self._hardware.avgUseTime

    @property
    def avgHwQueueLength(self):
        """Average _hardware queue length.

        Returns the time-average length of queue of requests waiting to
        be granted by this resource, per resource releases, using Little's
        formula.
        """
        return self._hardware.avgQueueLength

    @property
    def hwQueueLength(self):
        """Current number of HW requests in queue."""
        return self._hardware.queueLength

    @property
    def hwInProcessCount(self):
        """Current number of HW requests in process."""
        return self._hardware.inUseCount

    @property
    def utilization(self):
        """Return the fraction of capacity used."""
        return self._hardware.utilization

    @property
    def avgThreadQueueTime(self):
        """The average thread queuing time per software thread release."""
        return self._threads.avgQueueTime

    @property
    def avgThreadUseTime(self):
        """The average thread use time per software thread release."""
        return self._threads.avgUseTime

    @property
    def avgServiceTime(self):
        """ The average thread service (wait + use) time per  software
            thread release.

            Shadows the property from base class.
        """
        return self._threads.avgServiceTime

    @property
    def avgThreadQueueLength(self):
        """ The time-average length of the queue of requests to be
            granted a software thread,

        Based on number of thread releases, using Little's formula.
        """
        return self._threads.avgQueueLength

    @property
    def threadQueueLength(self):
        """Current number of thread requests in queue."""
        return self._threads.queueLength

    @property
    def threadInUseCount(self):
        """Current number of requests using threads."""
        return self._threads.inUseCount

    @property
    def threadUtilization(self):
        """The fraction of thread capacity used."""
        return self._threads.utilization
