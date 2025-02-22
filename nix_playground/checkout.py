import contextlib
import json
import logging
import os
import pathlib
import shutil
import stat
import subprocess
import sys
import typing

import click
import pygit2

from .cli import cli
from .constants import DEFAULT_CHECKOUT_DIR
from .constants import DER_LINK
from .constants import PKG_LINK
from .constants import PLAYGROUND_DIR
from .constants import SRC_LINK
from .environment import Environment
from .environment import pass_env

logger = logging.getLogger(__name__)


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

        subprocess.check_call(
            [
                "nix-store",
                "--realise",
                "--add-root",
                SRC_LINK,
                src,
            ]
        )

    checkout_dir = pathlib.Path(DEFAULT_CHECKOUT_DIR)
    logger.info("Checking out source code from %s to %s", src, checkout_dir)
    shutil.copytree(src, str(checkout_dir))
    checkout_dir.chmod(0o700)

    logger.info("Change file permissions")
    with os.scandir(checkout_dir) as it:
        for entry in it:
            file_stat = entry.stat()
            pathlib.Path(entry.path).chmod(file_stat.st_mode | stat.S_IWRITE)

    logger.info("Initialize git repo")
    repo = pygit2.init_repository(DEFAULT_CHECKOUT_DIR)

    with switch_cwd(checkout_dir):
        index = repo.index
        index.add_all()
        index.write()
        ref = "HEAD"
        author = pygit2.Signature("nix-playground", "noreply@launchplatform.com")
        message = "Initial commit"
        tree = index.write_tree()
        parents = []
        repo.create_commit(ref, author, author, message, tree, parents)
