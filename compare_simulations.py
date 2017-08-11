def compare_simulations(res1, res2):
    servers1 = res1["servers"]
    servers2 = res2["servers"]

    quantiles1 = server_resp_time(5, servers1)
    quantiles2 = server_resp_time(5, servers2)

    plot_q50_q95(quantiles1, quantiles2)