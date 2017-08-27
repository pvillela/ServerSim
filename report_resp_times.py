from typing import TYPE_CHECKING
from collections import OrderedDict, namedtuple

import matplotlib.pyplot as plt
import pandas as pd

if TYPE_CHECKING:
    from serversim import UserGroup


Minibatch = namedtuple("Result", ["ts", "counts", "means", "q_95"])


def minibatch_resp_times(time_resolution, grp):
    # type: (float, UserGroup) -> Minibatch

    times = ((svc_req.time_dict["submitted"] // time_resolution) *
             time_resolution
             for (_, svc_req) in grp.svc_req_log
             if svc_req.is_completed)

    vals = (svc_req.time_dict["completed"] - svc_req.time_dict["submitted"]
            for (_, svc_req) in grp.svc_req_log
            if svc_req.is_completed)

    series = pd.Series(vals, index=times)
    grouped = series.groupby(level=0)

    counts_ser = grouped.count()
    ts = counts_ser.index.values
    counts = counts_ser.values
    means = grouped.mean().values
    q_95 = grouped.quantile(.95).values

    return Minibatch(ts, counts, means, q_95)


def plot_counts_means_q95(minibatch1, minibatch2):
    # type: (Minibatch, Minibatch) -> None

    x = minibatch1.ts  # should be same as minibatch2.ts

    counts1 = minibatch1.counts
    counts2 = minibatch2.counts

    means1 = minibatch1.means
    means2 = minibatch2.means

    q1_95 = minibatch1.q_95
    q2_95 = minibatch2.q_95

    fig = plt.figure()

    # Plot counts
    axc = fig.add_axes([0, .97, .77, .77])
    axc.plot(x, counts1, color='b', label="Counts 1")
    axc.plot(x, counts2, color='r', label="Counts 2")
    axc.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)
    axc.set_xlabel("Time buckets")
    axc.set_ylabel("Throughput")

    # Plot response time averages and 95th percentiles
    axr = fig.add_axes([0, 0, .77, .77])
    axr.plot(x, means1, color='b', label="Means 1")
    axr.plot(x, q1_95, color='c', label="95th Percentile 1")
    axr.plot(x, means2, color='r', label="Means 2")
    axr.plot(x, q2_95, color='m', label="95th Percentile 2")
    axr.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)
    axr.set_xlabel("Time buckets")
    axr.set_ylabel("Response times")

    plt.show()

    
def compare_scenarios(sc1, sc2):
    grp1 = sc1.grp
    grp2 = sc2.grp

    minibatch1 = minibatch_resp_times(5, grp1)
    minibatch2 = minibatch_resp_times(5, grp2)

    plot_counts_means_q95(minibatch1, minibatch2)
