# django-flex-menus

[![Tests](https://github.com/django-mvp/django-flex-menus/actions/workflows/tests.yml/badge.svg)](https://github.com/django-mvp/django-flex-menus/actions/workflows/tests.yml)
[![Build](https://github.com/django-mvp/django-flex-menus/actions/workflows/build.yml/badge.svg)](https://github.com/django-mvp/django-flex-menus/actions/workflows/build.yml)
[![codecov](https://codecov.io/gh/django-mvp/django-flex-menus/branch/main/graph/badge.svg)](https://codecov.io/gh/django-mvp/django-flex-menus)
[![PyPI](https://img.shields.io/pypi/v/django-flex-menus)](https://pypi.org/project/django-flex-menus/)
[![Python](https://img.shields.io/pypi/pyversions/django-flex-menus)](https://pypi.org/project/django-flex-menus/)
[![License](https://img.shields.io/github/license/django-mvp/django-flex-menus)](https://github.com/django-mvp/django-flex-menus/blob/main/LICENSE)

Flexible site menus for Django.

Site navigation usually ends up spread between templates, context processors and a pile of
`{% if perms %}` blocks, which makes it hard to see what the menu actually contains and harder
still to render the same menu twice in two different shapes. django-flex-menus moves the
structure into Python: you declare a named tree once, attach a visibility rule to any part of
it, and templates ask for it by name and choose how it is drawn.

## Scope & philosophy

**What it is.** A tree of menu items, declared in Python and rendered through a renderer you
choose at the point of use. The tree carries structure, destinations and visibility rules. The
renderer carries the markup.

**What it deliberately is not.**

- **Not a theme, and not a set of templates.** No markup ships as the supported surface. The
  `example/` project contains Bootstrap 5 templates to demonstrate the renderer API, not to be
  imported from your project.
- **Not a permissions system.** A visibility rule is any predicate — a permission check, a
  subscription tier, a feature flag, the time of day. The library never decides what makes an
  item visible, only when to ask.
- **Not a database model.** Menus are code, defined at startup and versioned with your project.
  There is no editing interface and no migration.
- **Not a URL router.** Destinations resolve through Django's own resolver.

**When those pull against each other,** the structure wins over the markup. Anything that would
require the library to know what your HTML looks like belongs in a renderer instead.

## Requirements

- Python 3.12+
- Django 5.2, 6.0 or 6.1

## Installation

```bash
pip install django-flex-menus
```

Add the app to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ...
    "flex_menu",
]
```

There are no models, so no migration is needed.

## Quick start

Declare a menu in `myapp/menus.py`. Naming a `Menu` attaches it to the global tree, which is
what makes it reachable by name from a template:

```python
from flex_menu import Menu, MenuItem

main_nav = Menu(
    "main_nav",
    children=[
        MenuItem(name="home", view_name="home"),
        MenuItem(name="dashboard", view_name="dashboard"),
    ],
)
```

Point a renderer at your markup in `settings.py`:

```python
FLEX_MENUS = {
    "renderers": {
        "navbar": "myapp.renderers.NavbarRenderer",
        "sidebar": "myapp.renderers.SidebarRenderer",
    },
}
```

Then render it, as many times and in as many shapes as you need:

```django
{% load flex_menu %}

<nav>{% render_menu 'main_nav' renderer='navbar' %}</nav>
<aside>{% render_menu 'main_nav' renderer='sidebar' %}</aside>
```

## Controlling visibility

Every item takes a `check`: a boolean, or a callable receiving the request and any keyword
arguments passed to `{% render_menu %}`. An item whose check returns false is dropped, as is an
item whose URL cannot be resolved.

```python
MenuItem(
    name="billing",
    view_name="billing",
    check=lambda request, **kwargs: request.user.is_authenticated,
)
```

## Working with a menu

```python
main_nav.append(MenuItem(name="reports", view_name="reports"))
main_nav.extend([item_one, item_two])
main_nav.insert(item, 2)
main_nav.insert_after(item, "home")

reports = main_nav.get("reports")
reports.pop()
```

Run `python manage.py render_menu` to print the whole tree, or `--name <menu>` for one of them.

## Configuration

Everything lives under a single `FLEX_MENUS` dict:

```python
FLEX_MENUS = {
    "renderers": {
        "navbar": "myapp.renderers.NavbarRenderer",
    },
    # Used when {% render_menu %} is given no renderer
    "default_renderer": "navbar",
    # Whether unresolvable destinations are logged. Defaults to DEBUG.
    "log_url_failures": False,
}
```

## Thread safety

Menus are declared once at startup and shared across the process, so processing never mutates
the declared tree — each request works against its own copy. That copy is real work on every
render, so keep visibility checks cheap: they run for every item, on every request.

## Documentation

Full documentation, including the renderer API and how to write your own, is at
<https://django-mvp.github.io/django-flex-menus/>.

## Changelog

See [CHANGELOG.md](https://github.com/django-mvp/django-flex-menus/blob/main/CHANGELOG.md).

## License

MIT — see [LICENSE](https://github.com/django-mvp/django-flex-menus/blob/main/LICENSE).
