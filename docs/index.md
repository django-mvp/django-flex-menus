# Django Flex Menus

A flexible, developer-friendly Django package for building dynamic, context-aware navigation menus with minimal boilerplate.

## Features

- **Flexible API**: Simple `Menu` and `MenuItem` classes for building flexible tree structures using the [anytree](https://github.com/c0fec0de/anytree) API.
- **Flexible Rendering**: Reusable class-based renderers that can be used with any menu structure.
- **Flexible URL resolution**: Django view names, static URLs, or callable functions with automatic parameter filtering
- **Flexible Visibility**: Show/hide items based on user permissions, authentication, request attributes, database objects.

## Installation

```bash
pip install django-flex-menus
```

Add to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ...
    'flex_menu',
]
```

## Quick Start

**1. Define a menu** (e.g., in `myapp/menus.py`):

```python
from flex_menu import Menu, MenuItem

# Create main navigation
main_nav = Menu(
    "main_nav",
    children=[
        MenuItem(name="home", view_name="home"),
        MenuItem(name="about", view_name="about"),
        MenuItem(
            name="products",
            children=[
                MenuItem(name="product_a", view_name="products:detail"),
                MenuItem(name="product_b", view_name="products:detail"),
            ],
        ),
    ],
)
```

**2. Use in templates with URL parameters**:

```django
{% render_menu 'main_nav' slug="product-a" %}
```

**3. Configure renderers** (in `settings.py`):

```python
FLEX_MENUS = {
    "renderers": {
        "bootstrap5": "myproject.renderers.Bootstrap5NavbarRenderer",
        "sidebar": "myproject.renderers.Bootstrap5SidebarRenderer",
    },
}
```

**3. Render in template**:

```django
{% load flex_menu %}

<!DOCTYPE html>
<html>
<head>
    <title>My Site</title>
</head>
<body>
    {% render_menu 'main_nav' renderer='bootstrap5' %}
    <!-- CSS/JS automatically included before the menu -->
</body>
</html>
```

## Documentation

```{toctree}
:maxdepth: 2

getting-started
building-menus
manipulating-menus
template-usage
visibility-checks
custom-renderers
api/index
```

```{toctree}
:caption: Contributing
:maxdepth: 1

contributing/standards/testing
contributing/standards/code-documentation
```

## License

MIT License - see LICENSE file for details.
