#!/opt/cray/pe/python/3.11.7/bin/python
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import os
from typing import TYPE_CHECKING

from hpc_scripts import common
from hpc_scripts.lumi import (
    defaults,
    defs,
    make_build_hdf5,
    make_build_netcdf,
    make_prepare_mpi,
    utils,
)

if TYPE_CHECKING:
    from typing import Literal, Optional


# >>> config: start
BRANCH: str = "main"
PROJECT: Literal["pmap", "pmap-real_cases-shared", "pmap-snapshots"] = "pmap"
# >>> config: end


def core(
    branch: str,
    env: defs.ProgrammingEnvironment,
    ghex_transport_backend: defs.GHEXTransportBackend,
    hdf5_version: str,
    netcdf_version: str,
    partition: defs.Partition,
    project: str,
    python_version: defs.PythonVersion,
    refresh_python_venv: bool,
    rocm_version: str,
    stack: defs.SoftwareStack,
    stack_version: Optional[str],
) -> tuple[str, str]:
    project_with_underscores = project.replace("-", "_")
    with common.utils.output_file(filename=f"prepare_{project_with_underscores}") as (_, fname):
        # clear environment and load relevant modules
        cpe = utils.setup_env(env, partition, stack, stack_version)
        common.utils_module.module_load("buildtools")
        utils.load_boost(cpe, stack_version)
        python = utils.load_python(python_version)
        partition_type = utils.get_partition_type(partition)
        if partition_type == "gpu":
            common.utils_module.module_load(f"rocm/{rocm_version}")

        # set path to PMAP code, cloning the repo if the directory does not exist
        pmap_dir = os.path.join(common.config.APPS_ROOT_DIR, project, branch)
        if not os.path.exists(pmap_dir):
            common.utils.run(
                f"git clone -b {branch} git@github.com:PMAP-Project/"
                f"{project.replace('pmap', 'PMAP')}.git {pmap_dir}"
            )
        common.utils.export_variable(project_with_underscores.upper(), pmap_dir)
        pmap_subtree = utils.get_subtree(
            env,
            stack,
            stack_version,
            python_version,
            ghex_transport_backend=ghex_transport_backend,
            rocm_version=rocm_version if partition_type == "gpu" else None,
        )
        pmap_venv_dir = os.path.join(pmap_dir, "_venv", pmap_subtree)
        common.utils.export_variable(f"{project_with_underscores.upper()}_VENV", pmap_venv_dir)

        # low-level GT4Py, DaCe and GHEX config
        gt_cache_root = os.path.join(common.config.APPS_ROOT_DIR, project, "_gtcache", pmap_subtree)
        common.utils.export_variable("GT_CACHE_ROOT", gt_cache_root)
        common.utils.export_variable("GT_CACHE_DIR_NAME", ".gt_cache")
        common.utils.export_variable("GT4PY_EXTRA_COMPILE_ARGS", "'-fbracket-depth=4096'")
        common.utils.export_variable(
            "GT4PY_CARTESIAN_EXTRA_CUDA_COMPILE_ARGS", "'-fbracket-depth=4096'"
        )
        common.utils.export_variable("DACE_CONFIG", os.path.join(gt_cache_root, ".dace.conf"))

        # set/fix HIP-related variables
        if partition_type == "gpu":
            utils.setup_hip(rocm_version)

        # configure MPICH
        prepare_mpi_fname = make_prepare_mpi.core(ghex_transport_backend, partition)
        common.utils.run(f". {prepare_mpi_fname}")

        # configure HDF5 and NetCDF-C
        make_build_hdf5.setup(env, stack, stack_version, hdf5_version)
        make_build_netcdf.setup(env, stack, stack_version, hdf5_version, netcdf_version)

        # jump into project source directory
        with common.utils.chdir(pmap_dir, restore=False):
            if not os.path.exists(pmap_venv_dir):
                # create virtual environment if it does not exist yet
                refresh_python_venv = True
                common.utils.run(
                    f"uv venv --python={python} --prompt={pmap_subtree} {pmap_venv_dir}"
                )

            # activate venv
            common.utils.run(f"source {pmap_venv_dir}/bin/activate")

            # install the model with all its python dependencies
            if refresh_python_venv:
                common.utils.run("uv pip install --prerelease=allow -e .[dev,gpu,mpi-test]")

    return fname


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--branch", type=str, default=BRANCH)
    parser.add_argument("--env", type=str, default=defaults.ENV)
    parser.add_argument(
        "--ghex-transport-backend", type=str, default=defaults.GHEX_TRANSPORT_BACKEND
    )
    parser.add_argument("--hdf5-version", type=str, default=defaults.HDF5_VERSION)
    parser.add_argument("--netcdf-version", type=str, default=defaults.NETCDF_VERSION)
    parser.add_argument("--partition", type=str, default=defaults.PARTITION)
    parser.add_argument("--project", type=str, default=PROJECT)
    parser.add_argument("--python-version", type=str, default=defaults.PYTHON_VERSION)
    parser.add_argument("--refresh-python-venv", action="store_true")
    parser.add_argument("--rocm-version", type=str, default=defaults.ROCM_VERSION)
    parser.add_argument("--stack", type=str, default=defaults.STACK)
    parser.add_argument("--stack-version", type=str, default=defaults.STACK_VERSION)
    args = parser.parse_args()
    core(**args.__dict__)


if __name__ == "__main__":
    main()
