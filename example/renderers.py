"""Example renderers demonstrating Bootstrap 5 support for django-flex-menus.

These are demonstrative renderers, not part of the core package, meant as
examples for building your own renderers.
"""

from flex_menu.menu import MenuItem
from flex_menu.renderers import BaseRenderer


class Bootstrap5NavbarRenderer(BaseRenderer):
    """Bootstrap 5 navbar renderer.

    Renders menus as Bootstrap 5 navbar with dropdown support.
    Supports up to 2 levels of nesting (navbar -> dropdown -> items).

    This is a demonstrative renderer - adapt it to your needs.
    """

    templates = {
        0: {"default": "bootstrap5/navbar/navbar.html"},
        1: {
            "parent": "bootstrap5/navbar/dropdown_menu.html",  # Top-level with children = dropdown
            "leaf": "bootstrap5/navbar/item.html",  # Top-level without children = nav link
        },
        2: {
            "parent": "bootstrap5/navbar/dropdown_item.html",  # Nested dropdown (rare)
            "leaf": "bootstrap5/navbar/dropdown_item.html",  # Dropdown item
        },
    }

    def get_template(self, item: MenuItem) -> str:
        """Route dividers to their own template."""
        if item.extra_context.get("divider", False):
            return "bootstrap5/navbar/divider.html"

        return super().get_template(item)


class Bootstrap5SidebarRenderer(BaseRenderer):
    """Bootstrap 5 sidebar renderer using list-group.

    Renders menus as Bootstrap 5 list-group with collapsible sections.
    Supports multiple levels of nesting.

    This is a demonstrative renderer - adapt it to your needs.
    """

    templates = {
        0: {"default": "bootstrap5/sidebar/container.html"},
        1: {
            "parent": "bootstrap5/sidebar/collapsible_group.html",  # Top-level with children
            "leaf": "bootstrap5/sidebar/item.html",  # Top-level without children
        },
        "default": {
            "parent": "bootstrap5/sidebar/nested_group.html",  # Nested group
            "leaf": "bootstrap5/sidebar/sub_item.html",  # Nested item
        },
    }

    def get_template(self, item: MenuItem) -> str:
        """Route dividers to their own template."""
        if item.extra_context.get("divider", False):
            return "bootstrap5/sidebar/divider.html"

        return super().get_template(item)
