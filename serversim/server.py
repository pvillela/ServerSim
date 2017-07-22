"""
Classes representing computer servers.
"""

from . import MeasuredResource


class Server(MeasuredResource):
    """
    Represents a server.  
    
    A server can take a finite number of connections and
    support arbitrary service request types.
    
    Attributes:
        env: SimPy Environment
        maxConcurrency: The maximum of hardware threads for the server.
        numThreads: The maximum number of software threads for the server.
        threads: Simpy Resource representing the server's software threads.
        speed: Aggregate server speed across all hardware threads.
        name: The server's name.
    """
    
    def __init__(self, env, maxConcurrency, numThreads, speed, name):
        """Initializer."""
        MeasuredResource.__init__(self, env, maxConcurrency)
        self.env = env
        self.maxConcurrency = maxConcurrency
        self.numThreads = numThreads
        self.threads = MeasuredResource(env, numThreads)
        self.speed = speed  # aggregate server speed across all hardware threads
        self.name = name
    
    def processDuration(self, compUnits):
        """
        The time required to process a request of compUnits compute units.
        """
        return compUnits / (self.speed / self.maxConcurrency)
    
    avgProcessTime = MeasuredResource.avgUseTime
    """Returns the average processing time per processed request."""
    
    @property
    def avgThreadQueueTime(self):
        """The average thread queuing time per software thread release."""
        return self.threads.avgQueueTime

    @property
    def avgThreadUseTime(self):
        """The average thread use time per software thread release."""
        return self.threads.avgUseTime

    @property
    def avgThreadServiceTime(self):
        """ The average thread service (wait + use) time per  software
            thread release.
        """
        return self.threads.avgServiceTime

    @property
    def avgThreadQueueLength(self):
        """ The time-average length of the queue of requests to be
            granted a software thread,

        Based on number of thread releases, using Little's formula.
        """
        return self.threads.avgQueueLength

    @property
    def threadUtilization(self):
        """The fraction of thread capacity used."""
        return self.threads.utilization
