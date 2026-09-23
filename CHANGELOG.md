# Changelog

All notable changes to this project are documented in this file. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Releases before v0.5.0 predate this file. Their notes are on the
[releases page](https://github.com/django-mvp/django-flex-menus/releases).

## [Unreleased]

## [v0.4.6] - 2026-09-23

### Fixed

- **The package installs on Django 5.2 again.** A dependency update had rewritten the runtime
  requirement from `django>=5.2` to `django>=6.1.1`, so v0.4.4 and v0.4.5 could not be resolved
  by any project pinned below Django 6.1.1. Projects that reach this package indirectly through
  `django-mvp` were affected the same way, with no change of theirs asking for it. Nothing in
  the package uses a Django 6 API and the test matrix has run 5.2 and 6.0 throughout, so the
  lower bound is back to `django>=5.2` — what
  [ADR 0001](docs/adr/0001-supported-python-and-django-versions.md), the classifiers and the
  README's Requirements section have said all along.

### Changed

- Automated dependency updates no longer rewrite the runtime requirements on `django` and
  `anytree`. For a library those constraints state which versions are supported, so widening or
  narrowing them is a decision recorded in ADR 0001 rather than a side effect of whichever
  release was newest that week. Development dependencies keep updating weekly as before. The
  test suite now also checks that the declared range, the classifiers and the README agree, so
  the next attempt to raise the floor fails in CI.

## [v0.4.5] - 2026-09-22

### Fixed

- **A menu item whose URL came from `reverse_lazy` no longer raises
  `AttributeError: '__proxy__' object has no attribute 'decode'`** while working out whether
  it points at the current request. `reverse_lazy` is how a menu declared at module level has
  to resolve its URLs, because the URLconf is not loaded when the module is imported, so this
  reached most menus built the ordinary way. Selection matching in v0.4.4 passed the item's URL
  to `urlsplit`, which accepts only `str` or `bytes`; the lazy proxy is now resolved first.
  Introduced in v0.4.4 by the change to match items by resolved view name.

## [v0.4.4] - 2026-09-22

### Changed

- **Breaking:** the supported versions are now Python 3.12+ and Django 5.2 or 6.0. Python 3.11
  and Django 4.2, 5.0 and 5.1 are no longer supported. The 3.11 claim was never tested and the
  package could not be installed alongside its own development tooling on that version.

### Fixed

- **`{% render_menu %}` and `{% process_menu %}` no longer raise `KeyError: 'request'` when
  the template context carries no request.** They draw no menu instead. Django renders the
  production error page in exactly that context — `django.views.defaults.server_error` calls
  `template.render()` with no context and no request — so a project whose `500.html` drew a
  menu raised inside its own error page and the original error was never reported. A template
  naming a menu that does not exist still raises, request or no request, and visibility check
  functions are never called without a request, so their signature is unchanged.
- The README documented a `FLEX_MENU_LOG_URL_FAILURES` setting that nothing read. Logging of
  unresolvable destinations has always been controlled by `FLEX_MENUS["log_url_failures"]`,
  which is what the README now describes.
- The README documented `allowed_children` child-type validation and gave examples using it.
  No such attribute exists; the examples could not have worked. The section has been removed
  and the request is tracked as
  [#1](https://github.com/django-mvp/django-flex-menus/issues/1).
- The README linked to `CONFIGURATION.md`, `PERFORMANCE.md`, `THREAD_SAFETY.md` and
  `THEME_CLASSES.md`, none of which exist in the repository.
