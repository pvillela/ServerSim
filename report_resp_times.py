from typing import TYPE_CHECKING, Sequence, Tuple
from collections import OrderedDict

import matplotlib.pyplot as plt
import pandas as pd

if TYPE_CHECKING:
    from serversim import UserGroup


def minibatch_resp_times(time_resolution, grp):
    # type: (float, UserGroup) -> Tuple[Sequence[float], Sequence[float], Sequence[float], Sequence[float], Sequence[float], Sequence[float]]

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
    q_50 = grouped.quantile(.50).values
    q_95 = grouped.quantile(.95).values
    q_99 = grouped.quantile(.99).values

    return ts, counts, means, q_50, q_95, q_99


def plot_counts_means_q95(quantiles1, quantiles2):

    x = quantiles1[0]  # should be same as quantiles2[0]

    counts1 = quantiles1[1]
    counts2 = quantiles2[1]

    means1 = quantiles1[2]
    means2 = quantiles2[2]

    q1_95 = quantiles1[4]
    q2_95 = quantiles2[4]

    # Plot counts
    plt.plot(x, counts1, color='b', label="Counts 1")
    plt.plot(x, counts2, color='r', label="Counts 2")
    plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)
    plt.xlabel("Time buckets")
    plt.ylabel("Throughput")
    plt.show()

    # Plot averages and 95th percentiles

    plt.plot(x, means1, color='b', label="Means 1")
    plt.plot(x, q1_95, color='c', label="95th Percentile 1")

    plt.plot(x, means2, color='r', label="Means 2")
    plt.plot(x, q2_95, color='m', label="95th Percentile 2")

    # Hack to avoid duplicated labels (https://stackoverflow.com/questions/13588920/stop-matplotlib-repeating-labels-in-legend)
    handles, labels = plt.gca().get_legend_handles_labels()
    by_label = OrderedDict(zip(labels, handles))
    plt.legend(by_label.values(), by_label.keys(), bbox_to_anchor=(1.05, 1),
               loc=2, borderaxespad=0.)

    plt.xlabel("Time buckets")
    plt.ylabel("Response times")

    plt.show()

    
def compare_scenarios(sc1, sc2):
    grp1 = sc1.grp
    grp2 = sc2.grp

    quantiles1 = minibatch_resp_times(5, grp1)
    quantiles2 = minibatch_resp_times(5, grp2)

    plot_counts_means_q95(quantiles1, quantiles2)
