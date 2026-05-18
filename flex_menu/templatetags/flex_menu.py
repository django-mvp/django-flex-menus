from django import template
from django.template import TemplateSyntaxError
from django.utils.safestring import mark_safe

from flex_menu import root
from flex_menu.renderers import get_renderer

register = template.Library()


@register.simple_tag(takes_context=True)
def process_menu(context, menu, **kwargs):
    """
    Process a menu for the current request.

    Caches the processed menu on the request object to avoid re-processing
    if the same menu is rendered multiple times on the same page.

    Args:
        context: Template context (must contain 'request').
        menu: Menu name (str) or MenuItem instance.
        **kwargs: Context variables passed to check functions and URL resolution.
                 All kwargs are passed to check functions for visibility decisions.
                 For view_name items, kwargs are filtered to match URL parameters.
                 For callable URLs, all kwargs are passed through.

    Returns:
        Processed MenuItem instance or None if menu not found.
    """
    request = context["request"]

    # Get menu instance
    if isinstance(menu, str):
        menu_name = menu
        found_menu = root.get(menu_name)
        if not found_menu:
            raise template.TemplateSyntaxError(
                f"Menu '{menu_name}' does not exist. "
                "Run 'python manage.py render_menu' to examine the full menu tree."
            )
        menu = found_menu
    else:
        menu_name = menu.name

    if not menu:
        return None

    # Create cache key based on menu name and request ID
    cache_key = f"_processed_menu_{menu_name}_{id(request)}"

    # Check if already processed for this request
    processed = getattr(request, cache_key, None)

    if processed is None:
        # Process once per request
        processed = menu.process(request, **kwargs)
        # Cache on request object
        setattr(request, cache_key, processed)

    return processed


@register.simple_tag(takes_context=True)
def render_menu(context, menu, renderer=None, include_media=True, **kwargs):
    """
    Process and render a menu with the specified renderer.

    Media (CSS/JS) is automatically included in the output (CSS before the menu,
    JS after) unless include_media=False is specified.

    Args:
        context: Template context (must contain 'request').
        menu: Menu name (str) or MenuItem instance.
        renderer: Renderer name (str). Required.
        include_media: Whether to include renderer's CSS/JS (default: True).
        **kwargs: Context variables passed to check functions and URL resolution.
                 All kwargs are passed to check functions for visibility decisions.
                 For view_name items, kwargs are filtered to match URL parameters.
                 For callable URLs, all kwargs are passed through.

    Returns:
        Rendered HTML string with media included.

    Example:
        {% render_menu "main_navigation" renderer="sidebar" %}
        {% render_menu "project_menu" renderer="simple" project=project pk=project.pk %}
        {% render_menu "sidebar" renderer="simple" include_media=False user=user %}
    """
    # Process menu (with caching)
    processed_menu = process_menu(context, menu, **kwargs)

    if not processed_menu:
        return ""

    # Require renderer parameter
    if renderer is None:
        raise TemplateSyntaxError(
            "render_menu requires a 'renderer' parameter. "
            "Example: {% render_menu 'main_nav' renderer='bootstrap5' %}"
        )

    # Get renderer instance (or use if already an instance)
    if isinstance(renderer, str):
        renderer_instance = get_renderer(renderer)
    else:
        # Assume it's already a renderer instance
        renderer_instance = renderer

    # Render menu content
    menu_html = renderer_instance.render(processed_menu, **kwargs)

    # Include media if requested
    if include_media and hasattr(renderer_instance, "media"):
        media_html = str(renderer_instance.media)
        if media_html:
            # Media HTML contains link and script tags
            # Place before menu content (crispy-forms style)
            return mark_safe(f"{media_html}\n{menu_html}")

    return mark_safe(menu_html)


@register.simple_tag(takes_context=True)
def render_item(context, item, renderer=None, **kwargs):
    """
    Render a single menu item (for recursive rendering in templates).

    Use this tag in renderer templates to recursively render child items.

    Args:
        context: Template context.
        item: MenuItem instance to render.
        renderer: Renderer name (str) or renderer instance.
        **kwargs: Additional context passed to renderer.

    Returns:
        Rendered HTML string.

    Example:
        {# In a renderer template #}
        {% for child in item.visible_children %}
          {% render_item child renderer=renderer %}
        {% endfor %}
    """
    if not item or not item.visible:
        return ""

    # If renderer is a string, get the instance
    if isinstance(renderer, str):
        renderer_instance = get_renderer(renderer)
    elif renderer is None:
        renderer_instance = get_renderer()
    else:
        # Assume it's already a renderer instance
        renderer_instance = renderer

    # Render the item
    return renderer_instance.render(item, **kwargs)
