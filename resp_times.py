from typing import TYPE_CHECKING, Sequence, Tuple
import functools as ft

import numpy as np
import pylab as plt
from livestats import livestats

if TYPE_CHECKING:
    from serversim import UserGroup


def resp_times_by_interval(time_resolution, grp):
    # type: (float, UserGroup) -> Tuple[Sequence[float], Sequence[float], Sequence[float], Sequence[float]]
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
    xs = np.array(xs)
    q_50 = np.array([xlvs[x].quantiles()[0] for x in xs])
    q_95 = np.array([xlvs[x].quantiles()[1] for x in xs])
    q_99 = np.array([xlvs[x].quantiles()[2] for x in xs])

    return xs, q_50, q_95, q_99


def plot_q50_q95(quantiles1, quantiles2):

    x = quantiles1[0]  # should be same as quantiles2[0]
    
    q1_50 = quantiles1[1]
    q2_50 = quantiles2[1]

    q1_95 = quantiles1[2]
    q2_95 = quantiles2[2]

    plt.plot(x, q1_50, color='b')
    plt.plot(x, q1_95, color='c')

    plt.plot(x, q2_50, color='r')
    plt.plot(x, q2_95, color='m')

    plt.show()

    
def compare_simulations(res1, res2):
    grp1 = res1["grp"]
    grp2 = res2["grp"]

    quantiles1 = resp_times_by_interval(5, grp1)
    quantiles2 = resp_times_by_interval(5, grp2)

    plot_q50_q95(quantiles1, quantiles2)
