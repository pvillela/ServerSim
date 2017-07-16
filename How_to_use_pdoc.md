HOW TO USE pdoc
===============

Install pdoc:

```
pip install pdoc --user
```

The `--user` option is needed to avoid a permission denied error.

Then, execute the following commands on the command line:

```
export PYTHONPATH=/home/pvillela/DEV/Python/ServerSim/
pdoc --all-submodules --html --html-dir html serversim
```

The generated html will be in the directory `/home/pvillela/DEV/Python/ServerSim/html`
