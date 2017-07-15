SIMULATION OF SERVICE DEPLOYMENT SCENARIOS
==========================================

# Core Concepts

- **Server** -- Has a *concurrency capacity* and a *speed rating* in terms of computation units per second per concurrent execution.  A server has an infinite queue for service requests that exceed it concurrency capacity.
- **ServiceRequest** -- Has a distribution function for the number of computation units required to process a request.
- 