from .build import main as build  # noqa
from .checkout import main as checkout  # noqa
from .clean import main as clean  # noqa
from .cli import cli
from .patch import main as patch  # noqa

__ALL__ = [cli]

if __name__ == "__main__":
    cli()
