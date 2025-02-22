import logging
import os

import click
from rich.logging import Console
from rich.logging import RichHandler

from .environment import Environment
from .environment import LOG_LEVEL_MAP
from .environment import LogLevel
from .environment import pass_env


@click.group(help="Command line tools for patching nixpkgs")
@click.option(
    "-l",
    "--log-level",
    type=click.Choice(
        list(map(lambda key: key.value, LOG_LEVEL_MAP.keys())), case_sensitive=False
    ),
    default=lambda: os.environ.get("LOG_LEVEL", "INFO"),
)
@click.version_option(prog_name="nix-playground", package_name="nix-playground")
@pass_env
def cli(env: Environment, log_level: str):
    env.log_level = LogLevel(log_level)
    FORMAT = "%(message)s"
    console = Console(stderr=True)
    logging.basicConfig(
        level=LOG_LEVEL_MAP[env.log_level],
        format=FORMAT,
        datefmt="[%X]",
        handlers=[RichHandler(console=console)],
        force=True,
    )
    httpx_logger = logging.getLogger("httpx")
    httpx_logger.level = logging.WARNING
