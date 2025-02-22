from .build import main as build  # noqa
from .checkout import main as checkout  # noqa
from .cli import cli

__ALL__ = [cli]

if __name__ == "__main__":
    cli()
