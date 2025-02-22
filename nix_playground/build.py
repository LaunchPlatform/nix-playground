import logging
import pathlib
import subprocess
import textwrap

import pygit2

from . import constants
from .cli import cli
from .environment import Environment
from .environment import pass_env
from .utils import parse_pkg

logger = logging.getLogger(__name__)


@cli.command(name="build", help="Build nix package with changes in the checkout folder")
@pass_env
def main(env: Environment):
    np_dir = pathlib.Path(constants.PLAYGROUND_DIR)
    pkg_name = (np_dir / constants.PKG_NAME).read_text()
    package = parse_pkg(pkg_name)
    logger.info("Building package %s", pkg_name)

    repo = pygit2.Repository(constants.DEFAULT_CHECKOUT_DIR)
    path_file = np_dir / constants.PATCH_FILE
    logger.info("Writing patch file to %s", path_file)
    with path_file.open("wt") as fo:
        for patch in repo.diff(cached=True):
            fo.write(patch.text)
    logger.info("Building nix package with patch")
    subprocess.check_call(
        [
            "nix-build",
            "--expr",
            textwrap.dedent(f"""\
    with import <{package.flake}> {{}};
        {package.attr_name}.overrideAttrs (oldAttrs: {{
            patches = (lib.attrsets.attrByPath ["patches"] [] oldAttrs) ++ [{np_dir / constants.PATCH_FILE}];
        }})
    """),
        ]
    )
    logger.info("done")
