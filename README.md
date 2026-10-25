# GitHub Dev Battle

Some funky app where you can compare GitHub users.

## Prerequisites

* Python 3.14+
* [uv](https://docs.astral.sh/uv/) (will handle `fastapi`, `httpx`, and `jinja2` for you)

## TO USE

First, sync the dependencies:

```bash
uv sync
```

Start the FastAPI server:

```bash
uv run fastapi dev src/github_dev_battle/main.py
```

Then go to `http://localhost:8000/` and you can do the rest :P
