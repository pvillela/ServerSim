from typing import TYPE_CHECKING, Sequence, Tuple
import functools as ft
from collections import OrderedDict

import matplotlib.pyplot as plt
import pandas as pd
from livestats import livestats

if TYPE_CHECKING:
    from serversim import UserGroup


def minibatch_resp_times_pandas1(time_resolution, grp):
    # type: (float, UserGroup) -> Tuple[Sequence[float], Sequence[float], Sequence[float], Sequence[float], Sequence[float], Sequence[float]]

    xys = (((svc_req.time_dict["submitted"]//time_resolution) * time_resolution,
            svc_req.time_dict["completed"] - svc_req.time_dict["submitted"])
           for (_, svc_req) in grp.svc_req_log
           if svc_req.is_completed)

    df = pd.DataFrame(xys, columns=["time", "resp_time"])
    grouped = df.groupby("time")

    counts_df = grouped.count()['resp_time']
    ts = counts_df.index.values
    counts = counts_df.values
    means = grouped.mean()['resp_time'].values
    q_50 = grouped.quantile(.50)['resp_time'].values
    q_95 = grouped.quantile(.95)['resp_time'].values
    q_99 = grouped.quantile(.99)['resp_time'].values

    return ts, counts, means, q_50, q_95, q_99


def minibatch_resp_times_without_pandas(time_resolution, grp):
    # type: (float, UserGroup) -> Tuple[Sequence[float], Sequence[float], Sequence[float], Sequence[float], Sequence[float], Sequence[float]]
    quantiles = [0.5, 0.95, 0.99]

    xys = ((int(svc_req.time_dict["submitted"]/time_resolution),
            svc_req.time_dict["completed"] - svc_req.time_dict["submitted"])
           for (_, svc_req) in grp.svc_req_log
           if svc_req.is_completed)

    def ffold(map_, p):
        x, y = p
        if x not in map_:
            map_[x] = livestats.LiveStats(quantiles)
        map_[x].add(y)
        return map_

    xlvs = ft.reduce(ffold, xys, dict())

    xs = xlvs.keys()
    xs.sort()

    ts = [x*time_resolution for x in xs]
    counts = [xlvs[x].count for x in xs]
    means = [xlvs[x].average for x in xs]
    q_50 = [xlvs[x].quantiles()[0] for x in xs]
    q_95 = [xlvs[x].quantiles()[1] for x in xs]
    q_99 = [xlvs[x].quantiles()[2] for x in xs]

    return ts, counts, means, q_50, q_95, q_99
