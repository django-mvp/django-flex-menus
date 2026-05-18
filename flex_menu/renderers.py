"""
Renderer system for django-flex-menus.

Renderers handle the presentation layer, converting processed menu items
into HTML using templates. This decouples menu structure/logic from rendering.
"""

import logging
from typing import Any

from django.conf import settings
from django.forms import Media
from django.template.loader import render_to_string
from django.utils.module_loading import import_string
from django.utils.safestring import mark_safe

from .menu import MenuItem

logger = logging.getLogger(__name__)


class BaseRenderer:
    """
    Base renderer class for menu rendering.

    Renderers define how menu items are presented using templates.
    Templates are selected based on menu depth and properties.

    Attributes:
        templates (dict): Mapping of depth -> template configuration.
                         Each depth can have 'parent' and 'leaf' templates,
                         or just 'default'. If a depth is not found, uses
                         the 'default' key if present, otherwise raises error.

    Media (optional):
        Inner class defining CSS and JS dependencies for this renderer.
        Similar to Django's Form.Media and ModelAdmin.Media pattern.

    Example:
        class MyRenderer(BaseRenderer):
            templates = {
                0: {'default': 'menu/container.html'},
                1: {
                    'parent': 'menu/dropdown.html',
                    'leaf': 'menu/item.html',
                },
            }

            class Media:
                css = {
                    'all': ('menu/styles.css',)
                }
                js = ('menu/scripts.js',)
    """

    templates: dict[int | str, dict[str, str]] = {
        "default": {
            "parent": "menu/group.html",
            "leaf": "menu/item.html",
        }
    }

    def __init__(self):
        """Initialize renderer and setup media if defined."""
        # Check if renderer defines a Media class
        if hasattr(self, "Media"):
            self._media = Media(getattr(self, "Media"))
        else:
            self._media = Media()

    @property
    def media(self):
        """
        Return media assets (CSS/JS) required by this renderer.

        Returns:
            django.forms.Media instance with CSS and JS files.
        """
        return self._media

    def get_template(self, item: MenuItem) -> str:
        """
        Get the template path for a menu item based on depth and properties.

        Args:
            item: The menu item to render.

        Returns:
            Template path string.

        Raises:
            ValueError: If no template found for this depth and no default provided.
        """
        depth = item.depth

        # Try to get templates for this specific depth
        depth_templates = self.templates.get(depth)

        if not depth_templates:
            # Try to use default templates
            depth_templates = self.templates.get("default")

            if not depth_templates:
                # No default provided - raise error
                supported_depths = [k for k in self.templates.keys() if k != "default"]
                raise ValueError(
                    f"Renderer {self.__class__.__name__} does not support depth {depth}. "
                    f"Supported depths: {supported_depths}. "
                    f"Add a 'default' key to templates dict to handle arbitrary depths."
                )

        # Determine template key based on item properties
        if item.has_children:
            template_key = "parent"
        else:
            template_key = "leaf"

        # Get the actual template path
        template = depth_templates.get(template_key)

        if not template:
            # Fall back to default if specific key not found
            template = depth_templates.get("default")

        if not template:
            raise ValueError(
                f"Renderer {self.__class__.__name__} has no template for "
                f"depth={depth}, key='{template_key}'. "
                f"Available keys: {list(depth_templates.keys())}"
            )

        return template

    def get_context_data(self, item: MenuItem, **kwargs) -> dict[str, Any]:
        """
        Build context data for template rendering.

        Args:
            item: The menu item to render.
            **kwargs: Additional context data.

        Returns:
            Dictionary of context data for the template.
        """
        context = {
            "item": item,
            "renderer": self,
            "depth": item.depth,
            "visible": item.visible,
            "children": item.visible_children,
            "selected": item.selected,
            "label": item.name,
            "url": item.url if item.url else None,
            # Extra context from menu item
            **item.extra_context,
            **kwargs,
        }

        return context

    def render(self, item: MenuItem, **kwargs) -> str:
        """
        Render a menu item using its template.

        Args:
            item: The menu item to render.
            **kwargs: Additional context data.

        Returns:
            Rendered HTML string, or empty string if item is not visible.
        """
        if not item.visible:
            return ""

        template = self.get_template(item)
        context = self.get_context_data(item, **kwargs)

        return mark_safe(render_to_string(template, context))


def get_renderer(name: str | None = None) -> BaseRenderer:
    """
    Get a renderer instance by name from settings.

    Loads renderer class path from FLEX_MENUS['renderers'] dict in settings.
    If no name provided, uses FLEX_MENUS['default_renderer'].

    Args:
        name: Renderer name or None for default.

    Returns:
        Renderer instance.

    Raises:
        ValueError: If renderer not found in settings.
        ImportError: If renderer class cannot be imported.

    Example:
        # In settings.py
        FLEX_MENUS = {
            'renderers': {
                'bootstrap5': 'myapp.renderers.Bootstrap5Renderer',
                'tailwind': 'myapp.renderers.TailwindRenderer',
            },
            'default_renderer': 'bootstrap5',
        }

        # In code or template
        renderer = get_renderer('bootstrap5')
        html = renderer.render(menu_item)
    """
    config = getattr(settings, "FLEX_MENUS", {})
    renderers = config.get("renderers", {})

    # Determine which renderer to use
    if name is None:
        name = config.get("default_renderer", "default")

    # Get renderer path
    renderer_path = renderers.get(name)

    if not renderer_path:
        # If 'default' requested and not in config, use BaseRenderer
        if name == "default":
            return BaseRenderer()

        available = list(renderers.keys())
        raise ValueError(
            f"Renderer '{name}' not found in FLEX_MENUS['renderers']. "
            f"Available renderers: {available or ['(none configured)']}. "
            f"Add to settings.py: FLEX_MENUS = {{ 'renderers': {{ '{name}': 'path.to.RendererClass' }} }}"
        )

    # Import and instantiate renderer class
    try:
        renderer_class = import_string(renderer_path)
    except ImportError as e:
        raise ImportError(f"Cannot import renderer '{name}' from '{renderer_path}': {e}") from e

    # Validate renderer has required methods
    if not hasattr(renderer_class, "render"):
        raise TypeError(f"Renderer class '{renderer_path}' must have a 'render' method")

    return renderer_class()  # type: ignore[no-any-return]
