# django-flex-menus Constitution

<!-- Authored at onboarding. Rarely changed; changes go through the constitution pathway
     (human-gated), never mid-feature. Read at the Constitution Check in /plan and by
     reviewers. -->

## Core articles

### Article I — Testing
Every change follows [`docs/contributing/standards/testing.md`](docs/contributing/standards/testing.md): what gets a test
and what does not, the test-first cycle, test structure and fixtures, and the coverage floors.

### Article II — Simplicity
Start with the simplest design that satisfies the spec. New dependencies, new abstractions,
and new infrastructure each require a stated justification in plan.md Complexity Tracking.
YAGNI over speculation.

### Article III — Anti-Abstraction
No wrapper layers, base classes, or "future-proofing" indirection without a present, concrete
second use. Prefer duplication over the wrong abstraction.

### Article IV — Integration-First
Contracts and integration points are designed and tested before internals are polished.
Acceptance scenarios exercise the system the way users touch it.

### Article V — Security & data-safety
Values interpolated into rendered output are escaped through the framework's template layer,
never hand-built string interpolation of model or user data. Secrets live in runtime config,
never in code, fixtures, or version control. Authentication, authorisation, cryptography and
permission changes never take a shortened review path.

### Article VI — Documentation
Public API changes ship their docs in the same PR: README + CHANGELOG updated. Docstrings,
component annotations and code comments follow
[`docs/contributing/standards/code-documentation.md`](docs/contributing/standards/code-documentation.md). If the repo ships
built docs, they must build clean. For a **package**, the README states what the package is,
what it deliberately is not, how to install and configure it, and links to the full documentation.

### Article VII — Dependency discipline
A new runtime dependency requires a stated justification (Simplicity applied to the dependency
tree; prefer the shared `mvp-shared` toolchain bundle over ad-hoc dev deps). `deptry` must pass:
no unused, missing, or transitively-relied-upon dependencies.

### Article VIII — Internationalization
User-facing strings are translatable. In Python (models, forms, views, admin, template tags,
validators) they are wrapped with `gettext_lazy` (imported as `_`); templates load
`{% load i18n %}` and wrap strings with `{% trans %}` / `{% blocktrans %}`. Model `verbose_name`
/ `verbose_name_plural` and form `label` / `help_text` / `error_messages` use `gettext_lazy`; pure
acronyms are exempt. A package ships a base English (`en`) catalog and a `locale/` directory so
host projects can compile or extend translations. CI runs `makemessages` clean over the source as
the i18n gate; correct wrapper usage is otherwise enforced by review, and a hard-coded user-visible
string in a PR is a blocking comment. A package with no user-facing strings satisfies this
trivially.

### Article IX — Data-model conventions (Django)
Every model field is a deliberate indexing decision. Because consumers of a published package cannot
add their own indexes, any field with a plausible lookup / filter / ordering path is indexed at its
definition (`db_index`, `unique`, an FK's automatic index, or a composite `Meta.constraints` /
`Meta.indexes`); a field with no query path stays unindexed to avoid write cost. The choice —
indexed or not, and why — is recorded (plan `data-model.md` or `decisions.md`). `verbose_name` and
`help_text` are mandatory on every model field (Article VIII). **Migrations are consolidated per
PR:** the migrations a feature branch introduces are squashed into as few files as possible before
the PR is submitted (branch-local and unapplied, so safe at any release stage); data migrations
(`RunPython`/`RunSQL`) are exempt from auto-regeneration — keep them via `squashmigrations` or
standalone.

### Article X — Cohesion (Python)
Related behaviour is grouped in a class, not scattered across module-level functions.

**The test:** two or more module-level functions that share a *subject* belong on a class. They
share a subject when they operate on the same data, take the same first argument, are only
meaningful in sequence, or are named around the same noun (`build_x`, `validate_x`, `render_x`).

**Why this is a standard and not a taste.** In a published package, a class is the extension
point. A consumer who needs different behaviour subclasses it and overrides one method. A module
of functions can only be monkey-patched, which is not a supported interface and breaks on any
internal change. Grouping also gives the behaviour a name, a place for shared configuration, and
one import instead of six.

**Shape:** shared state or configuration → a regular class holding it. Grouping for namespacing
with no shared state → still a class, with `@classmethod`/`@staticmethod`, or a small frozen
dataclass carrying the config. Expose a module-level convenience function only as a thin wrapper
over the class, never as the implementation.

