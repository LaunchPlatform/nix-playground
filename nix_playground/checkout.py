import itertools
import json
import logging
import os
import pathlib
import shutil
import stat
import subprocess
import sys

import click
import pygit2

from . import constants
from .cli import cli
from .environment import Environment
from .environment import pass_env
from .utils import switch_cwd

logger = logging.getLogger(__name__)


@cli.command(name="checkout", help="Checkout nixpkgs source content locally")
@click.argument("PKG_NAME", type=str)
@pass_env
def main(env: Environment, pkg_name: str):
    np_dir = pathlib.Path(constants.PLAYGROUND_DIR)
    np_dir.mkdir(exist_ok=True)

    (np_dir / constants.PKG_NAME).write_text(pkg_name)

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
                    constants.DER_LINK,
                ]
            )
        except subprocess.CalledProcessError:
            logger.error("Failed to instantiate package %s", pkg_name)
            sys.exit(-1)
        der_path = os.readlink(constants.DER_LINK)
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
                constants.PKG_LINK,
                der_path,
            ]
        )

        subprocess.check_call(
            [
                "nix-store",
                "--realise",
                "--add-root",
                constants.SRC_LINK,
                src,
            ]
        )

    checkout_dir = pathlib.Path(constants.DEFAULT_CHECKOUT_DIR)
    logger.info("Checking out source code from %s to %s", src, checkout_dir)
    shutil.copytree(src, str(checkout_dir))
    checkout_dir.chmod(0o700)

    logger.info("Change file permissions")
    for root, dirs, files in os.walk(checkout_dir):
        for file_name in itertools.chain(files, dirs):
            file_path = pathlib.Path(root) / file_name
            file_stat = file_path.stat()
            file_path.chmod(file_stat.st_mode | stat.S_IWRITE)

    logger.info("Initialize git repo")
    repo = pygit2.init_repository(constants.DEFAULT_CHECKOUT_DIR)

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

    logger.info(
        'The checked out source code for "%s" is now available at "%s", you can go ahead and modify it',
        pkg_name,
        checkout_dir,
    )
    logger.info(
        'Then, you can run "np build" to build the package with the changes in "checkout" folder, '
        'or you can run "np patch" to generate the patch for applying to the upstream'
    )
