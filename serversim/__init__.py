"""
Package to support simulation of different service/microservice deployment granularities.  Depends on SimPy 3.x.
"""

from .service import (
    SvcRequester, CoreSvcRequester, Async, Block, CallSeq, CallPar, Cont)
from .server import Server
from .usergroup import UserGroup
