from typing import TYPE_CHECKING, Sequence, Tuple
import functools as ft

import numpy as np
from livestats import livestats

if TYPE_CHECKING:
    from serversim import Server


def server_resp_time(time_resolution, servers):
    # type: (float, Sequence[Server]) -> Tuple[Sequence[float], Sequence[float], Sequence[float], Sequence[float]]
    quantiles = [0.5, 0.95, 0.99]

    svc_reqs = []
    for s in servers:
        svc_reqs = svc_reqs + s.svc_req_log

    xys = [(int(svc_req.time_dict["submitted"]/time_resolution),
            svc_req.time_dict["completed"] - svc_req.time_dict["submitted"])
           for svc_req in svc_reqs
           if svc_req.is_completed]

    def ffold(map, p):
        x, y = p
        if x not in map:
            map[x] = livestats.LiveStats(quantiles)
        map[x].add(y)
        return map

    xlvs = ft.reduce(ffold, xys, dict())

    xs = xlvs.keys()
    xs.sort()
    xs = np.array(xs)
    q_50 = np.array([xlvs[x].quantiles()[0] for x in xs])
    q_95 = np.array([xlvs[x].quantiles()[1] for x in xs])
    q_99 = np.array([xlvs[x].quantiles()[2] for x in xs])

    return xs, q_50, q_95, q_99
