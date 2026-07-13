"""
Tests for MenuItem class properties, behavior, and validation.
"""

import pytest
from django.test import RequestFactory

from flex_menu import MenuItem, root


class TestMenuItemCreation:
    """Test MenuItem instantiation and validation."""

    def test_create_simple_item_with_url(self):
        """MenuItem can be created with a URL."""
        item = MenuItem(name="home", url="/")
        assert item.name == "home"
        assert item._url == "/"
        assert item.has_url is True
        assert item.has_children is False

    def test_create_item_with_view_name(self):
        """MenuItem can be created with a Django view name."""
        item = MenuItem(name="admin", view_name="admin:index")
        assert item.view_name == "admin:index"
        assert item.has_url is True

    def test_create_parent_with_children(self):
        """MenuItem can be created with children."""
        item = MenuItem(
            name="parent",
            children=[
                MenuItem(name="child1", url="/child1/"),
                MenuItem(name="child2", url="/child2/"),
            ],
        )
        assert item.has_children is True
        assert len(item.children) == 2
        assert item.has_url is False

    def test_cannot_have_url_and_children(self):
        """MenuItem cannot have both URL and children."""
        with pytest.raises(
            ValueError, match="cannot have both a URL/view_name and children"
        ):
            MenuItem(
                name="invalid",
                url="/test/",
                children=[MenuItem(name="child", url="/child/")],
            )

    def test_cannot_have_view_name_and_children(self):
        """MenuItem cannot have both view_name and children."""
        with pytest.raises(
            ValueError, match="cannot have both a URL/view_name and children"
        ):
            MenuItem(
                name="invalid",
                view_name="some_view",
                children=[MenuItem(name="child", url="/child/")],
            )

    def test_auto_attach_to_root(self):
        """MenuItem automatically attaches to root when parent=None."""
        item = MenuItem(name="test_auto_attach", url="/test/")
        assert item.parent == root
        # Clean up
        item.parent = None

    def test_extra_context_storage(self):
        """MenuItem stores extra_context data."""
        item = MenuItem(
            name="test",
            url="/",
            extra_context={"label": "Test Label", "icon": "fa-home"},
        )
        assert item.extra_context["label"] == "Test Label"
        assert item.extra_context["icon"] == "fa-home"


class TestMenuItemProperties:
    """Test MenuItem property accessors."""

    def test_has_url_with_url(self):
        """has_url returns True when URL is set."""
        item = MenuItem(name="test", url="/test/")
        assert item.has_url is True

    def test_has_url_with_view_name(self):
        """has_url returns True when view_name is set."""
        item = MenuItem(name="test", view_name="admin:index")
        assert item.has_url is True

    def test_has_url_false(self):
        """has_url returns False when neither URL nor view_name is set."""
        item = MenuItem(name="test")
        assert item.has_url is False

    def test_has_children_true(self):
        """has_children returns True when children exist."""
        item = MenuItem(name="parent", children=[MenuItem(name="child", url="/")])
        assert item.has_children is True

    def test_has_children_false(self):
        """has_children returns False when no children."""
        item = MenuItem(name="leaf", url="/")
        assert item.has_children is False

    def test_is_leaf(self):
        """is_leaf is opposite of has_children."""
        leaf = MenuItem(name="leaf", url="/")
        parent = MenuItem(name="parent", children=[MenuItem(name="child", url="/")])
        assert leaf.is_leaf is True
        assert parent.is_leaf is False

    def test_is_parent(self):
        """is_parent is alias for has_children."""
        leaf = MenuItem(name="leaf", url="/")
        parent = MenuItem(name="parent", children=[MenuItem(name="child", url="/")])
        assert leaf.is_parent is False
        assert parent.is_parent is True

    def test_is_clickable(self):
        """is_clickable is alias for has_url."""
        clickable = MenuItem(name="link", url="/")
        not_clickable = MenuItem(name="header")
        assert clickable.is_clickable is True
        assert not_clickable.is_clickable is False

    def test_depth_calculation(self):
        """depth property calculates tree depth correctly."""
        grandparent = MenuItem(
            name="gp",
            children=[
                MenuItem(
                    name="parent",
                    children=[MenuItem(name="child", url="/")],
                )
            ],
        )
        # MenuItem auto-attaches to root, so depth is 1 (root=0, this=1)
        assert grandparent.depth == 1
        parent = grandparent.children[0]
        child = parent.children[0]
        assert parent.depth == 2
        assert child.depth == 3
        # Clean up
        grandparent.parent = None


