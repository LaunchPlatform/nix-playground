import json
import logging
import re
import subprocess

import pygit2

from . import constants
from .cli import cli
from .environment import Environment
from .environment import pass_env
from .utils import ensure_np_dir
from .utils import parse_pkg

logger = logging.getLogger(__name__)

INCORRECT_OUTPUT_REGEX = re.compile("has incorrect output '(.+?)', should be '(.+?)'")


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
    patch_store_path = (
        subprocess.check_output(
            [
                "nix",
                "store",
                "add",
                str(patch_path),
            ]
        )
        .decode("utf8")
        .strip()
    )
    logger.info("Added patch file to store as %s", patch_store_path)

    logger.info("Building nix package with patch")

    drv_json_path = np_dir / constants.DRV_JSON_FILE
    with drv_json_path.open("rb") as fo:
        drv_payloads = json.load(fo)

    if len(drv_payloads) != 1:
        raise ValueError("Expected only one der in the payload")

    drv_path = list(drv_payloads.keys())[0]
    drv_payload = drv_payloads[drv_path]

    patches = drv_payload["env"].get("patches", "")
    if patches:
        patches = patches.split(" ")
    else:
        patches = []
    patches.append(patch_store_path)
    drv_payload["env"]["patches"] = " ".join(patches)
    drv_payload["inputSrcs"].append(patch_store_path)

    # This is a hack, we expect the `nix derivation add` command to return an error like this:
    #
    #   error: derivation '/nix/store/k4lb25pvzr0magkpk04c1mw69ix73gnf-hello-2.12.1.drv' has incorrect output
    #   '/nix/store/p09fxxwkdj69hk4mgddk4r3nassiryzc-hello-2.12.1',
    #   should be '/nix/store/ja3hh4izqsjzq3rh8fxdqxw7vf56pw9m-hello-2.12.1'
    #
    # So that we can get the correct output path. Ideally we should somehow use this rewrite der function in the nix
    # C++ code:
    # https://github.com/NixOS/nix/blob/d904921eecbc17662fef67e8162bd3c7d1a54ce0/src/libstore/derivations.cc#L1032-L1051
    # or read the source code to find how the exact hashing algorithm, but maybe next time ...
    # TODO: improve this hack
    logger.info("Computing correct output pathes")
    proc = subprocess.run(
        ["nix", "derivation", "add"],
        input=json.dumps(drv_payload).encode("utf8"),
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode == 0:
        raise ValueError("Does not expect this command to work")

    output_path_map = {
        key: value
        for key, value in INCORRECT_OUTPUT_REGEX.findall(proc.stderr.decode("utf8"))
    }
    logger.info("Got new output path map: %r", output_path_map)

    # patch der..
    outputs = drv_payload["outputs"]
    for out_key, out_value in outputs.items():
        out_path = out_value["path"]
        outputs[out_key] = dict(path=output_path_map.get(out_path, out_path))
    env_out = drv_payload["env"].get("out")
    if env_out is not None and env_out:
        output_paths = env_out.split(" ")
        drv_payload["env"]["out"] = " ".join(
            map(lambda p: output_path_map.get(p, p), output_paths)
        )

    # this time with output patch patched, it should work
    print(
        subprocess.check_output(
            ["nix", "derivation", "add"],
            input=json.dumps(drv_payload).encode("utf8"),
        )
    )
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
