import logging

import click

from .cli import cli
from .environment import Environment
from .environment import pass_env

logger = logging.getLogger(__name__)


@cli.command(name="checkout", help="Checkout nixpkgs source content locally")
@click.argument("NAME", type=str)
@pass_env
def main(env: Environment, name: str):
    logger.info("Checkout out nixpkgs %s")
