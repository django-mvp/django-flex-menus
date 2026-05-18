"""
Unified MenuItem class for django-flex-menus.

This module provides a single, flexible MenuItem class that can represent:
- Clickable links (has url/view_name)
- Containers/parents (has children)
- Non-clickable items (headers, dividers)

Note: Menu items cannot have both a URL and children - they must be either
a link OR a container, not both.
"""

import logging
from collections.abc import Callable
from typing import Optional
from urllib.parse import urlencode

from anytree import Node, RenderTree, search
from django.conf import settings
from django.core.handlers.wsgi import WSGIRequest
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch

from .utils import get_required_url_params


# Configuration for logging URL resolution failures
def _should_log_url_failures():
    """
    Check if URL resolution failures should be logged.

    By default, URL failures are only logged when DEBUG=True since failed
    URL resolution is often expected behavior (e.g., menu items that should
    be hidden when users lack permissions or when optional views aren't available).

    Can be overridden with the FLEX_MENUS['log_url_failures'] setting.

    Returns:
        bool: True if URL failures should be logged, False otherwise.
    """
    return getattr(settings, "FLEX_MENUS", {}).get("log_url_failures", settings.DEBUG)


# Sentinel value to distinguish between "no parent specified" and "explicitly no parent"
class _NoParentType:
    pass


_NO_PARENT = _NoParentType()


