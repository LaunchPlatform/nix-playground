import pathlib

import pytest
from click.testing import CliRunner

from nix_playground.main import cli
from nix_playground.utils import switch_cwd


@pytest.mark.parametrize(
    "pkg_name, expected_result_files",
    [
        ("nixpkgs#cowsay", [pathlib.Path("bin") / "cowsay"]),
        (
            "github:NixOS/nixpkgs/a3a3dda3bacf61e8a39258a0ed9c924eeca8e293#cowsay",
            [pathlib.Path("bin") / "cowsay"],
        ),
        ("nixpkgs#hello", [pathlib.Path("bin") / "hello"]),
        ("nixpkgs#libnvidia-container", [pathlib.Path("bin") / "nvidia-container-cli"]),
    ],
)
def test_build(
    tmp_path: pathlib.Path,
    cli_runner: CliRunner,
    pkg_name: str,
    expected_result_files: list[pathlib],
):
    cli_runner.mix_stderr = False
    with switch_cwd(tmp_path):
        result = cli_runner.invoke(cli, ["checkout", pkg_name])
        assert result.exit_code == 0
        result = cli_runner.invoke(cli, ["build"])
        assert result.exit_code == 0

    for expected_file in expected_result_files:
        expected_file_path = tmp_path / "result" / expected_file
        assert expected_file_path.exists()
