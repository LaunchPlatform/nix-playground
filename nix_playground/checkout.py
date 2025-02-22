import json
import logging
import os
import subprocess
import sys

import click

from .cli import cli
from .environment import Environment
from .environment import pass_env

logger = logging.getLogger(__name__)


LOCAL_DER_LINK = ".pkg_der"


@cli.command(name="checkout", help="Checkout nixpkgs source content locally")
@click.argument("PKG_NAME", type=str)
@pass_env
def main(env: Environment, pkg_name: str):
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
                LOCAL_DER_LINK,
            ]
        )
    except subprocess.CalledProcessError:
        logger.error("Failed to instantiate package %s", pkg_name)
        sys.exit(-1)
    der_path = os.readlink(LOCAL_DER_LINK)
    logger.info("Got package der path %s", der_path)
    der_payload = json.loads(
        subprocess.check_output(["nix", "derivation", "show", der_path])
    )
    logger.info("Got package der path %s", der_payload)
