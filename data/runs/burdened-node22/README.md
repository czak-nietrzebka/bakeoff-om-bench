BURDENED BY CONFOUND A5 (2026-08-26) - the arm-B runs of series RUN-1.

Arm B worked on the system's node 22.22, while the arena repository declares
`engines.node: 24.x` and arm A was given an explicit PATH with node 24.19.

Two causes, both on the testbench side:
1. `launcher_b_env` did not set PATH - the arm-B tick inherited the process environment.
   Arm A forced it to be explicit, because `sudo` clears the environment; arm B did not,
   so nobody checked what it inherited. It looked healthy in the pilot, because
   `--test-command` DOES carry an explicit PATH: the verification had the right node and
   the work itself did not.
2. The arm-B home directory was mode 750, so the agent's user could not have executed the
   node 24 binary even if it had been pointed at it - PATH would name the target and the
   shell would quietly fall back to the system's node 22.

Measured on T4-B: 15 of 80 bash calls (18%) were looking for node, including downloading
node 24 into /tmp; 29 build/test calls against 4 at baseline (retries). Reconnaissance was
SIMILAR on both sides (26 vs 23) - so the claim "the persona makes the agent recon more"
is false; the divergence came from the environment.

This is an unequal START, not a difference of method - a confound loading one arm only.

The records are NOT deleted: they are evidence, and the reference point for MEASURING the
confound (against the rerun on an equalised environment). Arm A is not affected by this
confound: its T1-T5 runs stand and are not repeated.

Fix: `launcher_b_env(node_path=...)` plus a symmetry meta-test (the node in arm A's command
== the node in arm B's environment), and a traverse ACL for the agent's user.
The decision to rerun arm B: the operator, 2026-08-26.
