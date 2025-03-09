import contextlib
import dataclasses
import io
import logging
import os
import pathlib
import subprocess
import sys
import tarfile
import typing

import pygit2

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


def strip_path(strip_count: int, tar: tarfile.TarFile):
    for member in tar.getmembers():
        member.path = member.path.split("/", strip_count)[-1]
        yield member


def extract_tar(
    input_file: io.BytesIO, mode: str = "r:gz", strip_path_count: int | None = None
):
    with tarfile.open(fileobj=input_file, mode=mode) as tar_file:
        extra_kwargs = {}
        if strip_path_count:
            extra_kwargs["members"] = strip_path(strip_path_count, tar_file)
        if hasattr(tarfile, "data_filter"):
            tar_file.extractall(filter="data", **extra_kwargs)
        else:
            logger.warning("Performing unsafe tar file extracting")
            tar_file.extractall(**extra_kwargs)


def apply_patch(
    repo: pygit2.Repository,
    patch_file: pathlib.Path,
    patch_bin: pathlib.Path | None = None,
):
    # TODO: ideally, we should support patch file in different formats, like what nixpkg's setup.sh provides.
    #       https://github.com/NixOS/nixpkgs/blob/09e25be882ef7751b2e4bbc3aa4e2df1c4613558/pkgs/stdenv/generic/setup.sh#L1386C1-L1400C13
    #       however, not sure how common these type of patches files are. Let's ignore it for now, and let the user
    #       report the issues and implement it if that's really needed
    if patch_file.suffix in {".gz", ".bz2", ".xz", ".lzma"}:
        logger.error(
            "Currently compressed patch file is not supported yet, please see the issue https://github.com/LaunchPlatform/nix-playground/issues/FIXME to learn more"
        )
        raise

    diff = pygit2.Diff.parse_diff(patch_file.read_bytes())
    try:
        repo.apply(diff)
    except pygit2.GitError as exc:
        logger.info(
            "Failed to patch with git, fall back to use patch command instead. Error: %s",
            exc,
        )
        if patch_bin is None:
            logger.error(
                "Need to provide patch command line executable via --patch-bin or have it in the PATH"
            )
            sys.exit(-1)
        with switch_cwd(repo.path):
            subprocess.check_call([patch_bin, "-i", str(patch_file), "-p1"])
