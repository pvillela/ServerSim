from typing import TYPE_CHECKING, Sequence, Tuple
import functools as ft

import pylab as plt
from livestats import livestats

if TYPE_CHECKING:
    from serversim import UserGroup


def resp_times_by_interval(time_resolution, grp):
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


def plot_means_q95(quantiles1, quantiles2):

    x = quantiles1[0]  # should be same as quantiles2[0]

    counts1 = quantiles1[1]
    counts2 = quantiles2[1]

    means1 = quantiles1[2]
    means2 = quantiles2[2]

    q1_95 = quantiles1[4]
    q2_95 = quantiles2[4]

    # Plot counts
    plt.plot(x, counts1, color='b')
    plt.plot(x, counts2, color='r')
    plt.show()

    # Plot averages and 95th percentiles

    plt.plot(x, means1, color='b')
    plt.plot(x, q1_95, color='b')

    plt.plot(x, means2, color='r')
    plt.plot(x, q2_95, color='r')

    plt.show()

    
def compare_simulations(res1, res2):
    grp1 = res1["grp"]
    grp2 = res2["grp"]

    quantiles1 = resp_times_by_interval(5, grp1)
    quantiles2 = resp_times_by_interval(5, grp2)

    plot_means_q95(quantiles1, quantiles2)
