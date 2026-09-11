#!/opt/cray/pe/python/3.11.7/bin/python
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import os
from typing import Literal

from hpc_scripts import common
from hpc_scripts.lumi import defaults, defs, make_prepare_pmap, make_select_gpu, utils

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
PROJECT: Literal["pmap", "pmap-real_cases-shared", "pmap-snapshots"] = "pmap"
USE_CASE: str = "thermal"
# >>> config: end


def core(
    branch: str,
    dace_default_block_size: str,
    env: defs.ProgrammingEnvironment,
    ghex_aggregate_fields: bool,
    ghex_collect_statistics: bool,
    ghex_transport_backend: defs.GHEXTransportBackend,
    gt_backend: str,
    hdf5_version: str,
    netcdf_version: str,
    num_nodes: int,
    num_runs: int,
    num_tasks_per_node: int,
    num_threads_per_task: int,
    output_dir: str,
    partition: defs.Partition,
    pmap_disable_log: bool,
    pmap_enable_benchmarking: bool,
    pmap_enable_overcomputing: bool,
    pmap_extended_timers: bool,
    pmap_precision: defs.FloatingPointPrecision,
    project: str,
    python_version: defs.PythonVersion,
    rocm_version: str,
    stack: defs.SoftwareStack,
    stack_version: str,
    use_case: str,
) -> str:
    prepare_pmap_fname = make_prepare_pmap.core(
        branch,
        env,
        ghex_transport_backend,
        hdf5_version,
        netcdf_version,
        partition,
        project,
        python_version,
        rocm_version,
        stack,
        stack_version,
    )

    project_with_underscores = project.replace("-", "_")
    with common.utils.output_file(filename=f"run_{project_with_underscores}") as (_, fname):
        common.utils.run(f". {prepare_pmap_fname}")

        with common.utils.chdir(f"${project_with_underscores.upper()}"):
            common.utils.run(f". ${project_with_underscores.upper()}_VENV/bin/activate")
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
            if utils.get_partition_type(partition) == "gpu" and dace_default_block_size:
                common.utils.export_variable("DACE_DEFAULT_BLOCK_SIZE", dace_default_block_size)

            srun_options = utils.get_srun_options(
                num_nodes,
                num_tasks_per_node,
                num_threads_per_task,
                partition,
                gt_backend=gt_backend,
            )
            select_gpu_fname = make_select_gpu.core()
            if output_dir is not None:
                output_dir = os.path.abspath(output_dir)
            else:
                output_dir = os.path.join(
                    "_data", use_case, pmap_precision, gt_backend.replace(":", "")
                )
            common.utils.run(f"mkdir -p {output_dir}")
            command = (
                f"srun {' '.join(srun_options)} {select_gpu_fname} pmap "
                f"{os.path.join('config', use_case + '.yml')} "
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
    parser.add_argument("--env", type=str, default=defaults.ENV)
    parser.add_argument("--ghex-aggregate-fields", type=bool, default=GHEX_AGGREGATE_FIELDS)
    parser.add_argument("--ghex-collect-statistics", type=bool, default=GHEX_COLLECT_STATISTICS)
    parser.add_argument(
        "--ghex-transport-backend", type=bool, default=defaults.GHEX_TRANSPORT_BACKEND
    )
    parser.add_argument("--gt-backend", type=str, default=GT_BACKEND)
    parser.add_argument("--hdf5-version", type=str, default=defaults.HDF5_VERSION)
    parser.add_argument("--netcdf-version", type=str, default=defaults.NETCDF_VERSION)
    parser.add_argument("--num-nodes", type=int, default=NUM_NODES)
    parser.add_argument("--num-runs", type=int, default=NUM_RUNS)
    parser.add_argument("--num-tasks-per-node", type=int, default=NUM_TASKS_PER_NODE)
    parser.add_argument("--num-threads-per-task", type=int, default=NUM_THREADS_PER_TASK)
    parser.add_argument("--partition", type=str, default=defaults.PARTITION)
    parser.add_argument("--pmap-disable-log", type=bool, default=PMAP_DISABLE_LOG)
    parser.add_argument("--pmap-enable-benchmarking", type=bool, default=PMAP_ENABLE_BENCHMARKING)
    parser.add_argument("--pmap-enable-overcomputing", type=bool, default=PMAP_ENABLE_OVERCOMPUTING)
    parser.add_argument("--pmap-extended-timers", type=bool, default=PMAP_EXTENDED_TIMERS)
    parser.add_argument("--pmap-precision", type=str, default=PMAP_PRECISION)
    parser.add_argument("--project", type=str, default=PROJECT)
    parser.add_argument("--python-version", type=str, default=defaults.PYTHON_VERSION)
    parser.add_argument("--rocm-version", type=str, default=defaults.ROCM_VERSION)
    parser.add_argument("--stack", type=str, default=defaults.STACK)
    parser.add_argument("--stack-version", type=str, default=defaults.STACK_VERSION)
    parser.add_argument("--use-case", type=str, default=USE_CASE)
    args = parser.parse_args()
    with common.utils.output_directory():
        core(**args.__dict__)
