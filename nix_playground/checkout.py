import json
import logging
import subprocess
import sys

import click

from .cli import cli
from .environment import Environment
from .environment import pass_env

logger = logging.getLogger(__name__)


@cli.command(name="checkout", help="Checkout nixpkgs source content locally")
@click.argument("PKG_NAME", type=str)
@pass_env
def main(env: Environment, pkg_name: str):
    logger.info("Checkout out nixpkgs %s ...", pkg_name)
    try:
        pkg_path = json.loads(
            subprocess.check_output(["nix", "eval", "--json", pkg_name])
        )
    except subprocess.CalledProcessError:
        logger.error("Failed to eval package %s", pkg_name)
        sys.exit(-1)
    logger.info("Got package path %s", pkg_path)
    pkg_der_path = (
        subprocess.check_output(["nix-store", "--query", "--deriver", pkg_path])
        .decode("utf8")
        .strip()
    )
    logger.info("Got package der path %s", pkg_der_path)
    der_payload = subprocess.check_output(["nix", "derivation", "show", pkg_der_path])
    logger.info("Got package der path %s", der_payload)
