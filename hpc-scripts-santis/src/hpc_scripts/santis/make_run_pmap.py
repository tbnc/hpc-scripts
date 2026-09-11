#!/usr/bin/python3.11
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import os

from hpc_scripts import common
from hpc_scripts.santis import defaults, defs, make_prepare_pmap

# >>> config: start
BRANCH: str = "main"
DACE_DEFAULT_BLOCK_SIZE: str | None = None
GHEX_AGGREGATE_FIELDS: bool = False
GHEX_COLLECT_STATISTICS: bool = False
GT_BACKEND: str = "gt:gpu"
NUM_NODES: int = 1
NUM_RUNS: int = 1
NUM_TASKS_PER_NODE: int = 1
NUM_THREADS_PER_TASK: int = 1
PMAP_DISABLE_LOG: bool = False
PMAP_ENABLE_BENCHMARKING: bool = False
PMAP_ENABLE_OVERCOMPUTING: bool = False
PMAP_EXTENDED_TIMERS: bool = False
PMAP_PRECISION: defs.FloatingPointPrecision = "double"
USE_CASE: str = "thermal"
# >>> config: end


def core(
    branch: str,
    dace_default_block_size: str,
    ghex_aggregate_fields: bool,
    ghex_collect_statistics: bool,
    ghex_transport_backend: defs.GHEXTransportBackend,
    gt_backend: str,
    num_nodes: int,
    num_runs: int,
    num_tasks_per_node: int,
    num_threads_per_task: int,
    output_dir: str,
    pmap_disable_log: bool,
    pmap_enable_benchmarking: bool,
    pmap_enable_overcomputing: bool,
    pmap_extended_timers: bool,
    pmap_precision: defs.FloatingPointPrecision,
    python_version: defs.PythonVersion,
    refresh_python_venv: bool,
    uenv: defs.UEnv,
    use_case: str,
) -> str:
    prepare_pmap_fname = make_prepare_pmap.core(
        branch, ghex_transport_backend, python_version, refresh_python_venv, uenv
    )

    with common.utils.output_file(filename="run_pmap") as (_, fname):
        common.utils.run(f". {prepare_pmap_fname}")

        with common.utils.chdir("$PMAP"):
            common.utils.run(". $PMAP_VENV/bin/activate")
            common.utils.export_variable("GHEX_AGGREGATE_FIELDS", int(ghex_aggregate_fields))
            common.utils.export_variable("GHEX_COLLECT_STATISTICS", int(ghex_collect_statistics))
            common.utils.export_variable("GT_BACKEND", gt_backend)
            common.utils.export_variable("OMP_NUM_THREADS", num_threads_per_task)
            common.utils.export_variable("OMP_PLACES", "cores")
            common.utils.export_variable("OMP_PROC_BIND", "close")
            # common.utils.export_variable("OMP_DISPLAY_AFFINITY", "True")
            common.utils.export_variable("PMAP_DISABLE_LOG", int(pmap_disable_log))
            common.utils.export_variable("PMAP_ENABLE_BENCHMARKING", int(pmap_enable_benchmarking))
            common.utils.export_variable(
                "PMAP_ENABLE_OVERCOMPUTING", int(pmap_enable_overcomputing)
            )
            common.utils.export_variable("PMAP_EXTENDED_TIMERS", int(pmap_extended_timers))
            common.utils.export_variable("PMAP_PRECISION", pmap_precision)
            if dace_default_block_size:
                common.utils.export_variable("DACE_DEFAULT_BLOCK_SIZE", dace_default_block_size)

            if output_dir is not None:
                output_dir = os.path.abspath(output_dir)
            else:
                output_dir = os.path.join(
                    "_data",
                    uenv.replace("/", "-").replace(":", "-"),
                    use_case,
                    pmap_precision,
                    gt_backend.replace(":", ""),
                )
            common.utils.run(f"mkdir -p {output_dir}")
            command = (
                f"srun "
                f"--nodes={num_nodes} --ntasks-per-node={num_tasks_per_node} --gpus-per-task=1 "
                f"pmap {os.path.join('config', use_case + '.yml')} "
                f"--output-directory={output_dir}"
            )
            if pmap_enable_benchmarking:
                command += " --write-profiling-data"

            for _ in range(num_runs):
                common.utils.run(command)

    return fname


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--branch", type=str, default=BRANCH)
    parser.add_argument("--dace-default-block-size", type=str, default=DACE_DEFAULT_BLOCK_SIZE)
    parser.add_argument("--ghex-aggregate-fields", type=bool, default=GHEX_AGGREGATE_FIELDS)
    parser.add_argument("--ghex-collect-statistics", type=bool, default=GHEX_COLLECT_STATISTICS)
    parser.add_argument(
        "--ghex-transport-backend", type=bool, default=defaults.GHEX_TRANSPORT_BACKEND
    )
    parser.add_argument("--gt-backend", type=str, default=GT_BACKEND)
    parser.add_argument("--num-nodes", type=int, default=NUM_NODES)
    parser.add_argument("--num-runs", type=int, default=NUM_RUNS)
    parser.add_argument("--num-tasks-per-node", type=int, default=NUM_TASKS_PER_NODE)
    parser.add_argument("--num-threads-per-task", type=int, default=NUM_THREADS_PER_TASK)
    parser.add_argument("--pmap-disable-log", type=bool, default=PMAP_DISABLE_LOG)
    parser.add_argument("--pmap-enable-benchmarking", type=bool, default=PMAP_ENABLE_BENCHMARKING)
    parser.add_argument("--pmap-enable-overcomputing", type=bool, default=PMAP_ENABLE_OVERCOMPUTING)
    parser.add_argument("--pmap-extended-timers", type=bool, default=PMAP_EXTENDED_TIMERS)
    parser.add_argument("--pmap-precision", type=str, default=PMAP_PRECISION)
    parser.add_argument("--python", type=str, default=defaults.PYTHON_VERSION)
    parser.add_argument("--refresh-python-venv", action="store_true")
    parser.add_argument("--uenv", type=str, default=defaults.UENV)
    parser.add_argument("--use-case", type=str, default=USE_CASE)
    args = parser.parse_args()
    with common.utils.output_directory():
        core(**args.__dict__)