class MenuItem(Node):
    """
    Unified menu item that can be:
    - A clickable link (has url/view_name)
    - A container/parent (has children)
    - A non-clickable item (neither url nor children)

    Note: A MenuItem cannot have both a URL and children - it must be either
    a link OR a container, not both.

    Attributes:
        name (str): The unique name/identifier for this menu item.
        view_name (str): Django URL name for reverse resolution.
        url (str | Callable): Static URL or callable that returns URL.
        params (dict): Query parameters to append to the URL.
        parent (MenuItem): Parent menu item in the hierarchy.
        children (list[MenuItem]): Child menu items.
        check (Callable | bool): Function to determine visibility or boolean.
        extra_context (dict): Additional context data for templates.

    State attributes (set during processing):
        visible (bool): Whether this item passed visibility checks.
        selected (bool): Whether this item's URL matches the current request path.
        url (str): Resolved URL (after processing).
        request (WSGIRequest): The current request object.
    """

    request: WSGIRequest | None
    _processed_children: list["MenuItem"]
    _original_children: tuple["MenuItem", ...]
    _cached_url: str | None

    def __init__(
        self,
        name: str,
        view_name: str = "",
        url: str | Callable = "",
        params: dict | None = None,
        parent: Optional["MenuItem"] | _NoParentType = None,
        children: list["MenuItem"] | None = None,
        check: Callable | bool = True,
        extra_context: dict | None = None,
        **kwargs,
    ):
        """
        Initialize a menu item.

        Args:
            name: Unique identifier for this menu item.
            view_name: Django URL name for reverse resolution.
            url: Static URL string or callable returning URL.
            params: Query parameters dict to append to URL.
            parent: Parent menu item (or None for root-level items).
            children: List of child menu items.
            check: Callable(request, **kwargs) -> bool or boolean value.
            extra_context: Additional context for template rendering.
            **kwargs: Additional attributes for the node.

        Raises:
            ValueError: If both URL/view_name and children are provided.
        """
        # Validate: cannot have both URL and children
        if (view_name or url) and children:
            raise ValueError(
                f"MenuItem '{name}' cannot have both a URL/view_name and children. "
                f"Menu items must be EITHER a link OR a container, not both. "
                f"If you need a clickable item in a dropdown, add it as the first child."
            )

        # Handle parent=None -> attach to root by default
        if parent is None:
            parent = root
        elif parent is _NO_PARENT:
            parent = None

        super().__init__(name, parent=parent, children=children, **kwargs)

        # URL-related attributes
        self.view_name = view_name
        self._url = url
        self.params = params or {}

        # Visibility and context
        self._check = check
        self.extra_context = extra_context or {}

        # State (set during processing)
        self.visible = False
        self.selected = False
        self.url: str | None = None  # Resolved URL
        self.request: WSGIRequest | None = None
        self._processed_children: list["MenuItem"] = []

    def __str__(self) -> str:
        return f"MenuItem(name={self.name})"

    def __getitem__(self, name: str) -> "MenuItem":
        """Get child by name using bracket notation."""
        node = self.get(name)
        if node is None:
            raise KeyError(f"No child with name {name} found.")
        return node

    def __iter__(self):
        """Iterate over children."""
        yield from self.children

    # ========== Properties ==========

    @property
    def has_url(self) -> bool:
        """True if this menu item has a URL (view_name or url)."""
        return bool(self.view_name or self._url)

    @property
    def has_children(self) -> bool:
        """True if this menu has child items."""
        return len(self.children) > 0  # type: ignore[has-type]

    @property
    def visible_children(self) -> list["MenuItem"]:
        """Return processed, visible children (after processing)."""
        return self._processed_children

    @property
    def has_visible_children(self) -> bool:
        """True if this menu has visible children after processing."""
        return len(self._processed_children) > 0

    @property
    def is_parent(self) -> bool:
        """Alias for has_children."""
        return self.has_children

    @property
    def is_leaf(self) -> bool:
        """True if this is a leaf node (no children)."""
        return not self.has_children

    @property
    def is_clickable(self) -> bool:
        """True if this item can be clicked (has URL)."""
        return self.has_url

    @property
    def depth(self) -> int:
        """
        Depth in the tree.
        0 = root, 1 = top-level items, 2 = nested items, etc.
        """
        return len(self.path) - 1

    # ========== Menu Manipulation Methods ==========

    def append(self, child: "MenuItem") -> None:
        """
        Append a child menu item.

        Args:
            child: The child menu item to append.

        Raises:
            ValueError: If this item has a URL (cannot have both URL and children).
        """
        if self.has_url:
            raise ValueError(
                f"MenuItem '{self.name}' has a URL and cannot have children. "
                f"Menu items must be EITHER a link OR a container, not both."
            )
        child.parent = self  # type: ignore[has-type]

    def extend(self, children: list["MenuItem"]) -> None:
        """
        Append multiple child menu items.

        Args:
            children: List of child menu items to append.

        Raises:
            ValueError: If this item has a URL (cannot have both URL and children).
        """
        if self.has_url:
            raise ValueError(
                f"MenuItem '{self.name}' has a URL and cannot have children. "
                f"Menu items must be EITHER a link OR a container, not both."
            )
        for child in children:
            child.parent = self  # type: ignore[has-type]

    def insert(
        self,
        children: "MenuItem | list[MenuItem]",
        position: int,
    ) -> None:
        """
        Insert child menu items at a specified position.

        Args:
            children: A child or list of children to insert.
            position: Position index to insert at.

        Raises:
            ValueError: If this item has a URL (cannot have both URL and children).
        """
        if self.has_url:
            raise ValueError(
                f"MenuItem '{self.name}' has a URL and cannot have children. "
                f"Menu items must be EITHER a link OR a container, not both."
            )

        if not isinstance(children, list):
            children = [children]

        old = list(self.children)  # type: ignore[has-type]
        new = old[:position] + children + old[position:]
        self.children = new

    def insert_after(self, child: "MenuItem", named: str) -> None:
        """
        Insert a child menu item after an existing child with specified name.

        Args:
            child: The new child menu item to insert.
            named: The name of the existing child after which to insert.

        Raises:
            ValueError: If no child with specified name exists or if this item has a URL.
        """
        if self.has_url:
            raise ValueError(
                f"MenuItem '{self.name}' has a URL and cannot have children. "
                f"Menu items must be EITHER a link OR a container, not both."
            )

        existing_child = self.get(named)
        if existing_child:
            children_list = list(self.children)
            insert_index = children_list.index(existing_child) + 1
            self.children = children_list[:insert_index] + [child] + children_list[insert_index:]
        else:
            raise ValueError(f"No child with name '{named}' found.")

    def pop(self, name: str | None = None) -> "MenuItem":
        """
        Remove a child node or detach the current node from its parent.

        Args:
            name: The name of the child to remove. If None, removes this node.

        Returns:
            The removed node.

        Raises:
            ValueError: If no child with the specified name exists.
        """
        if name:
            node = self.get(name)
            if node:
                node.parent = None  # type: ignore[has-type]
                return node
            else:
                raise ValueError(f"No child with name {name} found.")
        self.parent = None
        return self

    def get(self, name: str, maxlevel: int | None = None) -> Optional["MenuItem"]:
        """
        Find a child node by name.

        Args:
            name: The name of the child node to find.
            maxlevel: The maximum depth to search.
                     1 = direct children only, 2 = children and grandchildren, etc.

        Returns:
            The child node, or None if not found.
        """
        if not name:
            return None

        # Adjust maxlevel for anytree's 1-indexed counting from search root
        # maxlevel=1 should search direct children, so we need anytree maxlevel=2
        anytree_maxlevel = maxlevel + 1 if maxlevel is not None else None

        result = search.find_by_attr(self, value=name, name="name", maxlevel=anytree_maxlevel)
        return result  # type: ignore[no-any-return]

    def print_tree(self) -> str:
        """
        Print the menu tree structure.

        Returns:
            A string representation of the tree.
        """
        result = RenderTree(self).by_attr("name")
        return str(result)

    # ========== Visibility and Processing ==========

    def check(self, request, **kwargs) -> bool:
        """
        Check if the menu item is visible based on the request.

        Args:
            request: The HTTP request object.
            **kwargs: Additional arguments for custom check functions.

        Returns:
            True if the menu item is visible, False otherwise.
        """
        if callable(self._check):
            result = self._check(request, **kwargs)
            return bool(result)
        return bool(self._check)

    def process(self, request, **kwargs) -> "MenuItem":
        """
        Process the menu item for a specific request.

        Creates a processed copy with request-specific state to avoid race conditions.
        For items with children, recursively processes all children.

        Args:
            request: The HTTP request object.
            **kwargs: Additional arguments passed to check functions and URL resolution.

        Returns:
            A processed copy of this menu item with request-specific state.
        """
        # Create shallow copy to avoid mutating the shared instance
        processed = self._create_request_copy()
        processed.request = request
        processed.visible = processed.check(request, **kwargs)

        if not processed.visible:
            return processed

        # Resolve URL if this item has one
        if processed.has_url:
            processed.url = processed.resolve_url(**kwargs)
            if not processed.url:
                # If URL cannot be resolved, check if this is a parent
                # Parents without URLs are allowed, but leaf nodes need resolvable URLs
                if not processed.has_children:
                    processed.visible = False
                    return processed
            else:
                # URL resolved successfully, check if it matches current path
                processed.match_url()

        # Process children if this is a parent
        # Use _original_children if available (from copy), otherwise use self.children
        children_to_process = getattr(processed, "_original_children", processed.children)
        if children_to_process:
            processed_children = []
            for child in children_to_process:
                processed_child = child.process(request, **kwargs)
                if processed_child.visible:
                    # Attach processed child to processed parent to maintain tree structure
                    processed_child.parent = processed
                    processed_children.append(processed_child)

            # Store processed children
            processed._processed_children = processed_children

            # If this is a container (no URL) with no visible children, hide it
            if not processed.has_url and not processed_children:
                processed.visible = False

        return processed

    def _create_request_copy(self) -> "MenuItem":
        """
        Create a shallow copy for request processing.

        Creates a copy that maintains the tree structure so depth calculations work.
        The copy will be detached from the global root but maintain proper parent-child relationships.
        """
        # If this has a parent (and it's not the global root), recursively copy parent first
        # This ensures the copy maintains proper depth in the tree
        if self.parent and self.parent.name != "DjangoFlexMenu":
            parent_copy = _NO_PARENT  # Will be set when parent processes us as a child
        else:
            parent_copy = _NO_PARENT  # Top-level or root

        # Create copy with detached parent (will be attached by parent's processing)
        copy_instance = self.__class__(
            name=self.name,
            view_name=self.view_name,
            url=self._url,
            params=self.params.copy() if self.params else None,
            parent=parent_copy,
            check=self._check,
            extra_context=self.extra_context.copy(),
            # Don't pass children yet - they'll be processed and added during process()
        )

        # Store reference to original children for processing
        # We'll iterate over these in process() and add processed copies as children
        copy_instance._original_children = self.children  # type: ignore[assignment]

        return copy_instance

    # ========== URL Resolution ==========

    def resolve_url(self, *args, **kwargs) -> str | None:
        """
        Resolve the URL for this menu item.

        Supports three types of URLs:
        - Django view names (resolved via reverse())
        - Static URL strings
        - Callable functions that return URLs

        Args:
            *args: Positional arguments for URL resolution.
            **kwargs: Keyword arguments for URL resolution. Extra kwargs not needed
                     for the URL pattern will be filtered out automatically.

        Returns:
            The resolved URL string, or None if resolution fails.
        """
        # Check for cached URL (only for static URLs with no args/kwargs)
        if not args and not kwargs and hasattr(self, "_cached_url"):
            return self._cached_url

        # Resolve Django view name
        if self.view_name:
            # Always try to filter kwargs to only include those needed by the URL pattern
            # This allows passing extra context (like object instances) alongside URL params
            filtered_kwargs = kwargs
            if kwargs:
                try:
                    param_names = set(get_required_url_params(self.view_name))
                    logger_instance = logging.getLogger(__name__)
                    logger_instance.debug(
                        f"URL param extraction for '{self.view_name}': param_names={param_names}, kwargs={list(kwargs.keys())}"
                    )
                    if param_names:
                        # Only pass kwargs that are in the URL pattern
                        filtered_kwargs = {k: v for k, v in kwargs.items() if k in param_names}
                        logger_instance.debug(f"Filtered kwargs for '{self.view_name}': {list(filtered_kwargs.keys())}")
                except NoReverseMatch:
                    # Pattern not found, use all kwargs
                    logger_instance = logging.getLogger(__name__)
                    logger_instance.debug(f"Could not find URL pattern for '{self.view_name}', using all kwargs")

            try:
                url = reverse(self.view_name, args=args, kwargs=filtered_kwargs)
                # Cache static URLs for reuse
                if not args and not kwargs:
                    self._cached_url = url
                return url
            except NoReverseMatch as e:
                # Only log if explicitly configured to do so
                if _should_log_url_failures():
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Could not reverse URL for view '{self.view_name}' in menu item '{self.name}'")
                    logger.warning(f"Reverse error: {e}")
                    try:
                        param_names_for_log = set(get_required_url_params(self.view_name))
                        if param_names_for_log:
                            logger.warning(f"Detected URL params: {param_names_for_log}")
                            logger.warning(f"Filtered kwargs: {filtered_kwargs}")
                        else:
                            logger.warning(f"Could not detect URL params - passed all kwargs: {list(kwargs.keys())}")
                    except NoReverseMatch:
                        logger.warning(f"Could not detect URL params - passed all kwargs: {list(kwargs.keys())}")
                # Cache failure for static URLs
                if not args and not kwargs:
                    self._cached_url = None
                return None

        # Callable URL function
        elif self._url and callable(self._url):
            try:
                return self._url(self.request, *args, **kwargs)  # type: ignore[no-any-return]
            except Exception as e:
                # Only log if explicitly configured to do so
                if _should_log_url_failures():
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Error calling URL function for menu item '{self.name}': {e}")
                return None

        # Static URL string
        elif self._url:
            static_url: str = self._url
            if self.params:
                query_string = urlencode(self.params)
                separator = "&" if "?" in static_url else "?"
                static_url = static_url + separator + query_string

            # Cache static URLs for reuse (when no args/kwargs)
            if not args and not kwargs:
                self._cached_url = static_url
            return static_url

        return None

    def match_url(self) -> bool:
        """
        Check if the menu item's URL matches the request path.

        Returns:
            True if the URL matches the request path, False otherwise.
        """
        url = getattr(self, "url", None)
        if not url or not self.request:
            self.selected = False
            return False

        self.selected = url == self.request.path
        return self.selected


