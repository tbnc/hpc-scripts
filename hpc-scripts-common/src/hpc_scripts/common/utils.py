# -*- coding: utf-8 -*-
from __future__ import annotations

import contextlib
import dataclasses
import os
import shutil
import subprocess
import tempfile
from typing import TYPE_CHECKING

from hpc_scripts.common import config

if TYPE_CHECKING:
    from typing import Any, Optional


OUTPUT_DIRECTORY_REGISTRY = []
OUTPUT_FILE_REGISTRY = []


@contextlib.contextmanager
def output_directory(path: Optional[str] = None):
    assert len(OUTPUT_DIRECTORY_REGISTRY) <= 1
    try:
        if len(OUTPUT_DIRECTORY_REGISTRY) > 0:
            final_cleanup = False
            yield OUTPUT_DIRECTORY_REGISTRY[-1]
        else:
            final_cleanup = True
            if path is not None:
                if not os.path.isabs(path):
                    path = os.path.join(config.SCRIPTS_ROOT_DIR, path)
                if os.path.exists(path):
                    shutil.rmtree(path)
                    print(f"hpc-scripts: overwrite {path}")
                else:
                    print(f"hpc-scripts: create {path}")
                os.makedirs(path)
            else:
                os.makedirs(
                    parent_dir := os.path.join(config.SCRIPTS_ROOT_DIR, "_tmp"), exist_ok=True
                )
                path = os.path.abspath(tempfile.mkdtemp(dir=parent_dir))
                os.makedirs(path, exist_ok=True)
                print(f"hpc-scripts: create {path}")
            OUTPUT_DIRECTORY_REGISTRY.append(path)
            yield path
    finally:
        if final_cleanup:
            OUTPUT_DIRECTORY_REGISTRY.pop()


@contextlib.contextmanager
def output_file(filename: Optional[str] = None):
    if filename is not None:
        basename, ext = os.path.splitext(filename)
        ext = ext or ".sh"
        if len(OUTPUT_DIRECTORY_REGISTRY) > 0:
            fname = os.path.abspath(os.path.join(OUTPUT_DIRECTORY_REGISTRY[-1], basename + ext))
        else:
            fname = os.path.join(config.SCRIPTS_ROOT_DIR, basename + ext)
        os.makedirs(os.path.dirname(fname), exist_ok=True)

        try:
            with open(fname, "w") as f:
                OUTPUT_FILE_REGISTRY.append(f)
                if ext == ".sh":
                    f.write("#!/bin/bash -l\n\n")
                yield f, fname
        finally:
            print(f"hpc-scripts: write {fname}")
            OUTPUT_FILE_REGISTRY.pop()


def run(*args: str, split: bool = False, verbose: bool = False) -> None:
    split_args = [item for arg in args for item in arg.split(" ")]
    if split:
        command = split_args[0]
        for arg in split_args[1:]:
            command += " \\\n    " + arg
    else:
        command = " ".join(split_args)
    if verbose:
        print(command)
    if len(OUTPUT_FILE_REGISTRY) > 0:
        OUTPUT_FILE_REGISTRY[-1].write(command + "\n")
    else:
        subprocess.run(command, capture_output=True, check=True, shell=True)


class InvalidArgumentError(Exception):
    def __init__(self, name: str, token: str, options: list[str]):
        options = [f"`{opt}`" for opt in options]
        msg = (
            f"Invalid value `{token}` for parameter `{name}`. "
            f"Available options: {', '.join(options)}."
        )
        super().__init__(msg)


@contextlib.contextmanager
def check_argument(name, token, options):
    if token not in options:
        raise InvalidArgumentError(name, token, options)
    try:
        yield token
    finally:
        pass


def export_variable(name: str, value: Any) -> None:
    run(f"export {name}={value!s}")


def append_to_path(path: str, value: Any) -> None:
    run(f"{path}={value!s}:${path}")


@contextlib.contextmanager
def chdir(dirname: str, restore: bool = True) -> None:
    try:
        run(f"pushd {dirname}")
        yield None
    finally:
        if restore:
            run("popd")


@dataclasses.dataclass
class ThreadsLayout:
    num_nodes: int
    num_tasks_per_node: int
    num_threads_per_task: int

    @property
    def num_tasks(self) -> int:
        return self.num_nodes * self.num_tasks_per_node
