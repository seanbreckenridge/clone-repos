from __future__ import annotations
import sys
import os
import shlex
import subprocess
import shutil
import contextlib
from functools import cached_property, lru_cache
from pathlib import Path
from urllib.parse import urlparse
from typing import Dict, Any, Optional, Union, List, Iterator

import click
import yaml
from reorder_editable.core import Editable


@contextlib.contextmanager
def in_cwd(to_dir: Union[str, Path]) -> Iterator[None]:
    curdir = os.getcwd()
    try:
        os.chdir(to_dir)
        yield
    finally:
        os.chdir(curdir)


@lru_cache(maxsize=1)
def _git_path() -> Union[str, RuntimeError]:
    git_path = shutil.which("git")
    if git_path is None:
        return RuntimeError("Could not find 'git' on your $PATH")
    return git_path


class Repo:
    def __init__(
        self,
        base: Path,
        git_url: str,
        *,
        break_system_packages: bool = False,
        symlink_to: Optional[str] = None,
        dirname: Optional[str] = None,
        preinstall_cmd: Optional[List[str]] = None,
        postinstall_cmd: Optional[List[str]] = None,
        pip_install: bool = False,
        editable_install: bool = False,
        editable_non_user: bool = False,
        pipefail: bool = False,
    ) -> None:
        self.base = base
        self.git_url = git_url
        self.preinstall_cmd = preinstall_cmd if preinstall_cmd is not None else []
        self.postinstall_cmd = postinstall_cmd if postinstall_cmd is not None else []
        self.pip_install = pip_install
        self.editable_install = editable_install
        self.editable_non_user = editable_non_user
        self.editable_check_dirs = ["src"]
        self.dirname = dirname
        self.symlink_to = symlink_to
        self.pipefail = pipefail
        self.break_system_packages = break_system_packages

    @staticmethod
    def strip_bool(val: Union[bool, str, None], default: bool) -> bool:
        if val is None:
            return default
        if isinstance(val, bool):
            return val
        if isinstance(val, str):
            if val.lower() == "true":
                return True
            elif val.lower() == "false":
                return False
        raise RuntimeError(f"Could not parse bool: {val}")

    @staticmethod
    def strip_str(val: Optional[str]) -> Optional[str]:
        if val is None:
            return None
        if val.strip() == "":
            return None
        return val

    @classmethod
    def strip_lst(cls, val: Union[Optional[str], List[str]]) -> List[str]:
        if val is None:
            return []
        if isinstance(val, str):
            v = cls.strip_str(val)
            assert v is not None
            return [v]
        elif isinstance(val, list):
            for item in val:
                if not isinstance(item, str):
                    raise RuntimeError(
                        f"While trying to parse list of strings {val}, found non-string: {item}"
                    )
            return val
        raise RuntimeError(
            f"While trying to parse list, string or null, found {type(val)} {val}"
        )

    known_keys = set(
        [
            "dirname",
            "pip",
            "preinstall",
            "postinstall",
            "symlink_to",
            "base",
            "pipefail",
        ]
    )

    @classmethod
    def from_dict(
        cls,
        git_url: str,
        base: Path,
        break_system_packages: bool,
        data: Optional[Dict[str, Any]] = None,
    ) -> Repo:
        if data is None:
            data = {}
        dirname = cls.strip_str(data.get("dirname"))
        pip_data = data.get("pip")
        pip_install = False
        editable_install = False
        editable_non_user = False
        if pip_data == "install":
            pip_install = True
        elif pip_data == "editable":
            editable_install = True
        elif pip_data == "editable_system":
            editable_install = True
            editable_non_user = True
        preinstall = cls.strip_lst(data.get("preinstall"))
        postinstall = cls.strip_lst(data.get("postinstall"))
        symlink_to = cls.strip_str(data.get("symlink_to"))
        pipefail = cls.strip_bool(data.get("pipefail"), default=False)
        if "base" in data and isinstance(data["base"], str):
            base = Path(data["base"]).expanduser().absolute()
            if not base.exists():
                click.echo(
                    f"Warning: base directory '{base}' does not exist, creating it",
                    err=True,
                )
                base.mkdir(parents=True)
        log_name = None
        for key in data.keys():
            if key not in cls.known_keys:
                if log_name is None:
                    log_name = cls._parse_name_from_url(git_url)
                click.echo(
                    f"{log_name}: Warning, unknown key: '{key}' '{data[key]}'", err=True
                )
        return cls(
            base=base,
            git_url=git_url,
            dirname=dirname,
            break_system_packages=break_system_packages,
            preinstall_cmd=preinstall,
            postinstall_cmd=postinstall,
            symlink_to=symlink_to,
            pip_install=pip_install,
            editable_install=editable_install,
            editable_non_user=editable_non_user,
            pipefail=pipefail,
        )

    def __repr__(self) -> str:
        return str(self.__dict__)

    __str__ = __repr__

    @staticmethod
    def _parse_name_from_url(url: str) -> str:
        return urlparse(url).path.split("/")[-1]

    @cached_property
    def name(self) -> str:
        if self.dirname is None:
            return self.__class__._parse_name_from_url(self.git_url)
        else:
            return self.dirname

    @cached_property
    def target(self) -> Path:
        return self.base / self.name

    def _git_clone(self) -> Optional[Exception]:
        gp = _git_path()
        if isinstance(gp, Exception):
            return gp
        if self.target.exists():
            click.echo(f"{self.name}: target {self.target} already exists", err=True)
            return None
        proc = subprocess.Popen(
            shlex.split(f"{gp} clone '{self.git_url}' '{self.target}'")
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
        return None

    def _symlink(self) -> None:
        assert self.symlink_to is not None
        st = Path(self.symlink_to).expanduser().absolute()
        if not st.exists():
            click.echo(f"{self.name}: target directory {st} does not exist")
            return
        link_target = st / self.name
        if os.path.exists(link_target):
            click.echo(f"{self.name}: link target {link_target} is already linked")
            return
        click.echo(f"Symlinking {self.target} -> {link_target}")
        try:
            os.symlink(self.target, link_target)
        except FileExistsError:
            click.echo(
                f"{self.name}: symlink target {link_target} already exists, skipping symlink"
            )

    def _pip_install(self) -> None:
        cmd = f"{sys.executable} -m pip install --user {'--break-system-packages' if self.break_system_packages else ''} '{self.target}'"
        click.echo(f"{self.name}: running '{cmd}'")
        proc = subprocess.Popen(shlex.split(cmd))
        proc.wait()
        if proc.returncode != 0:
            raise RuntimeError(f"{self.name}: pip error, return code {proc.returncode}")

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
            cmd = f"""{sys.executable} -m pip install {'--user' if not self.editable_non_user else ''} --editable {'--break-system-packages' if self.break_system_packages else ''} '{self.target}'"""
            click.echo(f"{self.name}: running '{cmd}'")
            proc = subprocess.Popen(shlex.split(cmd))
            proc.wait()
            if proc.returncode != 0:
                raise RuntimeError(
                    f"{self.name}: pip error, return code {proc.returncode}"
                )

    def _preinstall(self) -> None:
        with in_cwd(self.target):
            assert self.preinstall_cmd is not None
            for cmd in self.preinstall_cmd:
                click.echo(f"{self.name}: running preinstall sh -c '{cmd}'")
                proc = subprocess.Popen(["sh", "-c", cmd])
                proc.wait()
                if proc.returncode != 0:
                    click.echo(
                        f"{self.name}: preinstall error, return code {proc.returncode}",
                        err=True,
                    )
                    if self.pipefail:
                        click.echo(
                            f"{self.name}: pipefail is set, aborting install",
                        )
                        return

    def _postinstall(self) -> None:
        with in_cwd(self.target):
            assert self.postinstall_cmd is not None
            for cmd in self.postinstall_cmd:
                click.echo(f"{self.name}: running postinstall sh -c '{cmd}'")
                proc = subprocess.Popen(["sh", "-c", cmd])
                proc.wait()
                if proc.returncode != 0:
                    click.echo(
                        f"{self.name}: postinstall error, return code {proc.returncode}",
                        err=True,
                    )
                    if self.pipefail:
                        click.echo(
                            f"{self.name}: pipefail is set, aborting install",
                        )
                        return

    def run(self) -> None:
        err = self._git_clone()
        if err is not None:
            return
        if self.symlink_to is not None:
            self._symlink()
        if len(self.preinstall_cmd) > 0:
            self._preinstall()
        if self.pip_install:
            self._pip_install()
        if self.editable_install:
            self._editable_install()
        if len(self.postinstall_cmd) > 0:
            self._postinstall()

    @classmethod
    def parse_file(
        cls,
        base: Path,
        file: Path,
        break_system_packages: bool = False,
    ) -> List["Repo"]:
        repos: List[Repo] = []
        with file.open("r") as f:
            data = yaml.load(f, Loader=yaml.FullLoader)
        for key, data in data.items():
            repos.append(
                Repo.from_dict(
                    git_url=key,
                    base=base,
                    break_system_packages=break_system_packages,
                    data=data,
                )
            )
        return repos