# Global root menu instance
root = MenuItem("DjangoFlexMenu", parent=_NO_PARENT)


class Menu(MenuItem):
    """
    Top-level menu container that automatically registers itself to the root.

    This is a convenience class for defining menus. It's functionally identical
    to MenuItem but automatically attaches to the global root menu.

    Example:
        # Define a navigation menu
        NavMenu = Menu(
            "main_nav",
            children=[
                MenuItem(name="home", label="Home", view_name="home"),
                MenuItem(name="about", label="About", view_name="about"),
            ]
        )

        # Use in template
        {% render_menu 'main_nav' renderer='bootstrap5' %}
    """

    def __init__(
        self,
        name: str,
        children: list["MenuItem"] | None = None,
        check: Callable | bool = True,
        extra_context: dict | None = None,
        **kwargs,
    ):
        """
        Initialize a top-level menu.

        Args:
            name: Unique identifier for this menu.
            children: List of child menu items.
            check: Callable(request, **kwargs) -> bool or boolean value.
            extra_context: Additional context for template rendering.
            **kwargs: Additional attributes for the node.

        Note:
            Menu instances are always attached to the global root and cannot
            have URLs (they are containers only).
        """
        # Always attach to root, never have URL
        super().__init__(
            name=name,
            parent=root,
            children=children,
            check=check,
            extra_context=extra_context,
            **kwargs,
        )

    def _create_request_copy(self) -> "MenuItem":
        """
        Create a shallow copy for request processing.

        Override parent's method to use MenuItem constructor directly,
        avoiding the Menu class's automatic parent=root assignment.
        """
        if self.parent and self.parent.name != "DjangoFlexMenu":
            parent_copy = _NO_PARENT
        else:
            parent_copy = _NO_PARENT

        # Use MenuItem directly, not self.__class__, to avoid Menu's parent=root
        copy_instance = MenuItem(
            name=self.name,
            view_name=self.view_name,
            url=self._url,
            params=self.params.copy() if self.params else None,
            parent=parent_copy,
            check=self._check,
            extra_context=self.extra_context.copy(),
        )

        # Store reference to original children for processing
        copy_instance._original_children = self.children  # type: ignore[assignment]

        return copy_instance
