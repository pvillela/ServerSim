"""
Comparison of microservice deployment alternatives.
"""

from __future__ import print_function

import random

import simpy

from serversim import *


# fi = open("simout.txt", "w")
fi = sys.stdout


usersCurve = [(0, 900), (50, 650), (100, 900), (150, 650)]


def microservices_example(num_users, weight1, weight2, server_range1,
                          server_range2):

    def cug(mid, delta):
        """Computation units geneartor"""
        def f():
            return random.uniform(mid - delta, mid + delta)
        return f

    def ld_bal(svc_name):
        """Application server load-balancer."""
        if svc_name == "svc_1":
            s = random.choice(servers1)
        elif svc_name == "svc_2":
            s = random.choice(servers2)
        else:
            assert False, "Invalid service type."
        return s

    try:

        random.seed(12345)

        # num_users = 700
        simtime = 200
        hw_threads = 10
        sw_threads = 20
        speed = 20
        svc_1_comp_units = 2.0
        svc_2_comp_units = 1.0

        env = simpy.Environment()

        n_servers = max(server_range1[-1] + 1, server_range2[-1] + 1)
        servers = [Server(env, hw_threads, sw_threads, speed, "AppServer_%s" % i)
                   for i in range(n_servers)]
        servers1 = [servers[i] for i in server_range1]
        servers2 = [servers[i] for i in server_range2]

        svc_1 = CoreSvcRequester(env, "svc_1", cug(svc_1_comp_units,
                                                   svc_1_comp_units*.9), ld_bal)
        svc_2 = CoreSvcRequester(env, "svc_2", cug(svc_2_comp_units,
                                                   svc_2_comp_units*.9), ld_bal)

        weighted_txns = [(svc_1, weight1),
                         (svc_2, weight2)
                         ]

        min_think_time = 2.0  # .5 # 4
        max_think_time = 10.0  # 1.5 # 20

        grp = UserGroup(env, num_users, "UserTypeX", weighted_txns,
                        min_think_time, max_think_time)
        grp.activate_users()

        print("\n\n***** Start Simulation --", num_users, ",", weight1, ",",
              weight2, ", [", server_range1[0], ",", server_range1[-1] + 1,
              ") , [", server_range2[0], ",", server_range2[-1] + 1, ") *****",
              file=fi)
        print("Simulation: num_users =", num_users, "; simTime =", simtime,
              file=fi)

        env.run(until=simtime)

        print("<< ServerExample >>\n", file=fi)

        indent = " " * 4

        # print parameters
        print("\n" + "simtime =", simtime, file=fi)

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
        print(indent * 2 + "num_users =", grp.num_users, file=fi)
        print(indent * 2 + "min_think_time =", grp.min_think_time, file=fi)
        print(indent * 2 + "max_think_time =", grp.max_think_time, file=fi)
        print(indent * 2 + "responded_request_count =", grp.responded_request_count(None), file=fi)
        print(indent * 2 + "unresponded_request_count =", grp.unresponded_request_count(None), file=fi)
        print(indent * 2 + "avg_response_time =", grp.avg_response_time(None), file=fi)
        print(indent * 2 + "std_dev_response_time =", grp.std_dev_response_time(None), file=fi)
        print(indent*2 + "throughput =", grp.throughput(None), file=fi)

        for txn in grp.svcs:
            print(indent*2 + txn.svc_name + ":", file=fi)
            print(indent * 3 + "responded_request_count =", grp.responded_request_count(txn), file=fi)
            print(indent * 3 + "unresponded_request_count =", grp.unresponded_request_count(txn), file=fi)
            print(indent * 3 + "avg_response_time =", grp.avg_response_time(txn), file=fi)
            print(indent * 3 + "std_dev_response_time =", grp.std_dev_response_time(txn), file=fi)
            print(indent*3 + "throughput =", grp.throughput(txn), file=fi)

    finally:
        if not fi == sys.stdout:
            fi.close()
        print("\n*** Done ***", file=fi)


if __name__ == "__main__":
    print("\n\n\n@@@@@@@@@ Start comparative simulations @@@@@@@@@@")
    microservices_example(num_users=700, weight1=2, weight2=1, server_range1=range(0, 10), server_range2=range(0, 10))
    microservices_example(num_users=700, weight1=2, weight2=1, server_range1=range(0, 8), server_range2=range(8, 10))
    #
    # microservices_example(numUsers=700, weight1=5, weight2=1, serverRange1=range(0, 10), serverRange2=range(0, 10))
    # microservices_example(numUsers=700, weight1=5, weight2=1, serverRange1=range(0, 8), serverRange2=range(8, 10))
    #
    # microservices_example(numUsers=700, weight1=1, weight2=1, serverRange1=range(0, 10), serverRange2=range(0, 10))
    # microservices_example(numUsers=700, weight1=1, weight2=1, serverRange1=range(0, 8), serverRange2=range(8, 10))
    #
    # microservices_example(numUsers=700, weight1=1, weight2=1, serverRange1=range(0, 9), serverRange2=range(0, 9))
    # microservices_example(numUsers=700, weight1=1, weight2=1, serverRange1=range(0, 7), serverRange2=range(7, 9))
    # microservices_example(numUsers=700, weight1=1, weight2=1, serverRange1=range(0, 6), serverRange2=range(6, 9))
    #
    # microservices_example(numUsers=usersCurve, weight1=2, weight2=1, serverRange1=range(0, 10), serverRange2=range(0, 10))
    # microservices_example(numUsers=usersCurve, weight1=2, weight2=1, serverRange1=range(0, 8), serverRange2=range(8, 10))
    #
    # microservices_example(numUsers=usersCurve, weight1=1, weight2=1, serverRange1=range(0, 9), serverRange2=range(0, 9))
    # microservices_example(numUsers=usersCurve, weight1=1, weight2=1, serverRange1=range(0, 7), serverRange2=range(7, 9))
    # microservices_example(numUsers=usersCurve, weight1=1, weight2=1, serverRange1=range(0, 6), serverRange2=range(6, 9))
