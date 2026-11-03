# style-guides

Coding conventions I use in repositories I start or own. In an existing codebase, its own conventions win.

| Language | Guide | Lint config | Reference code |
|---|---|---|---|
| Python | [`python/STYLE-GUIDE.md`](python/STYLE-GUIDE.md) | [`python/ruff.toml`](python/ruff.toml) | [`python/example/transcript.py`](python/example/transcript.py) |

To adopt the Python guide in a project, link the guide from its `CONTRIBUTING` file and copy `ruff.toml` (or its contents under `[tool.ruff]` in `pyproject.toml`).

The reference module is checked with:

```sh
cd python
ruff check . && ruff format --check .
python -m doctest -v example/transcript.py
```
