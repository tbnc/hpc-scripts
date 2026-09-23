# -*- coding: utf-8 -*-
from typing import Optional

from hpc_scripts.lumi import defs

ACCOUNT: int = 465000527
ENV: defs.ProgrammingEnvironment = "cray"
GHEX_TRANSPORT_BACKEND: defs.GHEXTransportBackend = "mpi"
HDF5_VERSION: str = "2.1.1"
NCO_VERSION: str = "5.3.9"
NETCDF_VERSION: str = "4.10.0"
PARTITION: defs.Partition = "standard-g"
PYTHON_VERSION: defs.PythonVersion = "3.12"
ROCM_VERSION: str = "6.3.4"
STACK: defs.SoftwareStack = "lumi"
STACK_VERSION: Optional[str] = "25.03"
