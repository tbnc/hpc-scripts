# -*- coding: utf-8 -*-
import os

from hpc_scripts import common
from hpc_scripts.santis import defs


def get_uenv_with_dashes(uenv: defs.UEnv) -> str:
    return uenv.replace("/", "-").replace(":", "-")


def spack_activate_pmap_env() -> None:
    common.utils.run(f"source {defs.spack_root}/share/spack/setup-env.sh")
    common.utils.run(f"spack env activate {defs.spack_root}/_env/pmap")


def spack_activate_ecrad_env(python_version: defs.PythonVersion) -> None:
    common.utils.run(
        f"source {defs.scratch_dir}/ecrad-porting/_spack/c4449cb201/share/spack/setup-env.sh"
    )
    common.utils.run(
        f"spack env activate {defs.scratch_dir}/ecrad-porting/_spack/c4449cb201/_env/"
        f"py{python_version.replace('.', '')}"
    )


def setup_uv(uenv: defs.UEnv) -> None:
    common.utils.export_variable(
        "UV_CACHE_DIR",
        os.path.join(defs.user_project_dir, "_uvcache", uenv.replace("/", "-").replace(":", "-")),
    )


def setup_mpi() -> None:
    common.utils.export_variable("CC", "mpicc")
    common.utils.export_variable("CXX", "mpic++")
    common.utils.export_variable("MPICC", "mpicc")
    common.utils.export_variable("MPICXX", "mpic++")
    common.utils.export_variable("MPICH_GPU_SUPPORT_ENABLED", "1")


def setup_ghex(transport_backend: defs.GHEXTransportBackend) -> None:
    with common.utils.check_argument(
        "transport_backend", transport_backend, defs.valid_ghex_transport_backends
    ):
        common.utils.export_variable("GHEX_TRANSPORT_BACKEND", transport_backend.upper())
        common.utils.export_variable("GHEX_USE_GPU", 1)
        common.utils.export_variable("GHEX_GPU_TYPE", "NVIDIA")
        common.utils.export_variable("GHEX_GPU_ARCH", "90")


def setup_cuda() -> None:
    common.utils.export_variable("CUDA_HOME", "$(spack location -i cuda)")


def setup_gt4py(project_root: str, uenv: defs.UEnv) -> None:
    common.utils.export_variable(
        "GT_CACHE_ROOT",
        (gt_cache_root := os.path.join(project_root, "_gtcache", get_uenv_with_dashes(uenv))),
    )
    common.utils.export_variable("GT4PY_BUILD_CACHE_DIR", gt_cache_root)
    common.utils.export_variable("GT4PY_BUILD_CACHE_LIFETIME", "persistent")

    common.utils.export_variable(
        "GT4PY_EXTRA_COMPILE_ARGS", "'-fconstexpr-ops-limit=1000000000 -Wno-unused-variable'"
    )
    common.utils.export_variable(
        "GT4PY_CARTESIAN_EXTRA_CUDA_COMPILE_ARGS", "'--diag-suppress=1835 --diag-suppress=20012'"
    )

    common.utils.export_variable("DACE_CONFIG", os.path.join(gt_cache_root, ".dace.conf"))
