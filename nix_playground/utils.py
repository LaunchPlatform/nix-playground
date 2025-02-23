import contextlib
import dataclasses
import io
import logging
import os
import pathlib
import sys
import tarfile
import typing

from . import constants

logger = logging.getLogger(__name__)


@dataclasses.dataclass(frozen=True)
class Package:
    flake: str
    attr_name: str


@contextlib.contextmanager
def switch_cwd(cwd: str | pathlib.Path) -> typing.ContextManager:
    current_cwd = os.getcwd()
    try:
        os.chdir(cwd)
        yield
    finally:
        os.chdir(current_cwd)


def parse_pkg(pkg_name: str) -> Package:
    if "#" not in pkg_name:
        return Package(flake=constants.DEFAULT_FLAKE, attr_name=pkg_name)
    flake, attr_name = pkg_name.split("#", 1)
    return Package(flake=flake, attr_name=attr_name)


def ensure_np_dir() -> pathlib.Path:
    np_dir = pathlib.Path(constants.PLAYGROUND_DIR)
    if not np_dir.exists():
        logger.info("No checkout found in the current folder")
        sys.exit(-1)
    return np_dir


def extract_tar(input_file: io.BytesIO, mode: str = "r:gz"):
    with tarfile.open(fileobj=input_file, mode="r:gz") as tar_file:
        if hasattr(tarfile, "data_filter"):
            tar_file.extractall(filter="data")
        else:
            logger.warning("Performing unsafe tar file extracting")
            tar_file.extractall()
