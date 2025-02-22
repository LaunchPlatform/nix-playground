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
from .utils import parse_pkg
from .utils import switch_cwd

logger = logging.getLogger(__name__)


@cli.command(name="checkout", help="Checkout nixpkgs source content locally")
@click.argument("PKG_NAME", type=str)
@click.option("-c", "--checkout-to", type=click.Path(exists=False, writable=True))
@pass_env
def main(env: Environment, pkg_name: str, checkout_to: str | None):
    np_dir = pathlib.Path(constants.PLAYGROUND_DIR)
    np_dir.mkdir(exist_ok=True)
    (np_dir / constants.PKG_NAME).write_text(pkg_name)

    if checkout_to is None:
        checkout_dir = pathlib.Path(constants.DEFAULT_CHECKOUT_DIR)
    else:
        checkout_dir = pathlib.Path(checkout_to)

    package = parse_pkg(pkg_name)

    with switch_cwd(np_dir):
        logger.info("Checkout out package %s ...", pkg_name)
        try:
            subprocess.check_call(
                [
                    "nix-instantiate",
                    f"<{package.flake}>",
                    "--attr",
                    package.attr_name,
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
        patch_files = []
        patches = der_payload[der_path]["env"].get("patches", None)
        if patches is not None:
            patch_files = patches.split(" ")
            logger.info("Found package patches %s", patch_files)

    logger.info("Checking out source code from %s to %s", src, checkout_dir)
    shutil.copytree(src, str(checkout_dir))
    checkout_dir.chmod(0o700)
    # make a link for the operation later
    checkout_link = np_dir / constants.CHECKOUT_LINK
    checkout_link.unlink(missing_ok=True)
    checkout_link.absolute().symlink_to(checkout_dir.absolute())

    logger.info("Change file permissions")
    for root, dirs, files in os.walk(checkout_dir):
        for file_name in itertools.chain(files, dirs):
            file_path = pathlib.Path(root) / file_name
            file_stat = file_path.stat()
            file_path.chmod(file_stat.st_mode | stat.S_IWRITE)

    logger.info("Initialize git repo")
    repo = pygit2.init_repository(checkout_dir)

    with switch_cwd(checkout_dir):
        index = repo.index
        index.add_all()
        index.write()
        ref = "HEAD"
        author = pygit2.Signature(
            name=constants.CHECKOUT_GIT_AUTHOR_NAME,
            email=constants.CHECKOUT_GIT_AUTHOR_EMAIL,
        )
        tree = index.write_tree()
        current_commit = repo.create_commit(
            ref,
            author,
            author,
            "Initial commit",
            tree,
            [],
        )

        if patch_files:
            for patch_file in patch_files:
                logger.info("Making a new commit from patch file %s", patch_file)
                patch_file = pathlib.Path(patch_file)
                diff = pygit2.Diff.parse_diff(patch_file.read_bytes())
                repo.apply(diff)
                index = repo.index
                index.add_all()
                index.write()
                tree = index.write_tree()
                current_commit = repo.create_commit(
                    ref,
                    author,
                    author,
                    f"Applying package patch file {patch_file}",
                    tree,
                    [current_commit],
                )

    logger.info(
        'The checked out source code for "%s" is now available at "%s", you can go ahead and modify it',
        pkg_name,
        checkout_dir,
    )
    logger.info(
        'Then, you can run "np build" to build the package with the changes in "checkout" folder, '
        'or you can run "np patch" to generate the patch for applying to the upstream'
    )
