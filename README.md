# ServerSim

This is a framework for the creation of discrete event simulation models to analyze the performance and utilization of computer servers and services.

Software engineers and architects not familiar with Python may want to jump directly to the *Simulations* section of the tutorial, skip the code, and focus on the simulation definitions and conclusions.

### ServerSim Core Concepts

Click [here](https://github.com/pvillela/ServerSim/blob/master/CoreConcepts.ipynb) for the overview of ServerSim core concepts.

### Tutorial

Click [here](https://github.com/pvillela/ServerSim/blob/master/TutorialExample.ipynb) for the tutorial.  The tutorial provides a detailed example comparing two major service deployment patterns for multi-threaded services:

- **Cookie-cutter deployment**, where all services making up an application are deployed together on each physical or virtual server.  Each service may be deployed as a process or as a container.  The determining characteristic of this deployment approach is that services deployed on a server do not have compartmentalized allocations of computational capacity and share the server's overall computational capacity.  This is typical for "monolithic" applications (see [Fowler](https://martinfowler.com/bliki/MicroservicePremium.html) and [Hammant](https://paulhammant.com/2011/11/29/cookie-cutter-scaling/)) but can also be used for micro-services.
- **Individualized deployment**, where each of the services is deployed on its own physical or virtual server (which may be a container).  The determining characteristic of this deployment approach is that services deployed on a server have individual compartmentalized allocations of computational capacity, so that one service's computations do not compete with other services' computations for capacity.

