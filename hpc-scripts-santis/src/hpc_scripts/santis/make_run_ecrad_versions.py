#!/usr/bin/python3.11
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
from typing import Literal

from hpc_scripts import common
from hpc_scripts.santis import defaults, defs, make_prepare_ecrad_versions

# >>> config: start
BRANCH: str = "solvers-cy49r1"
DACE_DEFAULT_BLOCK_SIZE: str | None = None
ECRAD_ENABLE_CHECKS: bool = True
ECRAD_MODE: Literal["fortran", "gt4py", "validate", "validate_all"] = "gt4py"
ECRAD_NUM_RUNS: int = 0
ECRAD_PRECISION: defs.FloatingPointPrecision = "double"
ECRAD_STENCIL_NAME: str = "ecrad_ecckd_tripleclouds"
ECRAD_STENCIL_VERSION: str = "cy49r1s"
ECRAD_VERBOSE: bool = True
GT_BACKEND: str = "gt:gpu"
NUM_NODES: int = 1
NUM_RUNS: int = 1
NUM_TASKS_PER_NODE: int = 1
NUM_THREADS_PER_TASK: int = 64
REFRESH_PYTHON_VENV: bool = False
# >>> config: end


def core(
    branch: str,
    dace_default_block_size: str | None,
    ecrad_enable_checks: bool,
    ecrad_mode: Literal["fortran", "gt4py", "validate", "validate_all"],
    ecrad_num_runs: int,
    ecrad_precision: defs.FloatingPointPrecision,
    ecrad_stencil_name: str,
    ecrad_stencil_version: str,
    ecrad_verbose: bool,
    gt_backend: str,
    num_nodes: int,
    num_runs: int,
    num_tasks_per_node: int,
    num_threads_per_task: int,
    python_version: defs.PythonVersion,
    refresh_python_venv: bool,
    uenv: defs.UEnv,
) -> str:
    prepare_ecrad_fname = make_prepare_ecrad_versions.core(
        branch, python_version, refresh_python_venv, uenv
    )

    with common.utils.output_file(filename="run_ecrad_versions") as (_, fname):
        common.utils.run(f"source {prepare_ecrad_fname}")

        with common.utils.chdir("$ECRAD"):
            common.utils.export_variable("OMP_NUM_THREADS", num_threads_per_task)
            common.utils.export_variable("OMP_PLACES", "cores")
            common.utils.export_variable("OMP_PROC_BIND", "close")
            # common.utils.export_variable("OMP_DISPLAY_AFFINITY", "True")
            # common.utils.export_variable("GT4PY_EXTRA_COMPILE_ARGS", "'-fbracket-depth=32768'")
            if gt_backend in ["cuda", "dace:gpu", "gt:gpu"]:
                common.utils.export_variable("CUDA_HOST_CXX", "$CXX")
            if dace_default_block_size:
                common.utils.export_variable("DACE_DEFAULT_BLOCK_SIZE", dace_default_block_size)

            srun_options = (
                f"--nodes={num_nodes} --ntasks-per-node={num_tasks_per_node} --gpus-per-task=1"
            )

            common.utils.run(f"srun {srun_options} ecrad_setup --precision={ecrad_precision}")

            match ecrad_mode:
                case "fortran":
                    ecrad_command = (
                        f"ecrad_fortran --name={ecrad_stencil_name} "
                        f"--version={ecrad_stencil_version} --precision={ecrad_precision} "
                        f"--num-runs={ecrad_num_runs} {'--verbose ' if ecrad_verbose else ''}"
                    )
                case "gt4py":
                    ecrad_command = (
                        f"ecrad_gt4py --name={ecrad_stencil_name} "
                        f"--version={ecrad_stencil_version} --precision={ecrad_precision} "
                        f"--num-runs={ecrad_num_runs} {'--verbose ' if ecrad_verbose else ''}"
                        f"--backend={gt_backend} {'--enable-checks' if ecrad_enable_checks else ''}"
                    )
                case "validate":
                    ecrad_command = (
                        f"ecrad_validate --name={ecrad_stencil_name} "
                        f"--version={ecrad_stencil_version} --precision={ecrad_precision} "
                        f"--backend={gt_backend} {'--verbose ' if ecrad_verbose else ''}"
                    )
                case "validate_all":
                    ecrad_command = (
                        f"ecrad_validate_all --version=cy49r1s "
                        f"--precision={ecrad_precision} --backend={gt_backend} "
                        f"{'--verbose ' if ecrad_verbose else ''}"
                    )

            command = f"srun {srun_options} time {ecrad_command}"

            for _ in range(num_runs):
                common.utils.run(command)

    return fname


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--branch", type=str, default=BRANCH)
    parser.add_argument("--dace-default-block-size", type=str, default=DACE_DEFAULT_BLOCK_SIZE)
    parser.add_argument("--ecrad-enable-checks", type=bool, default=ECRAD_ENABLE_CHECKS)
    parser.add_argument("--ecrad-mode", type=str, default=ECRAD_MODE)
    parser.add_argument("--ecrad-num-runs", type=int, default=ECRAD_NUM_RUNS)
    parser.add_argument("--ecrad-precision", type=str, default=ECRAD_PRECISION)
    parser.add_argument("--ecrad-stencil-name", type=str, default=ECRAD_STENCIL_NAME)
    parser.add_argument("--ecrad-stencil-version", type=str, default=ECRAD_STENCIL_VERSION)
    parser.add_argument("--ecrad-verbose", type=bool, default=ECRAD_VERBOSE)
    parser.add_argument("--gt-backend", type=str, default=GT_BACKEND)
    parser.add_argument("--num-nodes", type=int, default=NUM_NODES)
    parser.add_argument("--num-runs", type=int, default=NUM_RUNS)
    parser.add_argument("--num-tasks-per-node", type=int, default=NUM_TASKS_PER_NODE)
    parser.add_argument("--num-threads-per-task", type=int, default=NUM_THREADS_PER_TASK)
    parser.add_argument("--python-version", type=str, default=defs.PythonVersion)
    parser.add_argument("--refresh-python-venv", action="store_true")
    parser.add_argument("--uenv", type=str, default=defaults.UENV)
    args = parser.parse_args()
    with common.utils.output_directory():
        core(**args.__dict__)
