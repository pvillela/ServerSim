import random
from util import probChooser
from livestats import livestats


class UserGroup(object):
    """
    Represents a set of identical user objects.  Each user object can
    repeatedly execute service requests randomly selected from the set of
    service requests specified for the group.
    """
    
    def __init__(self, env, numUsers, name, weightedTxns, minThinkTime, maxThinkTime):
        """
        Initializes the instance.
        
        @env: Simpy Environment
        @numUsers: number of users in group.
        @param name: this user group's name.
        @param weightedTxns: dictionary mapping SvcRequestFactory instances to positive numbers.
            The positive numbers are the relative frequencies with which the
            svcRequests will be executed (these frequencies do not need to
            add up to 1, as they will be normalized by this class).
        @param minThinkTime: the minimum think time between svcRequest
            invocations.  Think time will be uniformly distributed between
            minThinkTime and maxThinkTime.
        @param maxThinkTime: the maximum think time between svcRequest
            invocations.  Think time will be uniformly distributed between
            minThinkTime and maxThinkTime.
        """
        self.env = env
        self.numUsers = numUsers
        self.name = name
        self.weightedTxns = weightedTxns
        self.txns = [x[0] for x in weightedTxns]
        self.minThinkTime = minThinkTime
        self.maxThinkTime = maxThinkTime

        self.pickSvcRequestFactory = probChooser(weightedTxns)
        
        # create Tally objects for response times: overall and by svcRequest
        self.overallTally = livestats.LiveStats([0.5, 0.95, 0.99])  # overall tally
        self.tallyDict = {}  # map from svcRequest to tally
        for txn in self.txns:
            self.tallyDict[txn] = livestats.LiveStats([0.5, 0.95, 0.99])
    
    def _user(self):
        """
        Process execution loop for user.
        """
        while 1:
            thinkTime = \
                random.uniform(self.minThinkTime, self.maxThinkTime)
            yield self.env.timeout(thinkTime)
            startTime = self.env.now
            svcReqFactory = self.pickSvcRequestFactory()
            yield svcReqFactory.submit()
            responseTime = self.env.now - startTime
            self.overallTally.add(responseTime)
            self.tallyDict[svcReqFactory].add(responseTime)

    def activateUsers(self):
        """
        Create and activate the specified number of users.
        """
        for i in range(self.numUsers):
            self.env.process(self._user())
