import pylab as plt
from livestats import livestats


def plot_q50_q95(quantiles1, quantiles2):

    X = quantiles1[0]  # should be same as quantiles2[0]
    
    Q1_50 = quantiles1[1]
    Q2_50 = quantiles2[1]

    Q1_95 = quantiles1[2]
    Q2_95 = quantiles2[2]

    plt.plot(X, Q1_50,color='b')
    plt.plot(X, Q1_95,color='c')

    plt.plot(X, Q2_50,color='r')
    plt.plot(X, Q2_95,color='m')

    plt.show()