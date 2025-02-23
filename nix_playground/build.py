import json
import logging
import subprocess
import textwrap

import pygit2

from . import constants
from .cli import cli
from .environment import Environment
from .environment import pass_env
from .utils import ensure_np_dir
from .utils import parse_pkg

logger = logging.getLogger(__name__)


@cli.command(name="build", help="Build nix package with changes in the checkout folder")
@pass_env
def main(env: Environment):
    np_dir = ensure_np_dir()
    checkout_dir = np_dir / constants.CHECKOUT_LINK
    path_file = np_dir / constants.PATCH_FILE

    pkg_name = (np_dir / constants.PKG_NAME).read_text()
    package = parse_pkg(pkg_name)
    logger.info("Building package %s", pkg_name)

    repo = pygit2.Repository(checkout_dir)
    logger.info(
        "Gathering diff from %s and writing patch file to %s", checkout_dir, path_file
    )
    with path_file.open("wt") as fo:
        for patch in repo.diff(cached=True):
            fo.write(patch.text)
    patch_path = np_dir / constants.PATCH_FILE
    patch_store_path = subprocess.check_output(
        [
            "nix",
            "store",
            "add",
            str(patch_path),
        ]
    ).decode("utf8")
    logger.info("Added patch file to store as %s", patch_store_path)

    logger.info("Building nix package with patch")

    der_json_path = np_dir / constants.DER_JSON_FILE
    with der_json_path.open("rb") as fo:
        der_payloads = json.load(fo)

    if len(der_payloads) != 1:
        raise ValueError("Expected only one der in the payload")

    der_path = list(der_payloads.keys())[0]
    der_payload = der_payloads[der_path]

    patches = der_payload["env"].get("patches", "")
    if patches:
        patches = patches.split(" ")
    else:
        patches = []
    patches.append(patch_store_path)

    der_payload["env"]["patches"] = " ".join(patches)

    # This is a hack, we expect the `nix derivation add` command to return an error like this:
    #
    #   error: derivation '/nix/store/k4lb25pvzr0magkpk04c1mw69ix73gnf-hello-2.12.1.drv' has incorrect output
    #   '/nix/store/p09fxxwkdj69hk4mgddk4r3nassiryzc-hello-2.12.1',
    #   should be '/nix/store/ja3hh4izqsjzq3rh8fxdqxw7vf56pw9m-hello-2.12.1'
    #
    # So that we can get the correct output path
    proc = subprocess.run(
        ["nix", "derivation", "add"],
        input=json.dumps(der_payload).encode("utf8"),
        stderr=subprocess.PIPE,
    )
    if proc.returncode == 0:
        raise ValueError("Does not expect this command to work")
    proc.stderr

    # logger.debug("Running nix expr:\n%s", nix_expr)
    # subprocess.check_call(
    #     [
    #         "nix",
    #         "build",
    #         "--impure",
    #         "--expr",
    #         nix_expr,
    #     ]
    # )
    logger.info("done")
