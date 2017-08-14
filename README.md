# ServerSim

This is a framework for the creation of discrete event simulation models to analyze the performance and utilization of computer servers and services.

Software engineers and architects not familiar with Python may want to jump directly to the *Simulations* section of the tutorial, skip the code, and focus on the simulation definitions and conclusions.

### ServerSim Core Concepts

Click [here](https://github.com/pvillela/ServerSim/blob/master/CoreConcepts.ipynb) for the overview of ServerSim core concepts.

### Tutorial

Click [here](https://github.com/pvillela/ServerSim/blob/master/TutorialExample.ipynb) for the tutorial.  The tutorial provides a detailed example comparing two major service deployment patterns:

- **Cookie-cutter deployment**, where all services making up an application are deployed together on each VM or container.  This is typical for "monolithic" applications but can also be used for micro-services. See [Fowler](https://martinfowler.com/bliki/MicroservicePremium.html) and [Hammant](https://paulhammant.com/2011/11/29/cookie-cutter-scaling/).
- **Individualized deployment**, where each of the services is deployed on its own VM or (more likely) it own container.
