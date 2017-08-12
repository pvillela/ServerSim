"""
Supports the creation of discrete event simulation models to analyze the
performance and utilization of computer servers and services.
Depends on SimPy 3.x.
"""

import sys
import logging
import atexit

import const
from .measuredresource import MeasuredResource
from .server import Server
from .service import (
    SvcRequest, SvcRequester, CoreSvcRequester, Async, Blkg, Seq, Par)
from .usergroup import UserGroup
from .util import nullary, curried_nullary


indent = " " * 4

# const.logfile = open("simout.txt", "w")
const.logfile = sys.stdout


def _closeLogfile():
    if const.logfile is not None and not const.logfile == sys.stdout and not const.logfile == sys.stderr:
        const.logfile.close()


atexit.register(_closeLogfile)

logging.basicConfig(level=logging.INFO,
                    format='%(levelname)-4s %(message)s',
                    stream=const.logfile)
