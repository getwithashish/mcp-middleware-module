# Python Package from a Spec

Implement a Python package from a design specification (document, architecture diagram, or written requirements) and ship it as a working, linted, tested, type-checked, built, committed, tagged artefact.

## Entry criteria

- You have a design document that describes the module layout, class/function signatures, data models, and behaviour.
- The target repo exists (or needs to be created — see `github-repo-management`).
- You have `uv` available and a Python ≥ 3.10 runtime.

## Procedure

### 1. Scaffold project structure

Create the file tree matching the spec. Write in this order so each file can be checked:

```
pyproject.toml        # project metadata + deps + tool config
.gitignore
CHANGELOG.md          # empty for v0.0.0, first entry when tagging
README.md             # start with the spec's contract/usage section
LICENSE               # MIT unless the spec says otherwise
.github/
  CODEOWNERS
  workflows/ci.yml    # lint + test + build (publish is stub)
src/<pkg_name>/
  __init__.py         # re-export public API
  ...
tests/
  __init__.py
```

**pyproject.toml must have**: name, version, description, requires-python, dependencies, [build-system] with hatchling, [tool.ruff], [tool.mypy], [tool.pytest.ini_options].

Use a **version range** (not an exact pin) for runtime deps so each consumer repo can upgrade on its own schedule within the major: `fastmcp>=3.0,<4`.

### 2. Write source files

Match each module from the spec. For each file:

- Run `patch` or `write_file` for each source file.
- The spec's code blocks are the contract — implement them verbatim unless the spec says "suggestions welcome".
- If the spec includes docstrings, keep them; if not, add a module-level docstring.

### 3. Write tests

Create at least one test file per integration axis. For JWT/auth packages:

- `test_token_factory.py` — sanity that the factory produces well-formed tokens (sync)
- `test_auth_integration.py` — async tests against the verifier for every rejection case documented in the spec

Use `pytest-asyncio` with `asyncio_mode = "auto"` in pyproject.toml (no `@pytest.mark.asyncio` needed per-function when auto is set — but explicit markers are safer for CI matrix compat).

### 4. Install and test loop

```bash
# Create venv, sync, install the package as editable
uv venv && source .venv/bin/activate && uv sync --all-extras

# Run tests
uv run pytest -v --tb=short

# Run linter
uv run ruff check src tests

# Run type checker
uv run mypy src
```

Fix errors in this priority: **runtime errors** (test failures) → **type errors** (mypy) → **lint** (ruff).

### 5. Build

```bash
uv build
# Confirm dist/<pkg>-<version>.tar.gz and .whl are produced
```

### 6. Git: commit and tag

```bash
git add -A
git commit -m "feat: initial release of <pkg> v<version>

- Bullet list from the spec's deliverable checklist."
git tag v<version>
git push -u origin main
git push origin v<version>
```

## Decision points

| Situation | Action |
|---|---|
| `gh repo create --source . --clone` fails | These flags are incompatible. Create via `gh repo create <name> --public/--private` alone, then `git remote add origin <url>` and `git push`. |
| Spec says "public" but internal tool | Make the repo private; set `--private` on create. |
| Test helper needs to override settings | Build a base dict of defaults, then `.update(overrides)`, then unpack — avoids "multiple values for keyword argument" at runtime. |
| `**overrides` type annotation | Use `Any`, not `object`, as the dict value type. `**kwargs: object` produces "incompatible type" errors from mypy when unpacking into pydantic constructors. |
| Linter finds auto-fixable errors | Run `ruff check --fix src tests` before manual edits. Common auto-fixables: trailing newlines (W292), import sorting (I001). |
| FastMCP auth integration | Token verification imports from `fastmcp.server.auth` and `fastmcp.server.auth.providers.jwt`. Middleware and auth checks import from `fastmcp.server.middleware` and `fastmcp.server.auth`. Audit logging accesses the token via `fastmcp.server.dependencies.get_access_token()`. |

## Pitfalls

- **Do not combine `--source` and `--clone` on `gh repo create`.** The source flag expects the origin already set via `git init` + `git remote add`; `--clone` and `--source` are mutually exclusive.
- **`**overrides: object` breaks pydantic model construction.** Even though `object` seems type-safe for heterogeneous kwargs, mypy rejects unpacking `dict[str, object]` into a pydantic model requiring specific types. Use `Any`.
- **Base settings + overrides with shared keys cause duplicate-kwarg crashes.** If a helper takes `**overrides` and also passes the same key as a named arg, Python raises `TypeError: got multiple values for keyword argument`. Defend by building the base as a dict and calling `.update(overrides)` before unpacking.
- **LSP import errors for the package's own runtime deps are noise.** Until `uv sync` runs, LSP reports every framework import (fastmcp, pydantic, etc.) as unresolved. Install first, then check diagnostics are from real code bugs, not missing deps.
- **A freshly created empty repo has an unborn `main` branch.** `git log` fails with "does not have any commits yet" — this is expected. Check `git status` and `git branch` for the real state.
- **Tag after the commit, not before.** Create the tag when all files are committed and pushed to main, then push the tag separately. A tag pushed before its target commit creates an orphan tag reference on the remote.