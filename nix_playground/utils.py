import contextlib
import dataclasses
import os
import pathlib
import typing

from . import constants


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
