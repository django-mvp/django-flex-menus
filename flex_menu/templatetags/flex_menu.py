"""Template tags for processing and rendering flex_menu menus."""

from django import template
from django.template import TemplateSyntaxError
from django.utils.safestring import mark_safe

from flex_menu import root
from flex_menu.renderers import get_renderer

register = template.Library()


@register.simple_tag(takes_context=True)
def process_menu(context, menu, **kwargs):
    """Process a menu for the current request.

    Caches the processed menu on the request object to avoid re-processing
    if the same menu is rendered multiple times on the same page.

    A context with no request yields no menu. Django renders the production
    error page that way — django.views.defaults.server_error calls
    template.render() with no context and no request — and a menu has no user
    to decide visibility from in that case anyway. Raising there would bury the
    error the page exists to report.

    Args:
        context: Template context. Yields None when it carries no 'request'.
        menu: Menu name (str) or MenuItem instance.
        **kwargs: Context variables passed to check functions and URL resolution.
                 All kwargs are passed to check functions for visibility decisions.
                 For view_name items, kwargs are filtered to match URL parameters.
                 For callable URLs, all kwargs are passed through.

    Returns:
        Processed MenuItem instance, or None if the menu is not found or the
        context carries no request.

    Raises:
        template.TemplateSyntaxError: If menu is given by name and no such
            menu exists.
    """
    if isinstance(menu, str):
        menu_name = menu
        found_menu = root.get(menu_name)
        if not found_menu:
            raise template.TemplateSyntaxError(
                f"Menu '{menu_name}' does not exist. Run 'python manage.py render_menu' to examine the full menu tree."
            )
        menu = found_menu
    else:
        menu_name = menu.name

    if not menu:
        return None

    # Resolved after the menu lookup, so a template naming a menu that does not
    # exist still says so whether or not a request is present.
    request = context.get("request")
    if request is None:
        return None

    cache_key = f"_processed_menu_{menu_name}_{id(request)}"

    processed = getattr(request, cache_key, None)

    if processed is None:
        processed = menu.process(request, **kwargs)
        setattr(request, cache_key, processed)

    return processed


@register.simple_tag(takes_context=True)
def render_menu(context, menu, renderer=None, include_media=True, **kwargs):
    """Process and render a menu with the specified renderer.

    Media (CSS/JS) is automatically included in the output (CSS before the menu,
    JS after) unless include_media=False is specified.

    Args:
        context: Template context. Renders nothing when it carries no
                 'request' — see process_menu.
        menu: Menu name (str) or MenuItem instance.
        renderer: Renderer name (str). Required.
        include_media: Whether to include renderer's CSS/JS (default: True).
        **kwargs: Context variables passed to check functions and URL resolution.
                 All kwargs are passed to check functions for visibility decisions.
                 For view_name items, kwargs are filtered to match URL parameters.
                 For callable URLs, all kwargs are passed through.

    Returns:
        Rendered HTML string with media included.

    Raises:
        TemplateSyntaxError: If no renderer is given.

    Example:
        ::

            {% render_menu "main_navigation" renderer="sidebar" %}
            {% render_menu "project_menu" renderer="simple" project=project pk=project.pk %}
            {% render_menu "sidebar" renderer="simple" include_media=False user=user %}
    """
    processed_menu = process_menu(context, menu, **kwargs)

    if not processed_menu:
        return ""

    if renderer is None:
        raise TemplateSyntaxError(
            "render_menu requires a 'renderer' parameter. Example: {% render_menu 'main_nav' renderer='bootstrap5' %}"
        )

    renderer_instance = (
        get_renderer(renderer) if isinstance(renderer, str) else renderer
    )

    menu_html = renderer_instance.render(processed_menu, **kwargs)

    if include_media and hasattr(renderer_instance, "media"):
        media_html = str(renderer_instance.media)
        if media_html:
            # Both halves are renderer output: the media tags come from the
            # renderer's own Media declaration and menu_html is already marked
            # safe by the renderer, which autoescaped as it rendered.
            return mark_safe(f"{media_html}\n{menu_html}")  # noqa: S308

    return mark_safe(menu_html)  # noqa: S308


@register.simple_tag(takes_context=True)
def render_item(context, item, renderer=None, **kwargs):
    """Render a single menu item (for recursive rendering in templates).

    Use this tag in renderer templates to recursively render child items.

    Args:
        context: Template context.
        item: MenuItem instance to render.
        renderer: Renderer name (str) or renderer instance.
        **kwargs: Additional context passed to renderer.

    Returns:
        Rendered HTML string.

    Example:
        ::

            {% for child in item.visible_children %}
              {% render_item child renderer=renderer %}
            {% endfor %}
    """
    if not item or not item.visible:
        return ""

    if isinstance(renderer, str):
        renderer_instance = get_renderer(renderer)
    elif renderer is None:
        renderer_instance = get_renderer()
    else:
        renderer_instance = renderer

    return renderer_instance.render(item, **kwargs)
