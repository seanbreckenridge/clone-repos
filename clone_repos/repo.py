import sys
import os
import shlex
import subprocess
import contextlib
from functools import cached_property
from pathlib import Path
from urllib.parse import urlparse
from typing import Dict, Any, Optional, List

import click
import yaml
from reorder_editable.core import Editable


@contextlib.contextmanager
def in_cwd(to_dir: os.PathLike):
    curdir = os.getcwd()
    try:
        os.chdir(to_dir)
        yield
    finally:
        os.chdir(curdir)


class Repo:
    def __init__(
        self,
        base: Path,
        git_url: str,
        *,
        symlink_to: Optional[str] = None,
        dirname: Optional[str] = None,
        postinstall_cmd: Optional[str] = None,
        pip_install: bool = False,
        editable_install: bool = False,
    ) -> None:
        self.base = base
        self.git_url = git_url
        self.postinstall_cmd = postinstall_cmd
        self.pip_install = pip_install
        self.editable_install = editable_install
        self.editable_check_dirs = ["src"]
        self.dirname = dirname
        self.symlink_to = symlink_to

    @staticmethod
    def strip_str(val: Optional[str]) -> Optional[str]:
        if val is None:
            return None
        if val.strip() == "":
            return None
        return val

    @classmethod
    def from_dict(
        cls, git_url: str, base: Path, data: Optional[Dict[str, Any]] = None
    ) -> "Repo":
        if data is None:
            data = {}
        dirname = cls.strip_str(data.get("dirname"))
        pip_data = data.get("pip")
        pip_install = False
        editable_install = False
        if pip_data == "install":
            pip_install = True
        elif pip_data == "editable":
            editable_install = True
        postinstall = cls.strip_str(data.get("postinstall"))
        symlink_to = cls.strip_str(data.get("symlink_to"))
        if "base" in data and isinstance(data["base"], str):
            base = Path(data["base"]).expanduser().absolute()
            assert base.exists(), f"provided base '{base}' does not exist"
        return cls(
            base=base,
            git_url=git_url,
            dirname=dirname,
            postinstall_cmd=postinstall,
            symlink_to=symlink_to,
            pip_install=pip_install,
            editable_install=editable_install,
        )

    def __repr__(self):
        return str(self.__dict__)

    __str__ = __repr__

    @cached_property
    def name(self) -> str:
        if self.dirname is None:
            return urlparse(self.git_url).path.split("/")[-1]
        else:
            return self.dirname

    @cached_property
    def target(self) -> Path:
        return self.base / self.name

    def _git_clone(self) -> Optional[FileNotFoundError]:
        if self.target.exists():
            click.echo(f"{self.name}: target {self.target} already exists", err=True)
            return
        proc = subprocess.Popen(
            shlex.split(f"git clone '{self.git_url}' '{self.target}'")
        )
        proc.wait()
        if proc.returncode != 0:
            click.echo(
                f"{self.name}: git error, return code {proc.returncode}", err=True
            )
        if not self.target.exists():
            click.echo(
                f"'{self.target}' does not exist after 'git clone' step, skipping repo install",
                err=True,
            )
            return FileNotFoundError()

    def _symlink(self) -> None:
        assert self.symlink_to is not None
        st = Path(self.symlink_to).expanduser().absolute()
        if not st.exists():
            click.echo(f"{self.name}: target directory {st} does not exist")
            return
        link_target = st / self.name
        if os.path.islink(link_target):
            click.echo(f"{self.name}: link target {link_target} is already linked")
            return
        click.echo(f"Symlinking {self.target} -> {link_target}")
        os.symlink(self.target, link_target)

    def _pip_install(self) -> None:
        proc = subprocess.Popen(
            [sys.executable, *shlex.split(f"-m pip install --user '{self.target}'")]
        )
        proc.wait()
        if proc.returncode != 0:
            click.echo(
                f"{self.name}: pip error, return code {proc.returncode}", err=True
            )

    def _editable_install(self) -> None:
        e = Editable()
        installed = e.read_lines()
        targets = [str(self.target)]
        # is common for editable packages to place everything under 'src' folder
        for additional in self.editable_check_dirs:
            targets.append(str(self.target / additional))
        if any(t in installed for t in targets):
            click.echo(f"{self.name}: {self.target} already in editable install list")
        else:
            proc = subprocess.Popen(
                [
                    sys.executable,
                    *shlex.split(f"-m pip install --user --editable '{self.target}'"),
                ]
            )
            proc.wait()
            if proc.returncode != 0:
                click.echo(
                    f"{self.name}: pip error, return code {proc.returncode}", err=True
                )

    def _postinstall(self) -> None:
        with in_cwd(self.target):
            assert self.postinstall_cmd is not None
            click.echo(f"{self.name}: running postinstall '{self.postinstall_cmd}'")
            proc = subprocess.Popen(shlex.split(self.postinstall_cmd))
            proc.wait()
            if proc.returncode != 0:
                click.echo(
                    f"{self.name}: postinstall error, return code {proc.returncode}",
                    err=True,
                )

    def run(self) -> None:
        err = self._git_clone()
        if err is not None:
            return
        if self.symlink_to is not None:
            self._symlink()
        if self.pip_install:
            self._pip_install()
        if self.editable_install:
            self._editable_install()
        if self.postinstall_cmd is not None:
            self._postinstall()


def parse_file(base: Path, file: Path) -> List[Repo]:
    repos: List[Repo] = []
    with file.open("r") as f:
        data = yaml.load(f, Loader=yaml.FullLoader)
    for key, data in data.items():
        r = Repo.from_dict(git_url=key, base=base, data=data)
        repos.append(r)
    return repos
