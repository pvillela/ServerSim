
from __future__ import print_function

from typing import Sequence, Any, IO

from serversim import *


def print_results(numUsers=None, weight1=None, weight2=None, serverRange1=None,
                  serverRange2=None, servers=None, grp=None, fi=None):
    # type: (int, float, float, Sequence[int], Sequence[int], Sequence[Server], UserGroup, IO[str]) -> None
    
    if fi is None:
        import sys
        fi = sys.stdout

    print("\n\n***** Start Simulation --", numUsers, ",", weight1, ",", weight2, ", [", serverRange1[0], ",", serverRange1[-1] + 1,
          ") , [", serverRange2[0], ",", serverRange2[-1] + 1, ") *****", file=fi)
    print("Simulation: num_users =", numUsers, file=fi)

    print("<< ServerExample >>\n", file=fi)

    indent = " " * 4

    print("\n" + "Servers:", file=fi)
    for svr in servers:
        print(indent*1 + "Server:", svr.name, file=fi)
        print(indent * 2 + "max_concurrency =", svr.max_concurrency, file=fi)
        print(indent * 2 + "num_threads =", svr.num_threads, file=fi)
        print(indent*2 + "speed =", svr.speed, file=fi)
        print(indent * 2 + "avg_process_time =", svr.avg_process_time, file=fi)
        print(indent * 2 + "avg_hw_queue_time =", svr.avg_hw_queue_time, file=fi)
        print(indent * 2 + "avg_thread_queue_time =", svr.avg_thread_queue_time, file=fi)
        print(indent * 2 + "avg_service_time =", svr.avg_service_time, file=fi)
        print(indent * 2 + "avg_hw_queue_length =", svr.avg_hw_queue_length, file=fi)
        print(indent * 2 + "avg_thread_queue_length =", svr.avg_thread_queue_length, file=fi)
        print(indent * 2 + "hw_queue_length =", svr.hw_queue_length, file=fi)
        print(indent * 2 + "hw_in_process_count =", svr.hw_in_process_count, file=fi)
        print(indent * 2 + "thread_queue_length =", svr.thread_queue_length, file=fi)
        print(indent * 2 + "thread_in_use_count =", svr.thread_in_use_count, file=fi)
        print(indent*2 + "utilization =", svr.utilization, file=fi)
        print(indent*2 + "throughput =", svr.throughput, file=fi)

    print(indent*1 + "Group:", grp.name, file=fi)
    print(indent*2 + "num_users =", grp.num_users, file=fi)
    print(indent*2 + "min_think_time =", grp.min_think_time, file=fi)
    print(indent*2 + "max_think_time =", grp.max_think_time, file=fi)
    print(indent * 2 + "responded_request_count =", grp.responded_request_count(None), file=fi)
    print(indent * 2 + "unresponded_request_count =", grp.unresponded_request_count(None), file=fi)
    print(indent * 2 + "avg_response_time =", grp.avg_response_time(), file=fi)
    print(indent * 2 + "std_dev_response_time =", grp.std_dev_response_time(None), file=fi)
    print(indent*2 + "throughput =", grp.throughput(None), file=fi)

    for txn in grp.svcs:
        print(indent*2 + txn.svcName + ":", file=fi)
        print(indent * 3 + "responded_request_count =", grp.responded_request_count(txn), file=fi)
        print(indent * 3 + "unresponded_request_count =", grp.unresponded_request_count(txn), file=fi)
        print(indent * 3 + "avg_response_time =", grp.avg_response_time(txn), file=fi)
        print(indent * 3 + "std_dev_response_time =", grp.std_dev_response_time(txn), file=fi)
        print(indent*3 + "throughput =", grp.throughput(txn), file=fi)