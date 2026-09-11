#!/usr/bin/python3.11
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import os

from hpc_scripts import common
from hpc_scripts.santis import defaults, defs, make_build_spack_env, utils

# >>> config: start
BRANCH: str = "main"
# >>> config: end


def core(
    branch: str,
    ghex_transport_backend: defs.GHEXTransportBackend,
    python_version: defs.PythonVersion,
    refresh_python_venv: bool,
    uenv: defs.UEnv,
) -> str:
    with common.utils.output_file(filename="prepare_pmap") as (_, fname):
        make_build_spack_env.activate_view("pmap", uenv)

        utils.setup_mpi()
        utils.setup_ghex(ghex_transport_backend)
        utils.setup_cuda()

        pmap_root = os.path.join(common.config.APPS_ROOT_DIR, "pmap")
        if not os.path.exists(pmap_dir := os.path.join(pmap_root, branch)):
            common.utils.run(
                f"git clone -b {branch} git@github.com:PMAP-Project/PMAP.git {pmap_dir}"
            )
        common.utils.export_variable("PMAP", pmap_dir)

        utils.setup_gt4py(pmap_root, uenv)

        with common.utils.chdir(pmap_dir, restore=False):
            venv_dir = os.path.join(
                pmap_dir,
                "_venv",
                utils.get_uenv_with_dashes(uenv),
                ghex_transport_backend,
                f"py{python_version.replace('.', '')}",
            )
            common.utils.export_variable("PMAP_VENV", venv_dir)

            if not os.path.exists(venv_dir):
                refresh_python_venv = True
                utils.setup_uv(uenv)
                common.utils.run(f"uv venv --python=$(which python{python_version}) {venv_dir}")

            common.utils.run(f". {venv_dir}/bin/activate")

            if refresh_python_venv:
                common.utils.run(
                    f"uv pip install --prerelease=allow -e "
                    f".[dev,gpu{'-cuda13x' if python_version < '3.14' else ''},ice4,mpi-test]"
                )
                common.utils.run("uv pip install 'dace==2.0.0a5'")

    return fname


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--branch", type=str, default=BRANCH)
    parser.add_argument(
        "--ghex-transport-backend", type=str, default=defaults.GHEX_TRANSPORT_BACKEND
    )
    parser.add_argument("--python-version", type=str, default=defaults.PYTHON_VERSION)
    parser.add_argument("--refresh-python-venv", action="store_true")
    parser.add_argument("--uenv", type=str, default=defaults.UENV)
    args = parser.parse_args()
    core(**args.__dict__)


if __name__ == "__main__":
    main()
