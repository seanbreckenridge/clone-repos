import os
import json
from pathlib import Path
from typing import Any

import click

from .repo import Repo


conf_dir = Path(os.environ.get("XDG_CONFIG_DIR", Path.home() / ".config"))
default_config = conf_dir / "clone-repos.yaml"


def _default(val: Any) -> Any:
    if isinstance(val, Path):
        return str(val)
    raise TypeError(f"Not sure how to serialize {type(val)} {val}")


@click.command(
    epilog="See https://github.com/seanbreckenridge/clone-repos/ for config file format"
)
@click.option(
    "-b",
    "--base-repos",
    required=True,
    type=click.Path(file_okay=False, dir_okay=True, exists=True, path_type=Path),
    envvar="REPOS",
    show_envvar=True,
    help="base repository directory to clone repos into",
)
@click.option(
    "-P",
    "--parse-config",
    required=False,
    is_flag=True,
    help="test parsing the config file instead of running clone",
)
@click.option(
    "-B",
    "--break-system-packages",
    required=False,
    is_flag=True,
    help="pass the --break-system-packages flag to pip",
)
@click.argument(
    "CONFIG_FILE",
    required=True,
    type=click.Path(dir_okay=False, file_okay=True, exists=True, path_type=Path),
    default=default_config,
)
def main(
    base_repos: Path, parse_config: bool, break_system_packages: bool, config_file: Path
) -> None:
    """
    Clones and sets up your repos.

    Can provide a CONFIG_FILE instead of using the default
    """
    repos = Repo.parse_file(
        base=base_repos, file=config_file, break_system_packages=break_system_packages
    )
    if parse_config:
        for r in repos:
            print(json.dumps(r.__dict__, default=_default))
    else:
        for r in repos:
            r.run()


if __name__ == "__main__":
    main(prog_name="clone-repos")
