#!/usr/bin/python3.11
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import os

from hpc_scripts import common
from hpc_scripts.santis import defaults, defs, make_build_spack_env, utils

# >>> config: start
BRANCH: str = "cy49r1s-pmap"
# >>> config: end


def core(
    branch: str, python_version: defs.PythonVersion, refresh_python_venv: bool, uenv: defs.UEnv
) -> str:
    with common.utils.output_file(filename="prepare_ecrad_versions") as (_, fname):
        make_build_spack_env.activate_view("ecrad", uenv)

        # set path to ecrad-versions code
        ecrad_root = os.path.join(common.config.APPS_ROOT_DIR, "ecrad-versions")
        if not os.path.exists(ecrad_dir := os.path.join(ecrad_root, branch)):
            common.utils.run(
                f"git clone -b {branch} git@github.com:PMAP-Project/ecRad-versions.git {ecrad_dir}"
            )
        common.utils.export_variable("ECRAD", ecrad_dir)

        utils.setup_gt4py(ecrad_root, uenv)

        with common.utils.chdir(ecrad_dir, restore=False):
            venv_dir = os.path.join(
                ecrad_dir,
                "_venv",
                utils.get_uenv_with_dashes(uenv),
                f"py{python_version.replace('.', '')}",
            )
            common.utils.export_variable("ECRAD_VENV", venv_dir)
            if not os.path.exists(venv_dir):
                refresh_python_venv = True
                utils.setup_uv(uenv)
                common.utils.run(f"uv venv --python=$(which python{python_version}) {venv_dir}")

            common.utils.run(f". {venv_dir}/bin/activate")

            if refresh_python_venv:
                common.utils.run("uv pip install -e .[dev,gpu]")
                common.utils.run("uv pip install 'dace==2.0.0a5'")

    return fname


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--branch", type=str, default=BRANCH)
    parser.add_argument("--python-version", type=str, default=defaults.PYTHON_VERSION)
    parser.add_argument("--refresh-python-venv", action="store_true")
    parser.add_argument("--uenv", type=str, default=defaults.UENV)
    args = parser.parse_args()
    core(**args.__dict__)


if __name__ == "__main__":
    main()
