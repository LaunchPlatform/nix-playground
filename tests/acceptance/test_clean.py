import pathlib

import pytest
from click.testing import CliRunner

from nix_playground import constants
from nix_playground.main import cli
from nix_playground.utils import switch_cwd


@pytest.mark.parametrize(
    "pkg_name, checkout_dir_name",
    [
        ("nixpkgs#cowsay", None),
        ("nixpkgs#cowsay", "my_checkout"),
        ("nixpkgs#libnvidia-container", None),
    ],
)
def test_clean(
    tmp_path: pathlib.Path,
    cli_runner: CliRunner,
    pkg_name: str,
    checkout_dir_name: str,
):
    cli_runner.mix_stderr = False
    with switch_cwd(tmp_path):
        checkout_args = ["checkout", pkg_name]
        if checkout_dir_name is not None:
            checkout_args.extend(["-c", checkout_dir_name])
        result = cli_runner.invoke(cli, checkout_args)
        assert result.exit_code == 0
        result = cli_runner.invoke(cli, ["clean"])
        assert result.exit_code == 0

    np_dir = tmp_path / constants.PLAYGROUND_DIR
    assert not np_dir.exists()
    checkout_dir = tmp_path / (
        constants.DEFAULT_CHECKOUT_DIR
        if checkout_dir_name is None
        else checkout_dir_name
    )
    assert not checkout_dir.exists()
