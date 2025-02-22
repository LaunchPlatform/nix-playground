import logging
import pathlib

import pygit2

from . import constants
from .cli import cli
from .environment import Environment
from .environment import pass_env

logger = logging.getLogger(__name__)


@cli.command(
    name="patch", help="Output the patch file to apply on the current nix package"
)
@pass_env
def main(env: Environment):
    np_dir = pathlib.Path(constants.PLAYGROUND_DIR)
    pkg_name = (np_dir / constants.PKG_NAME).read_text()
    logger.info("Making patch for package %s ...", pkg_name)

    repo = pygit2.Repository(constants.DEFAULT_CHECKOUT_DIR)
    for patch in repo.diff(cached=True):
        print(patch.text)
    logger.info("done")
