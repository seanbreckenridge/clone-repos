import os
from pathlib import Path
from clone_repos.repo import Repo

os.environ["REPOS"] = str(Path.home() / "Repos")

this_dir = Path(__file__).parent
conf = this_dir / "clone-repos.yaml"
assert conf.exists()

pipefail = this_dir / "pipefail.yaml"

base = Path(os.environ["REPOS"])


def test_parse_config() -> None:
    repos = Repo.parse_file(base=base, file=conf)
    assert isinstance(repos, list)
    pl = repos[3]
    assert isinstance(pl, Repo)
    assert pl.base == base
    assert pl.git_url == "https://github.com/seanbreckenridge/bleanser-fork"
    assert pl.postinstall_cmd == [
        'git remote add upstream "https://github.com/karlicoss/bleanser"',
        "git pull upstream master",
    ]
    assert pl.pip_install == False
    assert pl.editable_install == True
    assert pl.editable_non_user == False
    assert pl.dirname == "bl-fork"
    assert pl.symlink_to == "/tmp"

    assert repos[0].git_url == "https://github.com/seanbreckenridge/ttally"
    assert repos[0].preinstall_cmd == ["git pull"]
    assert repos[2].preinstall_cmd == ["git pull"]
    assert repos[2].pipefail == False


def test_pipefail() -> None:
    repos = Repo.parse_file(base=base, file=pipefail)
    assert isinstance(repos, list)
    assert repos[0].pipefail == True
