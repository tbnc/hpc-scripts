#!/usr/bin/python3.11
# -*- coding: utf-8 -*-
from __future__ import annotations

import itertools
import os
from typing import Literal

from hpc_scripts import common
from hpc_scripts.santis import defaults, defs, make_run_ecrad_versions, sbatch, utils

# >>> config: start
ACCOUNT: defs.Account = defaults.ACCOUNT
BRANCH: str = "main"
DACE_DEFAULT_BLOCK_SIZE: str | None = None
DRY_RUN: bool = False
ECRAD_ENABLE_CHECKS: bool = True
ECRAD_MODE: Literal["fortran", "gt4py", "validate", "validate_all"] = "validate_all"
ECRAD_NUM_RUNS: int = 1
ECRAD_PRECISION: list[defs.FloatingPointPrecision] = ["double"]
ECRAD_STENCIL_NAME: list[str] = ["ecrad_ecckd_tripleclouds"]
ECRAD_STENCIL_VERSION: list[str] = ["cy49r1s_pmap"]
ECRAD_VERBOSE: bool = True
GT_BACKEND: list[str] = ["gt:gpu", "dace:gpu"]
NUM_RUNS: int = 1
PARTITION: defs.Partition = defaults.PARTITION
PYTHON_VERSION: defs.PythonVersion = defaults.PYTHON_VERSION
TIME: str = "24:00:00"
UENV: defs.UEnv = defaults.UENV
# >>> config: end


def main():
    for ecrad_precision, ecrad_stencil_name, ecrad_stencil_version, gt_backend in itertools.product(
        ECRAD_PRECISION, ECRAD_STENCIL_NAME, ECRAD_STENCIL_VERSION, GT_BACKEND
    ):
        job_dir = os.path.join(
            defs.jobs_root_dir,
            utils.get_uenv_with_dashes(UENV),
            "ecrad-versions",
            BRANCH,
            ECRAD_MODE,
            ecrad_stencil_version,
            ecrad_stencil_name,
            ecrad_precision
            if ECRAD_MODE == "fortran"
            else f"{gt_backend.replace(':', '')}/{ecrad_precision}",
        )
        with common.utils.output_directory(path=job_dir):
            job_name = (
                f"ecrad_{ECRAD_MODE}-{ecrad_stencil_name}-{ecrad_stencil_version}-"
                f"{gt_backend}-{ecrad_precision[0]}"
            )
            job_script = make_run_ecrad_versions.core(
                branch=BRANCH,
                dace_default_block_size=DACE_DEFAULT_BLOCK_SIZE,
                ecrad_enable_checks=ECRAD_ENABLE_CHECKS,
                ecrad_mode=ECRAD_MODE,
                ecrad_num_runs=ECRAD_NUM_RUNS,
                ecrad_precision=ecrad_precision,
                ecrad_stencil_name=ecrad_stencil_name,
                ecrad_stencil_version=ecrad_stencil_version,
                ecrad_verbose=ECRAD_VERBOSE,
                gt_backend=gt_backend,
                num_nodes=(num_nodes := 1),
                num_runs=NUM_RUNS,
                num_tasks_per_node=(num_tasks_per_node := 1),
                num_threads_per_task=64,
                python_version=PYTHON_VERSION,
                refresh_python_venv=False,  # no internet connection on the compute nodes
                uenv=UENV,
            )
            sbatch.core(
                account=ACCOUNT,
                dry_run=DRY_RUN,
                job_name=job_name,
                job_script=job_script,
                num_nodes=num_nodes,
                num_tasks_per_node=num_tasks_per_node,
                partition=PARTITION,
                time=TIME,
                uenv=UENV,
            )


if __name__ == "__main__":
    main()
