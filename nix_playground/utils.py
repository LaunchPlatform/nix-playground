import contextlib
import os
import pathlib
import typing


@contextlib.contextmanager
def switch_cwd(cwd: str | pathlib.Path) -> typing.ContextManager:
    current_cwd = os.getcwd()
    try:
        os.chdir(cwd)
        yield
    finally:
        os.chdir(current_cwd)