**Django first.** Where the framework already owns the grouping, use it rather than inventing a
class: a `QuerySet`/`Manager` method instead of a function taking a queryset, a model method or
property instead of a function taking an instance, a `Form`/`Serializer` method instead of a free
validation function, a `TemplateView` method instead of a helper called by a view.

**Exceptions — narrow, and stated rather than assumed.** A genuinely standalone pure function with
no siblings. Framework-dictated module shapes: `conftest.py` fixtures, migrations, `urls.py`,
`apps.py`, decorator-registered template tags and filters, signal receivers, management-command
entry points. Factory functions that return the class. A module of independent utilities that
genuinely share no subject.

**This does not license abstraction.** Article III still holds: one class grouping today's
behaviour is the goal, not a base class, a registry, or a hierarchy built for a second
implementation that does not exist. Grouping related functions is organisation; adding a layer
between the caller and the work is not.

## Project articles (django-flex-menus-specific)

### Article XI — Compatibility
The supported versions are recorded in `docs/adr/0001-supported-python-and-django-versions.md`
and stated in `pyproject.toml`, the classifiers and the README. Those four agree at all times.
Changing them is an amendment here and a new ADR, never a side effect of a dependency bump.

The public surface is `Menu`, `MenuItem`, the `{% render_menu %}` and `{% render_item %}` template
tags, the `BaseRenderer` subclassing contract, and the `FLEX_MENUS` settings dict. It is
semver-stable: a rename or a removal is a major version, and a deprecation lives at least one
minor release with a warning before it goes. Anything not in that list is internal and may change
in a patch.

### Article XII — Stack norms
uv-managed with a hatchling build backend, and with the development toolchain coming from the shared `mvp-shared` bundle rather
than per-repo pins. CI calls the shared reusable workflows, pinned to a tag and never `@main`.
Documentation is Sphinx and must build clean.

The library ships no templates and no CSS. Markup belongs to a renderer the consumer writes; the
Bootstrap 5 templates under `example/` demonstrate the renderer API and are not a supported
surface. A change that requires the library to know what the consumer's HTML looks like is the
wrong change.

### Article XIII — Visibility rules stay neutral
A `check` is any predicate over the request. The library decides *when* to ask, never *what*
makes an item visible. No check may reach for a permission framework, an authentication backend
or a user model directly: convenience checks live alongside the neutral machinery and are opt-in,
so a consumer with a different notion of visibility is never fighting a built-in assumption.

## Quality bar

Read at plan and review; applies to every change.

- Test coverage: **project ≥ 90%, patch ≥ 85%** (`codecov.yml` is the reference), with a small
  tolerance — floors, not a 100% ratchet.
- Every public API change updates README + CHANGELOG in the same PR.
- Lint, type-check (`mypy`), and `deptry` pass. The lint gate is `pre-commit run --all-files`,
  not a bare `ruff check .`: the hook config excludes `docs/` and migrations, and runs hooks a
  bare invocation does not.
- The package builds and its metadata is valid; the README renders on the package index
  (absolute URLs only — a relative link breaks there); the public API honors the deprecation
  policy in Article XI.
- Documentation builds clean.

Article VIII is satisfied trivially at present and stays in force: the library emits almost no
text of its own, because an item's label comes from the consumer's `extra_context`. The first
user-facing string this package adds is wrapped. Article IX likewise — there are no models, and
adding one brings the article into play rather than being an exception to it.

## Non-negotiables

- Tests, build and lint pass before a change merges. Nobody overrides a red check.
- The default branch requires one approval, and the author of a change never approves it.
- Nothing pushes to the default branch outside a pull request. Releases run through the Prepare
  Release → Tag Release → Publish flow, never a hand-pushed tag.

<!-- The footer below is mandatory and closes every constitution, so a review can name the
     revision it was made against. Versioning is semantic — MAJOR for a removed or redefined
     article, MINOR for a new article or materially expanded guidance, PATCH for clarification
     and wording. Every amendment updates the version and the Last Amended date; Ratified never
     changes after the first adoption. -->

---

**Version**: 2.0.0 | **Ratified**: 2026-09-16 | **Last Amended**: 2026-09-28
