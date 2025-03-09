import itertools
import json
import logging
import mimetypes
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
from .utils import apply_patch
from .utils import extract_tar
from .utils import switch_cwd

logger = logging.getLogger(__name__)


@cli.command(name="checkout", help="Checkout nixpkgs source content locally")
@click.argument("PKG_NAME", type=str)
@click.option(
    "-c",
    "--checkout-to",
    type=click.Path(exists=False, writable=True),
    default=constants.DEFAULT_CHECKOUT_DIR,
    help="The folder to checkout the source code to.",
    show_default=True,
)
@pass_env
def main(env: Environment, pkg_name: str, checkout_to: str):
    np_dir = pathlib.Path(constants.PLAYGROUND_DIR)
    np_dir.mkdir(exist_ok=True)
    (np_dir / constants.PKG_NAME).write_text(pkg_name)

    checkout_dir = pathlib.Path(checkout_to)

    logger.info("Checkout out package %s ...", pkg_name)
    with switch_cwd(np_dir):
        try:
            drv_payloads = json.loads(
                subprocess.check_output(
                    [
                        "nix",
                        "derivation",
                        "show",
                        pkg_name,
                    ]
                )
            )
            logger.debug("Der payloads: %r", drv_payloads)
            if len(drv_payloads) != 1:
                raise ValueError("Expected only one der in the payload")

            drv_json_file = pathlib.Path(constants.DRV_JSON_FILE)
            with drv_json_file.open("wt") as fo:
                json.dump(drv_payloads, fo)

            drv_path = pathlib.Path(list(drv_payloads.keys())[0])
            drv_payload = drv_payloads[str(drv_path)]
        except subprocess.CalledProcessError:
            logger.error("Failed to fetch package der info %s", pkg_name)
            sys.exit(-1)
        logger.info("Got package der path %s", drv_path)

        src = drv_payload["env"].get("src")
        logger.info("Source of the der %r", src)
        if src is None:
            logger.error("This package has no source to patch")
            sys.exit(-1)

        logger.info("Realizing der %s ...", drv_path)
        subprocess.check_call(
            [
                "nix-store",
                "--realise",
                "--add-root",
                constants.PKG_LINK,
                str(drv_path),
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
        patches = drv_payload["env"].get("patches", "").strip()
        if patches:
            patch_files = patches.split(" ")
            logger.info("Found package patches %s, realizing ...", patch_files)
            pkg_patches_dir = pathlib.Path(constants.PKG_PATCHES_DIR)
            pkg_patches_dir.mkdir(exist_ok=True)
            for index, patch_file in enumerate(patch_files):
                subprocess.check_call(
                    [
                        "nix-store",
                        "--realise",
                        "--add-root",
                        str(pkg_patches_dir / f"{index}.patch"),
                        patch_file,
                    ]
                )

    logger.info("Checking out source code from %s to %s", src, checkout_dir)
    src_path = pathlib.Path(src)
    if src_path.is_dir():
        shutil.copytree(src, str(checkout_dir))
        checkout_dir.chmod(0o700)
    else:
        mime_type = mimetypes.guess_type(src_path)
        if mime_type == ("application/x-tar", "gzip"):
            logger.info("Extract tar.gz file %s into %s", src_path, checkout_dir)
            checkout_dir.mkdir(exist_ok=True)
            with src_path.open("rb") as fo, switch_cwd(checkout_dir):
                # TODO: is it always 1?
                extract_tar(fo, strip_path_count=1)
        # TODO: support other format
        else:
            logger.error("Unsupported src (%s) type, don't know how to handle", src)
            sys.exit(-1)

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
                apply_patch(repo=repo, patch_file=patch_file)
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
