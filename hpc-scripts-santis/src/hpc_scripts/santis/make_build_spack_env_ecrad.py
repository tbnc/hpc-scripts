#!/usr/bin/python3.11
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse

from hpc_scripts.santis import defaults, make_build_spack_env


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--uenv", type=str, default=defaults.UENV)
    parser.add_argument("--clear", action="store_true")
    args = parser.parse_args()
    make_build_spack_env.core(
        **args.__dict__,
        project="ecrad",
        specs=(
            "boost",
            "cuda@13",
            "gcc",
            "hdf5",
            "libffi",
            "nco",
            "netcdf-c",
            "netcdf-fortran",
            "python@3.11",
            "python@3.12",
            "python@3.13",
            "python@3.14",
        ),
    )


if __name__ == "__main__":
    main()
