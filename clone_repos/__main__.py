import os
from pathlib import Path

import click

from .repo import parse_file


conf_dir = Path(os.environ.get("XDG_CONFIG_DIR", Path.home() / ".config"))
default_config = conf_dir / "clone-repos.yaml"


@click.command()
@click.option(
    "--base-repos",
    required=True,
    type=click.Path(file_okay=False, dir_okay=True, exists=True, path_type=Path),
    envvar="REPOS",
    help="base repository directory to clone repos into",
)
@click.argument(
    "CONFIG_FILE",
    required=True,
    type=click.Path(dir_okay=False, file_okay=True, exists=True, path_type=Path),
    default=default_config,
)
def main(base_repos: Path, config_file: Path):
    repos = parse_file(base=base_repos, file=config_file)
    for r in repos:
        r.run()


if __name__ == "__main__":
    main(prog_name="clone-repos")
