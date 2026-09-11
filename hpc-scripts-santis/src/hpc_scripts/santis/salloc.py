#!/usr/bin/python3.11
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse

from hpc_scripts import common
from hpc_scripts.santis import defaults, defs

# >>> config: start
NUM_NODES: int = 1
NUM_TASKS_PER_NODE: int = 4
TIME: str = "02:00:00"
# >>> config: end


def core(
    account: str, num_nodes: int, num_tasks_per_node: int, partition: defs.Partition, time: str
) -> None:
    command = [
        "salloc",
        f"--account={account}",
        f"--nodes={num_nodes}",
        f"--ntasks-per-node={num_tasks_per_node}",
        "--gpus-per-task=1",
        f"--partition={partition}",
        f"--time={time}",
    ]
    common.utils.run(*command, verbose=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Get an allocation on the compute nodes.")
    parser.add_argument("--account", type=str, default=defaults.ACCOUNT)
    parser.add_argument("--num-nodes", type=int, default=NUM_NODES)
    parser.add_argument("--num-tasks-per-node", type=int, default=NUM_TASKS_PER_NODE)
    parser.add_argument("--partition", type=str, default=defaults.PARTITION)
    parser.add_argument("--time", type=str, default=TIME)
    args = parser.parse_args()
    core(**args.__dict__)


if __name__ == "__main__":
    main()