class TestMenuItemProcessing:
    """Test MenuItem processing with request context."""

    def test_process_creates_copy(self, simple_menu_item):
        """Processing creates a copy, not mutating original."""
        rf = RequestFactory()
        request = rf.get("/")

        processed = simple_menu_item.process(request)

        assert processed is not simple_menu_item
        assert processed.name == simple_menu_item.name
        assert simple_menu_item.request is None  # Original not mutated
        assert processed.request == request  # Copy has request

    def test_process_sets_visibility(self, simple_menu_item):
        """Processing sets visible based on check function."""
        rf = RequestFactory()
        request = rf.get("/")

        processed = simple_menu_item.process(request)
        assert processed.visible is True

    def test_process_with_check_function(self):
        """Processing respects check function."""
        item = MenuItem(
            name="staff_only",
            url="/admin/",
            check=lambda request: getattr(request.user, "is_staff", False),
        )
        rf = RequestFactory()

        # Regular request - not visible
        request = rf.get("/")
        request.user = type("User", (), {"is_staff": False})()
        processed = item.process(request)
        assert processed.visible is False

        # Staff request - visible
        staff_request = rf.get("/")
        staff_request.user = type("User", (), {"is_staff": True})()
        processed_staff = item.process(staff_request)
        assert processed_staff.visible is True

    def test_process_children(self, parent_menu_item):
        """Processing recursively processes children."""
        rf = RequestFactory()
        request = rf.get("/")

        processed = parent_menu_item.process(request)

        assert processed.has_visible_children is True
        assert len(processed.visible_children) == 2
        for child in processed.visible_children:
            assert child.visible is True
            assert child.request == request

    def test_visible_children_maintains_depth(self, complex_menu_tree):
        """Processed children maintain correct depth."""
        rf = RequestFactory()
        request = rf.get("/")

        processed = complex_menu_tree.process(request)

        # Main menu is depth 0
        assert processed.depth == 0

        # Top-level items are depth 1
        for child in processed.visible_children:
            assert child.depth == 1

            # Second-level items are depth 2
            if child.has_visible_children:
                for grandchild in child.visible_children:
                    assert grandchild.depth == 2

    def test_process_hides_parent_with_no_visible_children(self):
        """Parent with no URL and no visible children is hidden."""
        item = MenuItem(
            name="parent",
            children=[
                MenuItem(name="hidden", url="/", check=False),  # Always hidden
            ],
        )
        rf = RequestFactory()
        request = rf.get("/")

        processed = item.process(request)

        assert processed.visible is False  # Hidden because no visible children

    def test_process_selection_matching(self):
        """Processing sets selected=True for matching URL."""
        item = MenuItem(name="about", url="/about/")
        rf = RequestFactory()
        request = rf.get("/about/")

        processed = item.process(request)

        assert processed.selected is True

    def test_process_parent_selected_when_child_selected(self):
        """Parent is marked selected when a child's URL matches the request."""
        item = MenuItem(
            name="parent",
            children=[
                MenuItem(name="child", url="/about/"),
            ],
        )
        rf = RequestFactory()
        request = rf.get("/about/")

        processed = item.process(request)

        assert processed.visible_children[0].selected is True
        assert processed.selected is True

    def test_process_parent_selected_when_grandchild_selected(self):
        """Selection propagates through multiple ancestor levels."""
        item = MenuItem(
            name="grandparent",
            children=[
                MenuItem(
                    name="parent",
                    children=[
                        MenuItem(name="child", url="/about/"),
                    ],
                ),
            ],
        )
        rf = RequestFactory()
        request = rf.get("/about/")

        processed = item.process(request)
        processed_parent = processed.visible_children[0]

        assert processed_parent.visible_children[0].selected is True
        assert processed_parent.selected is True
        assert processed.selected is True

    def test_process_parent_not_selected_when_no_child_selected(self):
        """Parent stays unselected when no child matches the request."""
        item = MenuItem(
            name="parent",
            children=[
                MenuItem(name="child", url="/about/"),
            ],
        )
        rf = RequestFactory()
        request = rf.get("/contact/")

        processed = item.process(request)

        assert processed.visible_children[0].selected is False
        assert processed.selected is False


class TestMenuItemManipulation:
    """Test MenuItem tree manipulation methods."""

    def test_append_child(self):
        """Can append children to menu item."""
        parent = MenuItem(name="parent")
        child = MenuItem(name="child", url="/child/")

        parent.append(child)

        assert child in parent.children
        assert child.parent == parent

    def test_extend_children(self):
        """Can extend children list."""
        parent = MenuItem(name="parent")
        children = [
            MenuItem(name="child1", url="/child1/"),
            MenuItem(name="child2", url="/child2/"),
        ]

        parent.extend(children)

        assert len(parent.children) == 2
        assert all(c in parent.children for c in children)

    def test_cannot_append_if_has_url(self):
        """Cannot append children if item has URL."""
        item = MenuItem(name="leaf", url="/")
        child = MenuItem(name="child", url="/child/")

        with pytest.raises(ValueError, match="has a URL and cannot have children"):
            item.append(child)

    def test_get_child_by_name(self):
        """Can retrieve child by name using get()."""
        parent = MenuItem(
            name="parent",
            children=[
                MenuItem(name="child1", url="/"),
                MenuItem(name="child2", url="/"),
            ],
        )

        child = parent.get("child1")
        assert child is not None
        assert child.name == "child1"

    def test_bracket_notation_access(self):
        """Can access children using bracket notation."""
        parent = MenuItem(
            name="parent",
            children=[MenuItem(name="child1", url="/")],
        )

        child = parent["child1"]
        assert child.name == "child1"

    def test_bracket_notation_raises_keyerror(self):
        """Bracket notation raises KeyError for missing child."""
        parent = MenuItem(name="parent")

        with pytest.raises(KeyError):
            _ = parent["nonexistent"]


