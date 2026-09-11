#!/usr/bin/python3.11
# -*- coding: utf-8 -*-
from __future__ import annotations

import itertools
import os

from hpc_scripts import common
from hpc_scripts.santis import defaults, defs, make_run_pmap, sbatch, utils

# >>> config: start
ACCOUNT: defs.Account = defaults.ACCOUNT
BRANCH: str = "nesting-radiation"
DACE_DEFAULT_BLOCK_SIZE: str | None = None
DRY_RUN: bool = False
GHEX_AGGREGATE_FIELDS: bool = False
GHEX_COLLECT_STATISTICS: bool = False
GHEX_TRANSPORT_BACKEND: defs.GHEXTransportBackend = defaults.GHEX_TRANSPORT_BACKEND
GT_BACKEND: list[str] = ["dace:gpu"]
NUM_RUNS: int = 1
PARTITION: defs.Partition = defaults.PARTITION
PMAP_DISABLE_LOG: bool = False
PMAP_ENABLE_BENCHMARKING: bool = False
PMAP_ENABLE_OVERCOMPUTING: bool = True
PMAP_EXTENDED_TIMERS: bool = False
PMAP_PRECISION: list[defs.FloatingPointPrecision] = ["single"]
PYTHON_VERSION: defs.PythonVersion = defaults.PYTHON_VERSION
TIME: str = "03:00:00"
USE_CASE: dict[str, list[common.utils.ThreadsLayout]] = {
    "tests/nesting/baroclinic_wave_sphere_moist_rotated": [common.utils.ThreadsLayout(1, 1, 64)]
}
UENV: defs.UEnv = defaults.UENV
# >>> config: end


def main():
    for gt_backend, pmap_precision, use_case in itertools.product(
        GT_BACKEND, PMAP_PRECISION, USE_CASE
    ):
        for threads_layout in USE_CASE[use_case]:
            job_dir = os.path.join(
                defs.jobs_root_dir,
                utils.get_uenv_with_dashes(UENV),
                "pmap",
                BRANCH,
                use_case,
                pmap_precision,
                gt_backend.replace(":", ""),
            )
            with common.utils.output_directory(path=job_dir) as output_dir:
                job_name = (
                    f"{use_case.replace('/', '-')}-{threads_layout.num_tasks}-{pmap_precision[0]}"
                )
                job_script = make_run_pmap.core(
                    branch=BRANCH,
                    dace_default_block_size=DACE_DEFAULT_BLOCK_SIZE,
                    ghex_aggregate_fields=GHEX_AGGREGATE_FIELDS,
                    ghex_collect_statistics=GHEX_COLLECT_STATISTICS,
                    ghex_transport_backend=GHEX_TRANSPORT_BACKEND,
                    gt_backend=gt_backend,
                    num_nodes=threads_layout.num_nodes,
                    num_runs=NUM_RUNS,
                    num_tasks_per_node=threads_layout.num_tasks_per_node,
                    num_threads_per_task=threads_layout.num_threads_per_task,
                    output_dir=output_dir,
                    pmap_disable_log=PMAP_DISABLE_LOG,
                    pmap_enable_benchmarking=PMAP_ENABLE_BENCHMARKING,
                    pmap_enable_overcomputing=PMAP_ENABLE_OVERCOMPUTING,
                    pmap_extended_timers=PMAP_EXTENDED_TIMERS,
                    pmap_precision=pmap_precision,
                    python_version=PYTHON_VERSION,
                    refresh_python_venv=False,  # no internet connection on the compute nodes
                    uenv=UENV,
                    use_case=use_case,
                )
                sbatch.core(
                    account=ACCOUNT,
                    dry_run=DRY_RUN,
                    job_name=job_name,
                    job_script=job_script,
                    num_nodes=threads_layout.num_nodes,
                    num_tasks_per_node=threads_layout.num_tasks_per_node,
                    partition=PARTITION,
                    time=TIME,
                    uenv=UENV,
                )


if __name__ == "__main__":
    main()
