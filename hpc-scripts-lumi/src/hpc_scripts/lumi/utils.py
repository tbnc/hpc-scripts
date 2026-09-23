# -*- coding: utf-8 -*-
from __future__ import annotations

import os
from typing import TYPE_CHECKING

from hpc_scripts import common, lumi

if TYPE_CHECKING:
    from typing import Optional


def load_stack(stack: lumi.defs.SoftwareStack, stack_version: Optional[str]) -> str:
    with common.utils.check_argument("stack", stack, lumi.defs.valid_software_stacks):
        module = "CrayEnv" if stack == "cray" else stack.upper()
        if stack_version is not None:
            module += f"/{stack_version}"
        common.utils_module.module_load(module)
        return module.replace("/", "-")


def get_partition_type(partition: lumi.defs.Partition) -> str:
    with common.utils.check_argument("partition", partition, lumi.defs.valid_partitions):
        return lumi.defs.PartitionType[partition]


def load_partition(partition: lumi.defs.Partition) -> None:
    with common.utils.check_argument("partition", partition, lumi.defs.valid_partitions):
        partition_type = get_partition_type(partition)
        if partition_type == "gpu":
            common.utils_module.module_load("partition/G")
        else:
            common.utils_module.module_load("partition/C")


def load_cpe(env: lumi.defs.ProgrammingEnvironment, stack_version: Optional[str]) -> str:
    with common.utils.check_argument("env", env, lumi.defs.valid_programming_environments):
        if env == "cray":
            cpe = "cpeCray"
        else:
            cpe = "cpe" + env.upper()
        if stack_version is not None:
            cpe += "-" + stack_version
        common.utils_module.module_load(cpe.replace("-", "/"))
        return cpe


def load_boost(cpe: str, stack_version: str) -> None:
    if stack_version == "24.03":
        boost_version = "1.83.0"
    elif stack_version == "25.03":
        boost_version = "1.88.0"
    else:
        raise RuntimeError(f"Cannot determine boost version for {stack_version=}.")

    common.utils_module.module_load(f"Boost/{boost_version}-{cpe}")


def setup_env(
    env: lumi.defs.ProgrammingEnvironment,
    partition: lumi.defs.Partition,
    stack: lumi.defs.SoftwareStack,
    stack_version: Optional[str],
    load_cdo: bool = False,
) -> str:
    common.utils_module.module_reset()
    load_stack(stack, stack_version)
    load_partition(partition)
    if load_cdo:
        # note(stubbiali): the CDO module could only be built using easybuild for cpeGNU
        common.utils_module.module_load("CDO/2.4.3-cpeGNU-24.03")
    cpe = load_cpe(env, stack_version)
    common.utils.export_variable("CC", "cc")
    common.utils.export_variable("CXX", "CC")
    common.utils.export_variable("MPICC", "cc")
    common.utils.export_variable("MPICXX", "CC")
    return cpe


def load_python(python_version: lumi.defs.PythonVersion) -> str:
    with common.utils.check_argument(
        "python_version", python_version, lumi.defs.valid_python_versions
    ):
        if python_version == "cray-python":
            common.utils_module.module_load("cray-python")
            return "python"
        else:
            # uv-installed python interpreters do not need to be loaded
            return "python" + python_version


def get_subtree(
    env: lumi.defs.ProgrammingEnvironment,
    stack: lumi.defs.SoftwareStack,
    stack_version: Optional[str],
    python_version: Optional[lumi.defs.PythonVersion] = None,
    ghex_transport_backend: Optional[lumi.defs.GHEXTransportBackend] = None,
    rocm_version: Optional[str] = None,
) -> str:
    with common.utils.check_argument("env", env, lumi.defs.valid_programming_environments):
        with common.utils.check_argument("stack", stack, lumi.defs.valid_software_stacks):
            subtree = os.path.join(
                stack + ("-" + stack_version if stack_version else ""),
                env + ("-" + stack_version if stack_version else ""),
            )

            if python_version is not None:
                with common.utils.check_argument(
                    "python_version", python_version, lumi.defs.valid_python_versions
                ):
                    if python_version == "cray-python":
                        subtree = os.path.join(subtree, python_version)
                    else:
                        subtree = os.path.join(subtree, "py" + python_version.replace(".", ""))

            if ghex_transport_backend is not None:
                with common.utils.check_argument(
                    "ghex_transport_backend",
                    ghex_transport_backend,
                    lumi.defs.valid_ghex_transport_backends,
                ):
                    subtree = os.path.join(subtree, ghex_transport_backend)

            if rocm_version is not None:
                subtree = os.path.join(subtree, "rocm-" + rocm_version)

            return subtree


def setup_uv(subtree: str) -> None:
    common.utils.export_variable(
        "UV_CACHE_DIR", os.path.join(common.config.APPS_ROOT_DIR, "_uvcache", subtree)
    )


def setup_hip(rocm_version: str) -> None:
    common.utils.export_variable("CUDA_HOME", f"/opt/rocm-{rocm_version}")
    common.utils.export_variable("CUPY_ACCELERATORS", "cub")
    common.utils.export_variable("CUPY_INSTALL_USE_HIP", 1)
    common.utils.export_variable("GHEX_USE_GPU", 1)
    common.utils.export_variable("GHEX_GPU_TYPE", "AMD_LEGACY")
    common.utils.export_variable("GHEX_GPU_ARCH", "gfx90a")
    common.utils.export_variable("GT4PY_USE_HIP", 1)
    common.utils.export_variable("HCC_AMDGPU_TARGET", "gfx90a")
    common.utils.export_variable(
        "HIPCC_COMPILE_FLAGS_APPEND", "'--offload-arch=gfx90a $(CC --cray-print-opts=cflags)'"
    )
    common.utils.export_variable("HIPCC_LINK_FLAGS_APPEND", "$(CC --cray-print-opts=libs)")
    common.utils.export_variable("ROCM_HOME", f"/opt/rocm-{rocm_version}")


def get_srun_options(
    num_nodes: int,
    num_tasks_per_node: int,
    num_threads_per_task: int,
    partition: lumi.defs.Partition,
    gt_backend: Optional[str] = None,
) -> list[str]:
    srun_options = [
        f"--nodes={num_nodes}",
        f"--ntasks-per-node={num_tasks_per_node}",
        "--distribution=block:block",
    ]
    if (
        get_partition_type(partition) == "gpu"
        and gt_backend in ["cuda", "dace:gpu", "gt:gpu"]
        and num_tasks_per_node == 8
    ):
        # srun_options.append("--cpu-bind=map_cpu:49,57,17,25,1,9,33,41")
        srun_options.append(
            "--cpu-bind=mask_cpu:fe000000000000,fe00000000000000,"
            "fe0000,fe000000,fe,fe00,fe00000000,fe0000000000"
        )
    else:
        srun_options += [f"--cpus-per-task={num_threads_per_task}", "--cpu-bind=cores"]
    return srun_options
