"""
Supports the creation of discrete event simulation models to analyze the
performance and utilization of computer servers and services.
Depends on SimPy 3.x.
"""

from .service import (
    SvcRequester, CoreSvcRequester, Async, Block, CallSeq, CallPar, Cont)
from .server import Server
from .usergroup import UserGroup
