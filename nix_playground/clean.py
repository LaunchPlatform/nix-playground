import logging
import shutil

from . import constants
from .cli import cli
from .environment import Environment
from .environment import pass_env
from .utils import ensure_np_dir

logger = logging.getLogger(__name__)


@cli.command(name="clean", help="Clean all files generated from nix-playground")
@pass_env
def main(env: Environment):
    np_dir = ensure_np_dir()

    checkout_link = np_dir / constants.CHECKOUT_LINK
    if checkout_link.exists():
        checkout_dir = checkout_link.readlink()
    else:
        checkout_dir = None

    logger.info("Deleting checkout link %s", checkout_link)
    checkout_link.unlink(missing_ok=True)

    if checkout_dir is not None:
        logger.info("Deleting checkout dir %s", checkout_dir)
        if checkout_dir.exists():
            shutil.rmtree(checkout_dir)

    logger.info("Deleting nix-playground dir %s", np_dir)
    if np_dir.exists():
        shutil.rmtree(np_dir)

    logger.info("done")
