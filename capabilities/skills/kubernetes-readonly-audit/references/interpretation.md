# Inventory interpretation

- PVC requested capacity is not measured filesystem use or unique physical allocation.
- A Bound PVC is not evidence that a backup exists or a restore succeeds.
- A Ready node is not evidence that every workload is healthy or its GPU works.
- Service ports are not necessarily container targetPorts or public listener ports.
- Route names alone do not establish internet exposure, TLS or authentication.
- A denied cluster-wide Secret listing does not establish denial in each namespace.
- Authorization review is not an end-to-end test of runner networking or credentials.
- Inventory snapshots are observations, not authority to overwrite desired state.
