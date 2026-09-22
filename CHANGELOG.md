# Changelog

All notable changes to this project are documented in this file. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Releases before v0.5.0 predate this file. Their notes are on the
[releases page](https://github.com/django-mvp/django-flex-menus/releases).

## [Unreleased]

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
