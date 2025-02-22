import pytest

from nix_playground import constants
from nix_playground.utils import Package
from nix_playground.utils import parse_pkg


@pytest.mark.parametrize(
    "pkg_name, expected",
    [
        (
            "libnvidia-container",
            Package(flake=constants.DEFAULT_FLAKE, attr_name="libnvidia-container"),
        ),
        ("nix#check", Package(flake="nix", attr_name="check")),
    ],
)
def test_parse_pkg(pkg_name: str, expected: Package):
    assert parse_pkg(pkg_name) == expected
