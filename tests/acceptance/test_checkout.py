import pathlib

import pytest
from click.testing import CliRunner

from nix_playground import constants
from nix_playground.main import cli
from nix_playground.utils import switch_cwd


@pytest.mark.parametrize(
    "pkg_name, expected_checkout_files",
    [
        ("nixpkgs#cowsay", [pathlib.Path("bin") / "cowsay"]),
        ("nixpkgs#hello", [pathlib.Path("src") / "hello.c"]),
        ("nixpkgs#libnvidia-container", [pathlib.Path("src") / "cli" / "main.c"]),
        ("nixpkgs#platformio-core", [pathlib.Path("platformio") / "__main__.py"]),
    ],
)
def test_checkout(
    tmp_path: pathlib.Path,
    cli_runner: CliRunner,
    pkg_name: str,
    expected_checkout_files: list[pathlib],
):
    cli_runner.mix_stderr = False
    with switch_cwd(tmp_path):
        result = cli_runner.invoke(cli, ["checkout", pkg_name])
    assert result.exit_code == 0

    np_dir = tmp_path / constants.PLAYGROUND_DIR
    assert np_dir.exists()
    pkg_name_file = np_dir / constants.PKG_NAME
    assert pkg_name_file.read_text() == pkg_name

    drv_json_file = np_dir / constants.DRV_JSON_FILE
    assert drv_json_file.exists()
    pkg_link = np_dir / constants.PKG_LINK
    assert pkg_link.exists()
    src_link = np_dir / constants.SRC_LINK
    assert src_link.exists()
    checkout_link = np_dir / constants.CHECKOUT_LINK
    assert checkout_link.exists()
    assert checkout_link.readlink() == tmp_path / constants.DEFAULT_CHECKOUT_DIR

    for expected_file in expected_checkout_files:
        expected_file_path = checkout_link / expected_file
        assert expected_file_path.exists()


def test_checkout_to_dir(tmp_path: pathlib.Path, cli_runner: CliRunner):
    cli_runner.mix_stderr = False
    pkg_name = "nixpkgs#cowsay"
    checkout_dir = tmp_path / "my_checkout"
    with switch_cwd(tmp_path):
        result = cli_runner.invoke(cli, ["checkout", pkg_name, "-c", checkout_dir.name])
    assert result.exit_code == 0

    np_dir = tmp_path / constants.PLAYGROUND_DIR
    checkout_link = np_dir / constants.CHECKOUT_LINK
    assert checkout_link.exists()
    assert checkout_link.readlink() == checkout_dir

    cowsay = checkout_dir / "bin" / "cowsay"
    assert cowsay.exists()
