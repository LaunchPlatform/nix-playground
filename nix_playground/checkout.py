import contextlib
import json
import logging
import os
import pathlib
import subprocess
import sys
import typing

import click

from .cli import cli
from .environment import Environment
from .environment import pass_env

logger = logging.getLogger(__name__)


PLAYGROUND_DIR = ".nix-playground"
DER_LINK = "der"
PKG_LINK = "pkg"


@contextlib.contextmanager
def switch_cwd(cwd: str | pathlib.Path) -> typing.ContextManager:
    current_cwd = os.getcwd()
    try:
        os.chdir(cwd)
        yield
    finally:
        os.chdir(current_cwd)


@cli.command(name="checkout", help="Checkout nixpkgs source content locally")
@click.argument("PKG_NAME", type=str)
@pass_env
def main(env: Environment, pkg_name: str):
    np_dir = pathlib.Path(PLAYGROUND_DIR)
    np_dir.mkdir(exist_ok=True)

    with switch_cwd(np_dir):
        logger.info("Checkout out package %s ...", pkg_name)
        try:
            package, attr_name = pkg_name.split("#", 1)
            subprocess.check_call(
                [
                    "nix-instantiate",
                    f"<{package}>",
                    "--attr",
                    attr_name,
                    "--add-root",
                    DER_LINK,
                ]
            )
        except subprocess.CalledProcessError:
            logger.error("Failed to instantiate package %s", pkg_name)
            sys.exit(-1)
        der_path = os.readlink(DER_LINK)
        logger.info("Got package der path %s", der_path)
        der_payload = json.loads(
            subprocess.check_output(["nix", "derivation", "show", der_path])
        )
        logger.debug("Der payload: %r", der_payload)
        src = der_payload[der_path]["env"].get("src")
        logger.info("Source of the der %r", src)

        logger.info("Realizing der %s ...", der_path)
        subprocess.check_call(
            [
                "nix-store",
                "--realise",
                "--add-root",
                PKG_LINK,
                der_path,
            ]
        )
