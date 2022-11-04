# clone-repos

a basic git repo clone script

supports running some sort of postinstall step as well

As an example of a `clone-repos.yaml` file this expects, [see mine](https://sean.fish/d/clone-repos.yaml?redirect)

This has special support for editable pip installs, using [reorder_editable](https://github.com/seanbreckenridge/reorder_editable)

This expects a `$REPOS` environment variable to be set, which is the base directory to clone into, e.g. in your shell config set:

```bash
export REPOS="${HOME}/Repos"
```

or you can provide the `--base-path` flag when running

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

### Tests

```bash
git clone 'https://github.com/seanbreckenridge/clone-repos'
cd ./clone-repos
pip install '.[testing]'
flake8 ./clone-repos
mypy ./clone-repos
```
