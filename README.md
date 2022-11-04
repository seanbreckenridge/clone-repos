# clone-repos

a basic git repo clone script, with special support for pip and/or editable installs, using [reorder_editable](https://github.com/seanbreckenridge/reorder_editable)

This supports running some sort of postinstall step (a shell command) as well

As an example of a `clone-repos.yaml` file this expects, [see mine](https://sean.fish/d/clone-repos.yaml?redirect)

## Installation

Requires `python3.9+`

To install with pip, run:

    pip install git+https://github.com/seanbreckenridge/clone-repos

## Usage

```
Usage: clone-repos [OPTIONS] CONFIG_FILE

Options:
  --base-path DIRECTORY  base repository directory to clone data into
                         [required]
  --help                 Show this message and exit.
```

The format for a repo is:

```yaml
"url to repository":
  base: path # overwrite base-path for this repo
  dirname: directory_name # directory name to clone into
  pip: how # 'install' or 'editable'
  postinstall: "shell command here"
```

This expects a `$REPOS` environment variable to be set, which is the base directory to clone into, e.g. in your shell config set:

```bash
export REPOS="${HOME}/Repos"
```

... or you can provide the `--base-path` flag when running

To run, just run `clone-repos`

I setup an alias in my dotfiles like:

`alias cr="python3 -m pip install 'git+https://github.com/seanbreckenridge/clone-repos' && clone-repos"`

### Tests

```bash
git clone 'https://github.com/seanbreckenridge/clone-repos'
cd ./clone-repos
pip install '.[testing]'
flake8 ./clone-repos
mypy ./clone-repos
```
