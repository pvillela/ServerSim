"""
Represents a group of users or clients that submit service requests.
"""

import random
import math
from typing import Union, Sequence, Tuple, Optional, MutableSequence

from livestats import livestats
import simpy

from .randutil import prob_chooser
from . import SvcRequester, SvcRequest


class UserGroup(object):
    """Represents a set of identical users or clients that submit
    service requests.

    Each user repeatedly executes service requests randomly
    selected from the set of service requests specified for the group.

    Attributes:
        << See __init__ args >>
        << Additional attributes or modifications to __init__ args >>

        svcs (List[SvcRequester]): The first components of *weighted_svcs*.
    """

    INFINITY = 1e99

    def __init__(self, env, num_users, name, weighted_svcs, min_think_time,
                 max_think_time, quantiles=None, svc_req_log=None):
        # type: (simpy.Environment, Union[int, Sequence[Tuple[float, int]]], str, Sequence[Tuple[SvcRequester, float]], float, float, Optional[Sequence[float]], Optional[MutableSequence[Tuple[str, SvcRequest]]]) -> None
        """Initializer.

        Args:
            env: The Simpy Environment.
            num_users: Number of users in group.  This can be either a
                positive integer or a sequence of (float, int), where
                the floats are monotonically increasing.  In this case,
                the sequence represents a step function of time, where each pair
                represents a step whose range of *x* values extend from the
                first component of the pair (inclusive) to the first
                component of the next pair (exclusive), and whose *y* value
                is the second component of the pair.  The first pair in
                the sequence must have 0 as its first component.
                If the num_users argument is an int, it is transformed
                into the list [(0, num_users)].
            name: This user group's name.
            weighted_svcs: List of pairs of
                SvcRequester instances and positive numbers
                representing the different service request types issued by
                the users in the group and their weights.  The weights are
                the relative frequencies with which the service requesters
                will be executed (the weights do not need to add up to 1,
                as they are normalized by this class).
            min_think_time: The minimum think time between service
                requests from a user.  Think time will be uniformly
                distributed between min_think_time and max_think_time.
            max_think_time: The maximum think time between service
                requests from a user.  Think time will be uniformly
                distributed between min_think_time and max_think_time.
            quantiles: List of quantiles to be tallied.  It
                defaults to [0.5, 0.95, 0.99] if not provided.
            svc_req_log: If not None, a sequence where service requests will
                be logged.  Each log entry is a pair (name, svc_req), where
                name is this group's name and svc_req is the current
                service request generated by this group.
        """
        self.env = env
        if isinstance(num_users, int):
            num_users = [(0, num_users)]
        if not isinstance(num_users, list):
            raise TypeError(
                "Argument num_users must be a number or a list of pairs.")
        if not num_users[0][0] == 0:
            raise ValueError("Argument num_users first element must be a pair "
                             "with 0 as the first component.")
        self.num_users = num_users
        self._num_users_times = [p[0] for p in num_users][1:] + [self.INFINITY]
        self._num_users_values = [p[1] for p in num_users]
        self._max_users = max(self._num_users_values)
        self.name = name
        self.weighted_svcs = weighted_svcs
        self.svcs = [x[0] for x in weighted_svcs]
        self.min_think_time = min_think_time
        self.max_think_time = max_think_time
        if quantiles is None:
            quantiles = [0.5, 0.95, 0.99]
        self.quantiles = quantiles
        self.svc_req_log = svc_req_log

        self._pick_svc = prob_chooser(*weighted_svcs)
        
        # create Tally objects for response times: overall and by svcRequest
        self._tally_dict = {}  # map from svcRequest to tally
        for svc in self.svcs:
            self._tally_dict[svc] = livestats.LiveStats(quantiles)
        self._overall_tally = livestats.LiveStats(quantiles)  # overall tally
        self._tally_dict[None] = self._overall_tally

        # additional recordkeeping
        self._request_count_dict = {}
        for svc in self.svcs:
            self._request_count_dict[svc] = 0
        self._request_count_dict[None] = 0

    # THROTTLE_LIMIT = 100

    def _user(self, user_idx):
        """
        Process execution loop for user.
        """
        n_times = len(self._num_users_times)
        for i in range(n_times):
            next_break_time = self._num_users_times[i]
            num_active_users = self._num_users_values[i]
            while self.env.now < next_break_time:
                # user goes dormant if the throttle applies
                if user_idx >= num_active_users:
                    yield self.env.timeout(next_break_time - self.env.now)
                # user stays active otherwise
                else:
                    think_time = random.uniform(self.min_think_time,
                                                self.max_think_time)
                    yield self.env.timeout(think_time)
                    start_time = self.env.now
                    svc = self._pick_svc()
                    self._request_count_dict[svc] += 1
                    self._request_count_dict[None] += 1
                    svc_req = svc.make_svc_request(None)
                    if self.svc_req_log is not None:
                        self.svc_req_log.append((self.name, svc_req))
                    yield svc_req.submit()
                    response_time = self.env.now - start_time
                    self._overall_tally.add(response_time)
                    self._tally_dict[svc].add(response_time)

    def activate_users(self):
        """
        Create and activate the users.
        """
        for user_idx in range(self._max_users):
            self.env.process(self._user(user_idx))

    def avg_response_time(self, svc=None):
        # type: (Optional[SvcRequester]) -> float
        """ Average response time for a given service or
            aggregate across all service requests,

        Args:
            svc (serversim.SvcRequester): given service
                instance or None.

        Returns:
            float: Average response time for the given service
                if svc is not None.  Otherwise, the average response
                time across all service requests.
        """
        return self._tally_dict[svc].average

    def std_dev_response_time(self, svc=None):
        # type: (Optional[SvcRequester]) -> float
        """Standard deviation for a given service or aggregate across all
        services.
        """
        return math.sqrt(abs(self._tally_dict[svc].variance()))

    def max_response_time(self, svc=None):
        # type: (Optional[SvcRequester]) -> float
        """Maximum response time for a given service or
        aggregate across all service requests,

        Args:
            svc (serversim.SvcRequester): given service
                instance or None.

        Returns:
            float: Maximum response time for the given service
                if svc is not None.  Otherwise, the maximum response
                time across all service requests.
        """
        return self._tally_dict[svc].max_val

    def min_response_time(self, svc=None):
        # type: (Optional[SvcRequester]) -> float
        """Minimum response time for a given service or
        aggregate across all service requests,

        Args:
            svc (serversim.SvcRequester): given service
                instance or None.

        Returns:
            float: Minimum response time for the given service
                if svc is not None.  Otherwise, the minimum response
                time across all service requests.
        """
        return self._tally_dict[svc].min_val

    def response_time_quantiles(self, svc=None):
        # type: (Optional[SvcRequester]) -> Sequence[float]
        """Response time quantiles for a given service or
        aggregate across all service requests,

            The quantiles are as specified in the constructor or the
            defaults.

        Args:
            svc (serversim.SvcRequester): given service
                instance or None.

        Returns:
            float: Response time quantiles for the given service
                requester if svc is not None.  Otherwise, the response
                time quantiles aggregated across all service requests.
        """
        return self._tally_dict[svc].quantiles()

    def responded_request_count(self, svc=None):
        # type: (Optional[SvcRequester]) -> int
        """Number of requests submitted and responded to."""
        return self._tally_dict[svc].count

    def unresponded_request_count(self, svc=None):
        # type: (Optional[SvcRequester]) -> int
        """Number of requests submitted but not yet responded to."""
        return self._request_count_dict[svc] - self.responded_request_count(svc)

    def throughput(self, svc=None):
        # type: (Optional[SvcRequester]) -> float
        """Aggregate responded requests per unit of time."""
        return self.responded_request_count(svc) / self.env.now
