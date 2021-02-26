## `as_blog`: Alex and Steve's Blog

The site where we turn Google Docs into publishable web pages.

## Technologies

### `pre-commit`

This repository comes ready to work with
[`pre-commit`](https://pre-commit.com/). This is a very easy way to ensure
that comits meet project standards. Unfortunately at present `black` and
`reorder-imports` are engaged in an ugly fight about the order of imports, so
you may find it easier not to install `pre-commit` until I've resolved the
correct configuration. A CI/CD pipeline will in any case eventually apply
these checks.

### `poetry`

The Python tooling is provided by [`poetry`](https://python-poetry.org/),
which makes dependency and virtual management handling much easier—no
`requirements.txt` file is needed!

It offers a choice of three different Python environments, and when
tests get organized we'll be able to run them with `tox` across the
multiple environments, but consider this a refinement for the future.
`poetry` is configured in the _pyproject.toml_ file, but there's
little need to edit that manually - `poetry` commands are normally
sufficient to update it.

The author's `poetry` installation lives in a complete Python virtual
environment in _~/.poetry_, which is the default installation mode and
allows `poetry` to be separately maintained from the projects it manages.

Some useful commands (get a full list with `poetry --help`):

**`poetry shell`** Starts a subshell running the selected project virtual environment.

**`poetry run` _`command ...`_** runs the given command in a subshell in
which the selected virtual environment is activated. A typical use would be to
start the local web server with the command `poetry run flask run`.

**`poetry add [-D]`** **_`dependency`_** Updates _pyproject.toml_ and the _poetry.lock_
    file with a new dependency. The `-D` option indicates the dependency is
    required only for development.

**`poetry install`** creates or updates the currently-selected virtual environment,
    including the current project.

**`poetry env use 3.x`** allows selection of one of the configured Python
    virtual environments (currently _3.6|3.7|3.8_)

**`poetry env list`** lists all virtual environmentd associate with the project. Sample output:

    as-blog-LcUmjM9R-py3.6
    as-blog-LcUmjM9R-py3.7 (Activated)
    as-blog-LcUmjM9R-py3.8

## Project-specific commands

`poetry` makes it easy to install commands in the virtual environment (see
the _pyproject.toml_ `[tool.poetry.scripts]` section). The following commands
are currently available:

**`pull` _`document_id`_** download the JSON document with the given id,
storing the JSON in a local database.

**`load` _`document_id`_** take the last-downloaded version of the given
document and convert it to HTML. Locate the appropriate Python file in the
snippets section of the repository and produce a replacement file where them
snippets are rreplaced with those extracted from the post.

**`view` _`document_id`_** sends the HTML generated for the aricle body to
standard output.

**`browse` _`document_id`_** opens a browser window on
http://127.0.0.1;5000/blog/document_id to display the processed HTML
output embedded in the blog template.

**`showjson` _`document_id`_** sends the captured JSON for the given
document_id to standard out, useful to access the JSON while avoiding the
complexity of interfacing directly to the database.

## Notes on code quality

Some of this stuff (database storage particularly) has been thrown together
in haste to get a working prototype ready. The organisation is
ill-thought-out and the code is extremely brittle in places. I'd really like
to improve code quality so don't hold back on the criticism.

Agressive refactoring is the way to go!

## Current status

This version's `load` command is finally capable of extracting
properly-identified snippets from a downloaded post and integrating them with
the `git`-maintained master file from which they are notionally extracted,
making it practical to perform simple code editing in the Google doc source
and use those changes to update the source file for the post in `git`.

There's a vestigial `Makefile` that at present just contains a couple of
early testing commands. It's a good place to capture simple recipes.

Assuming you've installed `poetry` and cloned the repo I'd suggest starting the web server with

    poetry run flask run

Note that a _.env_ file will be honoured by the `python-dotenv` package, allowing you to configure your environment
for ease of operation. Mine currently reads

    export FLASK_APP=src/tools/serve.py
    export FLASK_DEBUG=1
    export PYTHONPATH=src/tools:src/snippets

This _should_ work for everyone, allowing you to run all commands from the project
root directory.

## Future work



Besides the above-mentioned refactoring, take a look at
[issues in this repository](https://github.com/holdenweb/as_blog/issues).
Feel free to file further issues in cases of genuine need.