class TestMenuItemAdvanced:
    """Test advanced MenuItem functionality."""

    def test_insert_after_named_child(self):
        """Test inserting after a specific named child."""
        parent = MenuItem(name="parent", label="Parent")
        MenuItem(name="child1", label="Child 1", url="/1/", parent=parent)
        MenuItem(name="child3", label="Child 3", url="/3/", parent=parent)

        # Insert child2 after child1
        child2 = MenuItem(name="child2", label="Child 2", url="/2/")
        parent.insert_after(child2, "child1")

        children_list = list(parent.children)
        assert children_list[0].name == "child1"
        assert children_list[1].name == "child2"
        assert children_list[2].name == "child3"

    def test_insert_after_nonexistent(self):
        """Test insert_after with nonexistent child raises error."""
        parent = MenuItem(name="parent", label="Parent")
        child = MenuItem(name="child", label="Child", url="/child/")

        with pytest.raises(ValueError, match="No child with name 'nonexistent' found"):
            parent.insert_after(child, "nonexistent")

    def test_insert_after_on_leaf_raises(self):
        """Test insert_after on item with URL raises error."""
        leaf = MenuItem(name="leaf", label="Leaf", url="/leaf/")
        child = MenuItem(name="child", label="Child", url="/child/")

        with pytest.raises(ValueError, match="has a URL and cannot have children"):
            leaf.insert_after(child, "anything")

    def test_pop_by_name(self):
        """Test removing child by name."""
        parent = MenuItem(name="parent", label="Parent")
        child1 = MenuItem(name="child1", label="Child 1", url="/1/", parent=parent)
        MenuItem(name="child2", label="Child 2", url="/2/", parent=parent)

        # Pop child1
        removed = parent.pop("child1")

        assert removed is child1
        assert removed.parent is None
        assert len(list(parent.children)) == 1
        assert list(parent.children)[0].name == "child2"

    def test_pop_nonexistent_raises(self):
        """Test popping nonexistent child raises error."""
        parent = MenuItem(name="parent", label="Parent")

        with pytest.raises(ValueError, match="No child with name nonexistent found"):
            parent.pop("nonexistent")

    def test_pop_self(self):
        """Test popping self (detach from parent)."""
        parent = MenuItem(name="parent", label="Parent")
        child = MenuItem(name="child", label="Child", url="/child/", parent=parent)

        # Pop child from itself (detach)
        removed = child.pop()

        assert removed is child
        assert child.parent is None
        assert len(list(parent.children)) == 0


class TestMenuClass:
    """Test Menu convenience class."""

    def test_menu_auto_registers_to_root(self):
        """Menu automatically attaches to root."""
        from flex_menu import Menu

        menu = Menu(
            name="test_menu",
            children=[
                MenuItem(name="home", url="/"),
                MenuItem(name="about", url="/about/"),
            ],
        )

        assert menu.parent == root
        assert menu.name == "test_menu"
        assert len(menu.children) == 2

        # Clean up
        menu.parent = None

    def test_menu_cannot_have_url(self):
        """Menu is always a container, cannot have URL."""
        from flex_menu import Menu

        # Menu doesn't accept url/view_name parameters
        menu = Menu(
            name="test_menu_no_url",
            children=[MenuItem(name="item", url="/item/")],
        )

        assert menu.has_url is False
        assert menu.has_children is True

        # Clean up
        menu.parent = None

    def test_menu_is_accessible_by_name(self):
        """Menu can be retrieved from root by name."""
        from flex_menu import Menu

        menu = Menu(
            name="accessible_menu",
            children=[MenuItem(name="test", url="/test/")],
        )

        # Should be findable via root.get()
        found = root.get("accessible_menu")
        assert found is menu
        assert found.name == "accessible_menu"

        # Clean up
        menu.parent = None

    def test_menu_example_usage(self):
        """Test typical Menu usage pattern."""
        from flex_menu import Menu

        # Typical usage: define a navigation menu
        NavMenu = Menu(
            "main_nav",
            children=[
                MenuItem(name="home", url="/", extra_context={"label": "Home"}),
                MenuItem(
                    name="products",
                    extra_context={"label": "Products"},
                    children=[
                        MenuItem(
                            name="all",
                            url="/products/",
                            extra_context={"label": "All Products"},
                        ),
                        MenuItem(
                            name="new",
                            url="/products/new/",
                            extra_context={"label": "New Arrivals"},
                        ),
                    ],
                ),
                MenuItem(
                    name="contact", url="/contact/", extra_context={"label": "Contact"}
                ),
            ],
        )

        assert NavMenu.name == "main_nav"
        assert NavMenu.parent == root
        assert len(NavMenu.children) == 3
        assert NavMenu["products"].has_children is True

        # Verify it can be retrieved
        found = root.get("main_nav")
        assert found is NavMenu

        # Clean up
        NavMenu.parent = None
