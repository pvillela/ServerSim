from measuredresource import MeasuredResource


class Server(MeasuredResource):
    """
    Represents a server.  A server can take a finite number of connections and
    support arbitrary service request types.
    """
    
    def __init__(self, env, maxConcurrency, numThreads, speed, name):
        """
        Initializer.

        @env: SimPy Environment
        @param maxConcurrency: the maximum of hardware threads for the server.
        @param numThreads: the maximum number of software threads for the server.
        @param speed: number of compute units processed per second per 
            connection.
        @param name: the server's name
        """
        MeasuredResource.__init__(self, env, maxConcurrency)
        self.env = env
        self.maxConcurrency = maxConcurrency
        self.numThreads = numThreads
        self.threads = MeasuredResource(env, numThreads)
        self.speed = speed  # aggregate server speed across all hardware threads
        self.name = name
    
    def requestProcessDuration(self, compUnits):
        """The time required to process a request wth compUnits."""
        return compUnits / (self.speed / self.maxConcurrency)
    
    avgProcessTime = MeasuredResource.avgUseTime
    """
    Returns the average processing time per completion.
    """
    
    def avgThreadQueueTime(self):
        """
        Returns the average thread queuing time per thread completion.
        """
        return self.threads.avgQueueTime

    def avgThreadUseTime(self):
        """
        Returns the average use thread time per thread completion.
        """
        return self.threads.avgUseTime

    def avgThreadServiceTime(self):
        """
        Returns the average thread service time per thread completion.
        """
        return self.threads.avgServiceTime

    def avgThreadQueueLength(self):
        """
        Returns the time-average length of queue of requests waiting to
        be granted a thread, for completed thread requests, using Little's
        formula.
        """
        return self.threads.avgQueueLength

    def threadUtilization(self):
        """
        Return the fraction of thread capacity used.
        """
        return self.threads.utilization
