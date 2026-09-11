#!/usr/bin/python3.11
# -*- coding: utf-8 -*-
from __future__ import annotations

import os

from hpc_scripts import common
from hpc_scripts.santis import defs, utils


def _get_relative_build_dir(project: str, uenv: defs.UEnv) -> str:
    return os.path.join(utils.get_uenv_with_dashes(uenv), project)


def _get_build_dir(project: str, uenv: defs.UEnv) -> str:
    return os.path.join(defs.uenv_spack_builds_root, _get_relative_build_dir(project, uenv))


def activate_view(project: str, uenv: defs.UEnv) -> None:
    common.utils.run(f". {_get_build_dir(project, uenv)}/view/activate.sh")


def core(project: str, specs: tuple[str, ...], uenv: defs.UEnv, clear: bool = False) -> str:
    with common.utils.output_file(filename=f"build_spack_env_{project.replace('-', '_')}"):
        build_dir = _get_build_dir(project, uenv)
        if clear:
            common.utils.run(f"rm -rf {build_dir}")
        common.utils.run(f"uenv-spack {build_dir} --uarch=gh200 --name={project}")

        with common.utils.output_file(
            filename=f"spack/{_get_relative_build_dir(project, uenv)}/spack.yaml"
        ) as (_, spack_yaml):
            spec_list = "\n".join("    - " + spec for spec in specs)
            common.utils.run(
                f"""spack:
  include:
    - {build_dir}/config/user
    - {build_dir}/config/system
  config:
    deprecated: true
  concretizer:
    unify: when_possible
    reuse: true
  specs:
{spec_list}
  packages:
    all:
      variants: [ '+mpi', '+cuda', 'cuda_arch=90']
    mpi:
      require: 'cray-mpich'
  view:
    # https://spack.readthedocs.io/en/latest/environments.html#advanced-view-configuration
    default:
      # one of (run, roots, all)
      link: run
      root: {build_dir}/store/env/{project}
      projections:
        python: '{{name}}@{{version}}'"""
            )

        common.utils.run(f"mv {spack_yaml} {build_dir}/env")
        common.utils.run(f". {build_dir}/build")

        activate_view(project, uenv)
