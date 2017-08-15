from typing import TYPE_CHECKING, Sequence, Tuple
import functools as ft
from collections import OrderedDict
import itertools as it

import matplotlib.pyplot as plt
import pandas as pd
from livestats import livestats

if TYPE_CHECKING:
    from serversim import UserGroup


def minibatch_resp_times(time_resolution, grp):
    # type: (float, UserGroup) -> Tuple[Sequence[float], Sequence[float], Sequence[float], Sequence[float], Sequence[float], Sequence[float]]

    xys = [(int(svc_req.time_dict["submitted"]),
            svc_req.time_dict["completed"] - svc_req.time_dict["submitted"])
           for (_, svc_req) in grp.svc_req_log
           if svc_req.is_completed]

    times, vals = it.izip(*xys)
    series = pd.Series(vals, index=times)
    grouped_vals = series.groupby(by=lambda x: int(x/time_resolution))

    xs = grouped_vals.groups.keys()
    xs.sort()

    counts = grouped_vals.count().values
    means = grouped_vals.mean().values
    q_50 = grouped_vals.quantile(.50).values
    q_95 = grouped_vals.quantile(.95).values
    q_99 = grouped_vals.quantile(.99).values

    return xs, counts, means, q_50, q_95, q_99


def minibatch_resp_times_without_pandas(time_resolution, grp):
    # type: (float, UserGroup) -> Tuple[Sequence[float], Sequence[float], Sequence[float], Sequence[float], Sequence[float], Sequence[float]]
    quantiles = [0.5, 0.95, 0.99]

    xys = [(int(svc_req.time_dict["submitted"]/time_resolution),
            svc_req.time_dict["completed"] - svc_req.time_dict["submitted"])
           for (_, svc_req) in grp.svc_req_log
           if svc_req.is_completed]

    def ffold(map_, p):
        x, y = p
        if x not in map_:
            map_[x] = livestats.LiveStats(quantiles)
        map_[x].add(y)
        return map_

    xlvs = ft.reduce(ffold, xys, dict())

    xs = xlvs.keys()
    xs.sort()

    counts = [xlvs[x].count for x in xs]
    means = [xlvs[x].average for x in xs]
    q_50 = [xlvs[x].quantiles()[0] for x in xs]
    q_95 = [xlvs[x].quantiles()[1] for x in xs]
    q_99 = [xlvs[x].quantiles()[2] for x in xs]

    return xs, counts, means, q_50, q_95, q_99


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
