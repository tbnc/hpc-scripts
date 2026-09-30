#!/opt/cray/pe/python/3.11.7/bin/python
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import os
from typing import TYPE_CHECKING

from hpc_scripts import common
from hpc_scripts.lumi import defaults, defs, make_build_hdf5, make_build_netcdf, utils

if TYPE_CHECKING:
    from typing import Optional


def _get_dir(version: str) -> str:
    return os.path.join(common.config.APPS_ROOT_DIR, "nco", version)


def _get_build_dir(nco_dir: str, subtree: str, hdf5_version: str, netcdf_version: str) -> str:
    return os.path.join(
        nco_dir, "build", subtree, f"hdf5-{hdf5_version}", f"netcdf-{netcdf_version}"
    )


def _setup(build_dir: str) -> None:
    common.utils.export_variable("NCO_ROOT", build_dir)
    common.utils.export_variable("NCO_DIR", build_dir)
    common.utils.append_to_path("PATH", os.path.join(build_dir, "bin"))


def setup(
    env: defs.ProgrammingEnvironment,
    stack: defs.SoftwareStack,
    stack_version: Optional[str],
    hdf5_version: str,
    netcdf_version: str,
    version: str,
) -> None:
    _setup(
        build_dir=_get_build_dir(
            nco_dir=_get_dir(version),
            subtree=utils.get_subtree(env, stack, stack_version),
            hdf5_version=hdf5_version,
            netcdf_version=netcdf_version,
        )
    )


def core(
    env: defs.ProgrammingEnvironment,
    hdf5_version: str,
    netcdf_version: str,
    partition: defs.Partition,
    stack: defs.SoftwareStack,
    stack_version: Optional[str],
    version: str,
) -> None:
    with common.utils.output_file(filename="build_nco"):
        utils.setup_env(env, partition, stack, stack_version)
        common.utils_module.module_load("buildtools")

        with common.utils.chdir(common.config.APPS_ROOT_DIR):
            nco_dir = _get_dir(version)
            if not os.path.exists(nco_dir):
                common.utils.run("mkdir -p nco")
                common.utils.run(f"wget https://github.com/nco/nco/archive/{version}.tar.gz")
                common.utils.run(f"tar xvzf {version}.tar.gz")
                common.utils.run(f"mv nco-{version} {nco_dir}")
                common.utils.run(f"rm -rf {version}.tar.gz")

            with common.utils.chdir(nco_dir):
                make_build_hdf5.setup(env, stack, stack_version, hdf5_version)
                make_build_netcdf.setup(env, stack, stack_version, hdf5_version, netcdf_version)

                hdf5_root = make_build_hdf5.get_install_dir(env, stack, stack_version, hdf5_version)
                netcdf_root = make_build_netcdf.get_install_dir(
                    env, stack, stack_version, hdf5_version, netcdf_version
                )
                common.utils.export_variable("NETCDF_INC", os.path.join(netcdf_root, "include"))
                common.utils.export_variable("NETCDF_LIB", os.path.join(netcdf_root, "lib"))
                common.utils.append_to_path("LD_LIBRARY_PATH", os.path.join(hdf5_root, "lib"))

                subtree = utils.get_subtree(env, stack, stack_version)
                build_dir = _get_build_dir(nco_dir, subtree, hdf5_version, netcdf_version)
                common.utils.run(f"rm -rf {build_dir}")
                common.utils.run(
                    f"LDFLAGS='-L{os.path.join(hdf5_root, 'lib')} -lcurl -lhdf5 -lhdf5_hl -lz'",
                    "./configure",
                    f"--prefix={build_dir}",
                    "--enable-udunits=no",  # disable units support for now
                    "--enable-udunits2=no",  # disable units support for now
                )
                common.utils.run("make -j 8 install")

                _setup(build_dir)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", type=str, default=defaults.ENV)
    parser.add_argument("--hdf5-version", type=str, default=defaults.HDF5_VERSION)
    parser.add_argument("--netcdf-version", type=str, default=defaults.NETCDF_VERSION)
    parser.add_argument("--partition", type=str, default=defaults.PARTITION)
    parser.add_argument("--stack", type=str, default=defaults.STACK)
    parser.add_argument("--stack-version", type=str, default=defaults.STACK_VERSION)
    parser.add_argument("--version", type=str, default=defaults.NCO_VERSION)
    args = parser.parse_args()
    core(**args.__dict__)


if __name__ == "__main__":
    main()
