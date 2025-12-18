"""
Utility functions for django-flex-menus.

This module contains helper functions for URL resolution and parameter extraction.
"""

import logging
from functools import lru_cache

from django.urls import get_resolver
from django.urls.exceptions import NoReverseMatch


@lru_cache(maxsize=None)
def get_required_url_params(view_name):
    """
    Given a Django view_name (as used in reverse()), return the names of the
    required URL parameters (e.g. ['pk'] or ['slug']).

    Supports both simple view names ('home') and namespaced view names ('app:home').

    This function uses Django's internal reverse_dict for efficiency, with a fallback
    to tree-walking for edge cases.
    """
    from django.urls.resolvers import URLPattern, URLResolver

    resolver = get_resolver()

    # Fast path: Try to use Django's pre-built reverse_dict
    try:
        matches = resolver.reverse_dict.get(view_name)
        if matches:
            all_params = set()
            # reverse_dict structure: view_name -> [(pattern, (args_list, kwargs_list, defaults_dict)), ...]
            for _pattern, params_tuple in matches:
                # params_tuple is typically: ([args], [kwargs], {defaults})
                # We want the kwargs list (index 1)
                if isinstance(params_tuple, (list, tuple)) and len(params_tuple) > 1:
                    kwargs_list = params_tuple[1]
                    if kwargs_list:
                        all_params.update(kwargs_list)

            # If we found params via reverse_dict, return them
            if all_params or matches:  # matches exist even if no params (e.g., parameterless URLs)
                return all_params
    except (AttributeError, KeyError, IndexError, TypeError):
        # reverse_dict structure might vary between Django versions or be unavailable
        pass

    # Fallback: Walk the URL pattern tree (original implementation)
    params = set()
    found = False

    def walk(patterns, namespace_prefix="", parent_params=None):
        """Recursively walk URL patterns to find matches.

        Args:
            patterns: List of URL patterns to walk
            namespace_prefix: Current namespace prefix (e.g., "admin:")
            parent_params: Parameters from parent resolvers to accumulate
        """
        nonlocal found
        if parent_params is None:
            parent_params = set()

        for pattern in patterns:
            if isinstance(pattern, URLPattern):
                # Build full name including any namespace prefix
                if pattern.name:
                    full_name = f"{namespace_prefix}{pattern.name}"
                    if full_name == view_name:
                        found = True
                        # Add parameters from parent resolvers
                        params.update(parent_params)
                        # Extract parameters from this pattern
                        pat = pattern.pattern
                        # Django 2.0+ RoutePattern (has 'converters')
                        if hasattr(pat, "converters") and pat.converters:
                            params.update(pat.converters.keys())
                        # RegexPattern (older style) - use regex groupindex
                        elif hasattr(pat, "regex"):
                            try:
                                params.update(pat.regex.groupindex.keys())
                            except Exception:
                                pass
            elif isinstance(pattern, URLResolver):
                # Extract parameters from this resolver's pattern
                resolver_params = set(parent_params)  # Copy parent params
                pat = pattern.pattern
                if hasattr(pat, "converters") and pat.converters:
                    resolver_params.update(pat.converters.keys())
                elif hasattr(pat, "regex"):
                    try:
                        resolver_params.update(pat.regex.groupindex.keys())
                    except Exception:
                        pass

                # Accumulate namespace if present
                ns = pattern.namespace
                new_prefix = namespace_prefix
                if ns:
                    new_prefix = f"{namespace_prefix}{ns}:"
                # Recursively walk nested patterns with accumulated params
                walk(pattern.url_patterns, new_prefix, resolver_params)

    # Walk the URL pattern tree
    walk(resolver.url_patterns, "")

    if not found:
        raise NoReverseMatch(f"No URL pattern found for view name '{view_name}'.")

    return params


def warm_url_params_cache():
    """
    Pre-populate the get_required_url_params cache with all registered URL patterns.

    This function should be called during Django app initialization to ensure that
    all URL parameter lookups are fast from the start, avoiding the initial overhead
    of cache misses.

    This walks the URL pattern tree once and caches the parameter names for every
    named URL pattern in the project.
    """
    from django.urls.resolvers import URLPattern, URLResolver

    resolver = get_resolver()
    cached_count = 0

    def walk(patterns, namespace_prefix=""):
        """Recursively walk URL patterns and cache parameter names.

        Args:
            patterns: List of URL patterns to walk
            namespace_prefix: Current namespace prefix (e.g., "admin:")
        """
        nonlocal cached_count

        for pattern in patterns:
            if isinstance(pattern, URLPattern):
                # Cache this pattern's parameters if it has a name
                if pattern.name:
                    full_name = f"{namespace_prefix}{pattern.name}"
                    try:
                        # This will cache the result
                        get_required_url_params(full_name)
                        cached_count += 1
                    except NoReverseMatch:
                        # Some patterns might not be reversible, skip them
                        pass
            elif isinstance(pattern, URLResolver):
                # Accumulate namespace if present
                ns = pattern.namespace
                new_prefix = namespace_prefix
                if ns:
                    new_prefix = f"{namespace_prefix}{ns}:"
                # Recursively walk nested patterns
                try:
                    walk(pattern.url_patterns, new_prefix)
                except Exception:
                    # Some resolvers might have issues, skip them
                    pass

    # Walk all URL patterns and cache them
    try:
        walk(resolver.url_patterns, "")
        logger = logging.getLogger(__name__)
        logger.debug(f"Warmed URL params cache with {cached_count} URL patterns")
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to warm URL params cache: {e}")


def serialize_menu(menu_item, **options):
    """
    Serialize a processed menu item to JSON.

    This utility function converts a processed menu item into a JSON string
    that can be used with frontend frameworks like Alpine.js, Vue, React, etc.

    Args:
        menu_item: A processed MenuItem instance (i.e., after calling .process(request)).
        **options: Additional options for serialization.
            - include_children (bool): Whether to include children. Default is True.
            - indent (int | None): JSON indentation for pretty printing. Default is None.

    Returns:
        JSON string representation of the menu.

    Example:
        >>> menu = root.get('main_nav').process(request)
        >>> json_data = serialize_menu(menu, indent=2)
        >>> # In template: <div x-data='{{ json_data|safe }}'>...</div>

    Raises:
        TypeError: If menu_item doesn't have a to_dict method.
    """
    import json

    if not hasattr(menu_item, "to_dict"):
        raise TypeError(f"menu_item must have a to_dict method. Got {type(menu_item)}")

    include_children = options.get("include_children", True)
    indent = options.get("indent", None)

    data = menu_item.to_dict(include_children=include_children)
    return json.dumps(data, indent=indent)
