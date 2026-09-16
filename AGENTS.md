# AGENTS.md — Agent Configuration for django-flex-menus

<!-- Thin index only — bloat here = ignored instructions. Details live in the pointed-to files. -->

django-flex-menus builds named Menu trees in Python, then renders them through a Renderer chosen
at the template tag. A Menu holds Items — Links, Actions and Decorations — each with a Check that
decides whether it is visible for the current request. `CONTEXT.md` defines these terms; use them.

## Stack & commands

- **Stack:** Python 3.12+ / Django 5.2 and 6.0, Poetry-managed, built on [anytree](https://github.com/c0fec0de/anytree)
- **Install:** `poetry install`
- **Test:** `poetry run pytest`
- **Lint:** `poetry run pre-commit run --all-files` (ruff lint + format, mypy, deptry)
- **Type-check:** `poetry run mypy`
- **Build:** `poetry build`
- **Docs:** `poetry run sphinx-build -E -b html docs docs/_build`

Lint is the pre-commit run, not a bare `ruff check .`: the hook config excludes `docs/`,
migrations and `tests/`, and a raw invocation reports findings in paths the gate does not cover.

## Agent skills

### Issue tracker

Issues tracked in GitHub Issues via the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

Default label vocabulary mapped 1:1 to canonical roles (needs-triage, needs-info, ready-for-agent,
ready-for-human, wontfix). See `docs/agents/triage-labels.md`.

### Domain docs

Single-context layout — one `CONTEXT.md` at root and `docs/adr/` for architectural decisions.
See `docs/agents/domain.md`.

### CI checks

CI runs from the shared reusable workflows in `django-mvp/shared`, pinned at `v0.4.1`. Because
they are called rather than inlined, every status check carries its caller job as a prefix.
The required checks are:

- `call-build / Code Quality`
- `call-build / Security Scan`
- `call-build / Build Package`
- `call-tests / Test Python 3.12, Django 5.2`
- `call-tests / Test Python 3.12, Django 6.0`
- `call-tests / Test Python 3.13, Django 5.2`
- `call-tests / Test Python 3.13, Django 6.0`

`tests.yml` and `build.yml` deliberately carry no `paths:` filter on `pull_request`. A required
check that is filtered out never reports, and a check that never reports blocks the merge.

## Releasing

Releases run through the shared release flow, never by hand and never by pushing a tag.

1. Dispatch **Prepare Release** with a bump level. It opens a PR carrying the version bump and
   the CHANGELOG section.
2. Merging that PR is the release decision. **Tag Release** then cuts the tag and the GitHub
   Release from the merge commit.
3. **Publish** uploads to PyPI through trusted publishing. PyPI's trusted publisher is bound to
   the `publish.yml` filename — renaming that file breaks publishing until the PyPI project
   settings are changed to match.

`pyproject.toml` holds the version and is the single source of truth for all three steps.

## Development workflow

Feature work follows a spec-driven process: spec → plan → tasks → implement → review → PR, with
`specs/NNN-slug/` directories generated per feature (there is no Spec Kit install in the repo).
Project standards and the quality bar live in `CONSTITUTION.md`.
