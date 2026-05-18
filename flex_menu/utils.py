"""
Utility functions for django-flex-menus.

This module contains helper functions for URL resolution and parameter extraction.
"""

from django.urls import get_resolver
from django.urls.exceptions import NoReverseMatch


def get_required_url_params(view_name: str) -> frozenset:
    """
    Given a Django view_name (as used in reverse()), return the names of the
    required URL parameters (e.g. {''pk''} or {''slug''}).

    Supports both simple view names (''home'') and namespaced view names (''app:home'').
    Parameters captured by parent resolver prefixes (e.g. ''<str:uuid>/'' in an
    include() prefix) are included.

    Relies on Django''s own pre-built resolver structures (namespace_dict,
    reverse_dict), so each call is O(1) dict lookups with no caching needed.
    """
    resolver = get_resolver()
    parts = view_name.split(":")
    name = parts[-1]
    namespaces = parts[:-1]

    # Navigate the namespace hierarchy, accumulating prefix params at each level.
    accumulated_params: set[str] = set()
    current = resolver

    for ns in namespaces:
        entry = current.namespace_dict.get(ns)
        if entry is None:
            raise NoReverseMatch(f"Namespace ''{ns}'' not found in ''{view_name}''.")
        _app_name, sub_resolver = entry
        # Accumulate URL params captured by this namespace''s prefix pattern.
        pat = sub_resolver.pattern
        if hasattr(pat, "converters") and pat.converters:
            accumulated_params.update(pat.converters.keys())
        elif hasattr(pat, "regex"):
            try:
                accumulated_params.update(pat.regex.groupindex.keys())
            except Exception:
                pass
        current = sub_resolver

    # Look up the local view name in the terminal resolver''s reverse_dict.
    # MultiValueDict.get() returns the last single entry: a 4-tuple
    # (bits, p_pattern, defaults, converters), where
    # bits = [(format_str, [param_names]), ...]
    matches = current.reverse_dict.get(name)
    if matches is None:
        raise NoReverseMatch(f"No URL pattern found for view name ''{view_name}''.")

    bits, _p_pattern, _defaults, _converters = matches
    local_params: set[str] = set()
    for _fmt, param_names in bits:
        local_params.update(param_names)

    return frozenset(accumulated_params | local_params)
