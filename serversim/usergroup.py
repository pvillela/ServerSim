"""
Class to represent a group of users or clients that submit service
execution requests.
"""

import random
import math

from livestats import livestats

from .randutil import probChooser


class UserGroup(object):
    """ Represents a set of identical users or clients that submit
        service execution requests.

    Each user can repeatedly execute service requests randomly
    selected from the set of service requests specified for the group.

    Attributes:
        env: Simpy Environment.
        numUsers (int): Number of users in group.
        name (str): This user group's name.
        weightedTxns (list[(any, Number)]): List of pairs of
            SvcRequestFactory instances and positive numbers
            representing the different service request types issued by
            the users in the group and their weights.   The weights are
            the relative frequencies with which the svcRequests will be
            executed (the weights do not need to add up to 1, as they
            are normalized by this class).
        minThinkTime (Number): The minimum think time between service
            requests.  Think time will be uniformly distributed between
            minThinkTime and maxThinkTime.
        maxThinkTime (Number): The maximum think time between service
            requests.  Think time will be uniformly distributed between
            minThinkTime and maxThinkTime.
        quantiles (list[float]): List of quantiles to be tallied.  It
            defaults to [0.5, 0.95, 0.99] if not provided.
    """
    
    def __init__(self, env, numUsers, name, weightedTxns, minThinkTime,
                 maxThinkTime, quantiles=None, throtleFunc=None):
        """Initializer."""
        self.env = env
        self.numUsers = numUsers
        self.name = name
        self.weightedTxns = weightedTxns
        self._txns = [x[0] for x in weightedTxns]
        self.minThinkTime = minThinkTime
        self.maxThinkTime = maxThinkTime
        if quantiles is None:
            quantiles = [0.5, 0.95, 0.99]
        self.quantiles = quantiles
        self.throttleFunc = throtleFunc

        self._pickSvcRequestFactory = probChooser(*weightedTxns)
        
        # create Tally objects for response times: overall and by svcRequest
        self._tallyDict = {}  # map from svcRequest to tally
        for txn in self._txns:
            self._tallyDict[txn] = livestats.LiveStats(quantiles)
        self._overallTally = livestats.LiveStats(quantiles)  # overall tally
        self._tallyDict[None] = self._overallTally

        # additional recordkeeping
        self._requestCountDict = {}
        for txn in self._txns:
            self._requestCountDict[txn] = 0
        self._requestCountDict[None] = 0

    THROTTLE_LIMIT = 100

    def _user(self, userIdx):
        """
        Process execution loop for user.
        """
        thf = self.throttleFunc
        while True:
            # user goes dormant if the throttle applies
            if thf is not None and thf(self.env.now) < userIdx:
                for t in range(1, self.THROTTLE_LIMIT):
                    if thf(self.env.now + t) >= userIdx: break
                yield self.env.timeout(t)
            # user stays active otherwise
            else:
                thinkTime = random.uniform(self.minThinkTime, self.maxThinkTime)
                yield self.env.timeout(thinkTime)
                startTime = self.env.now
                svcReqFactory = self._pickSvcRequestFactory()
                self._requestCountDict[svcReqFactory] += 1
                self._requestCountDict[None] += 1
                yield svcReqFactory.makeSvcRequest().submit()
                responseTime = self.env.now - startTime
                self._overallTally.add(responseTime)
                self._tallyDict[svcReqFactory].add(responseTime)

    def activateUsers(self):
        """
        Create and activate the specified number of users.
        """
        for userIdx in range(self.numUsers):
            self.env.process(self._user(userIdx))

    def avgResponseTime(self, txn=None):
        """ Average response time for a given service requester or
            aggregate across all service requests,

        Args:
            txn (serversim.SvcRequester): Given service requester
                instance or None.

        Returns:
            float: Average response time for the given service requester
                if txn is not None.  Otherwise, the average response
                time across all service requests.
        """
        return self._tallyDict[txn].average

    def stdDevResponseTime(self, txn=None):
        return math.sqrt(abs(self._tallyDict[txn].variance()))

    def maxResponseTime(self, txn=None):
        """ Maximum response time for a given service requester or
            aggregate across all service requests,

        Args:
            txn (serversim.SvcRequester): Given service requester
                instance or None.

        Returns:
            float: Maximum response time for the given service requester
                if txn is not None.  Otherwise, the maximum response
                time across all service requests.
        """
        return self._tallyDict[txn].max_val

    def minResponseTime(self, txn=None):
        """ Minimum response time for a given service requester or
            aggregate across all service requests,

        Args:
            txn (serversim.SvcRequester): Given service requester
                instance or None.

        Returns:
            float: Minimum response time for the given service requester
                if txn is not None.  Otherwise, the minimum response
                time across all service requests.
        """
        return self._tallyDict[txn].min_val

    def responseTimeQuantiles(self, txn=None):
        """ Response time quantiles for a given service requester or
            aggregate across all service requests,

            The quantiles are as specified in the constructor or the
            defaults.

        Args:
            txn (serversim.SvcRequester): Given service requester
                instance or None.

        Returns:
            float: Response time quantiles for the given service
                requester if txn is not None.  Otherwise, the response
                time quantiles aggregated across all service requests.
        """
        return self._tallyDict[txn].quantiles()

    def respondedRequestCount(self, txn=None):
        """Number of requests submitted and responded to."""
        return self._tallyDict[txn].num()

    def unrespondedRequestCount(self, txn=None):
        """Number of requests submitted but not yet responded to."""
        return self._requestCountDict[txn] - self.respondedRequestCount(txn)

    def throughput(self, txn=None):
        return self.respondedRequestCount(txn) / self.env.now
