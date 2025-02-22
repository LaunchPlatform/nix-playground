import logging
import pathlib

import click
import pygit2

from . import constants
from .cli import cli
from .environment import Environment
from .environment import pass_env

logger = logging.getLogger(__name__)


@cli.command(name="build", help="Build nix package with changes in the checkout folder")
@pass_env
def main(env: Environment):
    np_dir = pathlib.Path(constants.PLAYGROUND_DIR)
    repo = pygit2.Repository(constants.DEFAULT_CHECKOUT_DIR)
    path_file = np_dir / constants.PATCH_FILE
    with path_file.open("wt") as fo:
        for patch in repo.diff(cached=True):
            fo.write(patch.text)
