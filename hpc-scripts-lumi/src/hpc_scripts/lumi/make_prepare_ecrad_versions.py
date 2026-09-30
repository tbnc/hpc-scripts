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
    make_build_nco,
    make_build_netcdf,
    utils,
)

if TYPE_CHECKING:
    from typing import Optional


# >>> config: start
BRANCH: str = "main"
# >>> config: end


def core(
    branch: str,
    env: defs.ProgrammingEnvironment,
    hdf5_version: str,
    nco_version: str,
    netcdf_version: str,
    partition: defs.Partition,
    python_version: defs.PythonVersion,
    rocm_version: str,
    stack: defs.SoftwareStack,
    stack_version: Optional[str],
) -> str:
    with common.utils.output_file(filename="prepare_ecrad_versions") as (_, fname):
        # clear environment and load relevant modules
        cpe = utils.setup_env(env, partition, stack, stack_version)
        utils.load_boost(cpe, stack_version)
        utils.load_python(python_version)
        partition_type = utils.get_partition_type(partition)
        if partition_type == "gpu":
            common.utils_module.module_load(f"rocm/{rocm_version}")

        # set path to ecrad-versions code, cloning the repo if the directory does not exist yet
        ecrad_dir = os.path.join(common.config.APPS_ROOT_DIR, "ecrad-versions", branch)
        if not os.path.exists(ecrad_dir):
            common.utils.run(
                f"git clone -b {branch} git@github.com:PMAP-Project/ecRad-versions.git {ecrad_dir}"
            )
        common.utils.export_variable("ECRAD", ecrad_dir)
        subtree = utils.get_subtree(env, stack, stack_version)
        venv_dir = os.path.join(ecrad_dir, "_venv", subtree)
        common.utils.export_variable("ECRAD_VENV", venv_dir)

        # low-level GT4Py & DaCe config
        utils.setup_gt4py("ecrad-versions", subtree)

        # set/fix HIP-related variables
        if partition_type == "gpu":
            utils.setup_hip(rocm_version)

        # path to custom build of HDF5, NetCDF-C and NCO
        # note: NCO provides the utility ncks used in scripts/setup_optical_data.sh
        make_build_hdf5.setup(env, stack, stack_version, hdf5_version)
        make_build_netcdf.setup(env, stack, stack_version, hdf5_version, netcdf_version)
        make_build_nco.setup(env, stack, stack_version, hdf5_version, netcdf_version, nco_version)

        # configure uv
        utils.setup_uv(subtree)

        # jump into project source directory
        with common.utils.chdir(ecrad_dir, restore=False):
            if not os.path.exists(venv_dir):
                # create virtual environment if it does not exist yet
                common.utils.run(f"uv venv --prompt={subtree} {venv_dir}")
                common.utils.run(f"source {venv_dir}/bin/activate")
                common.utils.run("uv pip install -e .[dev,gpu,test]")
            else:
                # activate virtual environment
                common.utils.run(f"source {venv_dir}/bin/activate")

    return fname


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--branch", type=str, default=BRANCH)
    parser.add_argument("--env", type=str, default=defaults.ENV)
    parser.add_argument("--hdf5-version", type=str, default=defaults.HDF5_VERSION)
    parser.add_argument("--nco-version", type=str, default=defaults.NCO_VERSION)
    parser.add_argument("--netcdf-version", type=str, default=defaults.NETCDF_VERSION)
    parser.add_argument("--partition", type=str, default=defaults.PARTITION)
    parser.add_argument("--python-version", type=str, default=defaults.PYTHON_VERSION)
    parser.add_argument("--rocm-version", type=str, default=defaults.ROCM_VERSION)
    parser.add_argument("--stack", type=str, default=defaults.STACK)
    parser.add_argument("--stack-version", type=str, default=defaults.STACK_VERSION)
    args = parser.parse_args()
    core(**args.__dict__)


if __name__ == "__main__":
    main()
