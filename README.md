# clone-repos

a basic git repo clone script, with special support for pip and/or editable installs, using [reorder_editable](https://github.com/seanbreckenridge/reorder_editable)

This supports running a preinstall (after cloning) or postinstall step (a shell command) as well

For examples of a `clone-repos.yaml` file this expects at `~/.config/clone-repos.yaml`, see

- [clone-repos.yaml](https://sean.fish/d/clone-repos.yaml?redirect)
- [computer-clone-repos.yaml](https://sean.fish/d/computer-clone-repos.yaml?redirect)
- [hpi-clone-repos.yaml](https://sean.fish/d/hpi-clone-repos.yaml?redirect)

## Installation

Requires `python3.9+`

To install with pip, run:

    pip install git+https://github.com/seanbreckenridge/clone-repos

## Usage

```
Usage: clone-repos [OPTIONS] CONFIG_FILE

  Clones and sets up your repos.

  Can provide a CONFIG_FILE instead of using the default

Options:
  --base-repos DIRECTORY  base repository directory to clone repos into
                          [required]
  --parse-config          test parsing the config file instead of running
                          clone
  --help                  Show this message and exit.
```

The full format for a repo is:

```yaml
"url to repository":
  base: path # overwrite base-path for this repo
  dirname: directory_name # directory name to clone into
  symlink_to: directory_name # the parent directory to symlink the cloned repo to
  pip: how # 'install', 'editable' or 'editable_system'
  preinstall:
    - "shell command 1"
    - "shell command 2"
  postinstall: "shell command here"
```

The `preinstall` and `postinstall` scripts can either be one command (a string), or multiple (a list)

For `pip`, `editable` by default uses the `--user` flag, if you know what you're doing and want to install in your system lib directory, use `editable_system` (Note that this only works in particular python installations. In a lot of cases, pip will still default to installing into your `--user` directory instead). See [reorder_editable](https://github.com/seanbreckenridge/reorder_editable) for context.

This expects a `$REPOS` environment variable to be set, which is the base directory to clone into, e.g. in your shell config set:

```bash
export REPOS="${HOME}/Repos"
```

... or you can provide the `--base-repos` flag when running

To clone, run `clone-repos` or `python3 -m clone_repos`

To run this quickly on new machines, I setup an alias in my dotfiles like:

`alias cr="python3 -m pip install 'git+https://github.com/seanbreckenridge/clone-repos' && clone-repos"`

### Tests

```bash
git clone 'https://github.com/seanbreckenridge/clone-repos'
cd ./clone-repos
pip install '.[testing]'
flake8 ./clone-repos
mypy ./clone-repos
```
