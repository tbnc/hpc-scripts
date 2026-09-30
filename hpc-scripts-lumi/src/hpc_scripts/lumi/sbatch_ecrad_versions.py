#!/opt/cray/pe/python/3.11.7/bin/python
# -*- coding: utf-8 -*-
from __future__ import annotations

import itertools
from typing import Literal

from hpc_scripts import common
from hpc_scripts.lumi import defaults, defs, make_run_ecrad_versions, sbatch

# >>> config: start
ACCOUNT: int = defaults.ACCOUNT
BRANCH: str = "main"
DACE_DEFAULT_BLOCK_SIZE: str = "'256,1,1'"
DRY_RUN: bool = False
ECRAD_ENABLE_CHECKS: bool = True
ECRAD_MODE: Literal["fortran", "gt4py", "validate", "validate_all"] = "gt4py"
ECRAD_NUM_RUNS: int = 0
ECRAD_PRECISION: list[defs.FloatingPointPrecision] = ["single"]
ECRAD_STENCIL_NAME: list[str] = ["solver_tripleclouds_lw", "solver_tripleclouds_sw"]
ECRAD_STENCIL_VERSION: list[str] = ["cy49r1s"]
ECRAD_VERBOSE: bool = True
ENV: defs.ProgrammingEnvironment = "cray"
GT_BACKEND: list[str] = ["gt:cpu_kfirst", "gt:gpu"]
HDF5_VERSION: str = defaults.HDF5_VERSION
NETCDF_VERSION: str = defaults.NETCDF_VERSION
NUM_RUNS: int = 1
PARTITION: defs.Partition = "standard-g"
PYTHON_VERSION: defs.PythonVersion = defaults.PYTHON_VERSION
ROCM_VERSION: str = defaults.ROCM_VERSION
STACK: defs.SoftwareStack = defaults.STACK
STACK_VERSION: str = defaults.STACK_VERSION
TIME: str = "05:00:00"
# >>> config: end


def main():
    for ecrad_precision, ecrad_stencil_name, ecrad_stencil_version, gt_backend in itertools.product(
        ECRAD_PRECISION, ECRAD_STENCIL_NAME, ECRAD_STENCIL_VERSION, GT_BACKEND
    ):
        job_dir = (
            f"ecrad-versions/{BRANCH}/_jobs/{PARTITION}/{ECRAD_MODE}/{ecrad_stencil_version}/"
            f"{ecrad_stencil_name}/"
        )
        job_dir += (
            f"{ecrad_precision}"
            if ECRAD_MODE == "fortran"
            else f"{gt_backend.replace(':', '')}/{ecrad_precision}"
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
                env=ENV,
                gt_backend=gt_backend,
                hdf5_version=HDF5_VERSION,
                netcdf_version=NETCDF_VERSION,
                num_nodes=(num_nodes := 1),
                num_runs=NUM_RUNS,
                num_tasks_per_node=(num_tasks_per_node := 1),
                num_threads_per_task=7,
                partition=PARTITION,
                python_version=PYTHON_VERSION,
                rocm_version=ROCM_VERSION,
                stack=STACK,
                stack_version=STACK_VERSION,
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
            )


if __name__ == "__main__":
    main()
