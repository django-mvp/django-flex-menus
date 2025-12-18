"""Tests for menu serialization functionality."""

import json

import pytest
from django.template import Context, Template
from django.test import RequestFactory

from flex_menu import MenuItem, root, serialize_menu


@pytest.fixture
def request_factory():
    """Create request factory."""
    return RequestFactory()


@pytest.fixture
def get_request(request_factory):
    """Create a GET request."""
    return request_factory.get("/")


@pytest.fixture
def simple_menu():
    """Create a simple menu structure."""
    # Clean up any existing test menu
    existing = root.get("simple_test_menu")
    if existing:
        existing.parent = None

    menu = MenuItem(name="simple_test_menu", parent=root)
    MenuItem(name="item1", url="/item1/", parent=menu, extra_context={"label": "Item 1", "icon": "home"})
    MenuItem(name="item2", url="/item2/", parent=menu, extra_context={"label": "Item 2", "icon": "about"})
    yield menu

    # Cleanup
    menu.parent = None


@pytest.fixture
def nested_menu():
    """Create a nested menu structure."""
    # Clean up any existing menu
    existing = root.get("nested_test_menu")
    if existing:
        existing.parent = None

    menu = MenuItem(name="nested_test_menu", parent=root)
    parent = MenuItem(name="parent", parent=menu, extra_context={"label": "Parent"})
    MenuItem(name="child1", url="/child1/", parent=parent, extra_context={"label": "Child 1"})
    MenuItem(name="child2", url="/child2/", parent=parent, extra_context={"label": "Child 2"})
    yield menu

    # Cleanup
    menu.parent = None


@pytest.fixture
def conditional_menu():
    """Create a menu with conditional visibility."""
    existing = root.get("conditional_test_menu")
    if existing:
        existing.parent = None

    menu = MenuItem(name="conditional_test_menu", parent=root)
    MenuItem(
        name="always_visible",
        url="/always/",
        parent=menu,
        extra_context={"label": "Always Visible"},
    )
    MenuItem(
        name="staff_only",
        url="/staff/",
        parent=menu,
        check=lambda request: request.user.is_staff if hasattr(request.user, "is_staff") else False,
        extra_context={"label": "Staff Only"},
    )
    yield menu

    # Cleanup
    menu.parent = None


@pytest.mark.django_db
class TestMenuItemToDict:
    """Test MenuItem.to_dict() method."""

    def test_simple_item_to_dict(self, get_request):
        """Test serializing a simple menu item."""
        item = MenuItem(
            name="test",
            url="/test/",
            extra_context={"label": "Test Item", "icon": "test-icon"},
        )
        processed = item.process(get_request)

        data = processed.to_dict()

        assert data["name"] == "test"
        assert data["url"] == "/test/"
        assert data["visible"] is True
        assert data["selected"] is False
        assert data["depth"] == 0
        assert data["has_children"] is False
        assert data["has_visible_children"] is False
        assert data["is_clickable"] is True
        assert data["extra_context"]["label"] == "Test Item"
        assert data["extra_context"]["icon"] == "test-icon"
        assert data["children"] == []

    def test_nested_menu_to_dict(self, get_request, nested_menu):
        """Test serializing a nested menu structure."""
        processed = nested_menu.process(get_request)

        data = processed.to_dict()

        assert data["name"] == "nested_test_menu"
        assert data["has_children"] is True
        assert data["has_visible_children"] is True
        assert len(data["children"]) == 1

        parent_data = data["children"][0]
        assert parent_data["name"] == "parent"
        assert parent_data["extra_context"]["label"] == "Parent"
        assert len(parent_data["children"]) == 2

        child1_data = parent_data["children"][0]
        assert child1_data["name"] == "child1"
        assert child1_data["url"] == "/child1/"
        assert child1_data["extra_context"]["label"] == "Child 1"

    def test_to_dict_without_children(self, get_request, nested_menu):
        """Test serializing without children."""
        processed = nested_menu.process(get_request)

        data = processed.to_dict(include_children=False)

        assert data["name"] == "nested_test_menu"
        assert "children" not in data

    def test_invisible_items_excluded(self, get_request, conditional_menu):
        """Test that invisible items are not included in visible_children."""
        # Mock user without is_staff attribute
        get_request.user = type("User", (), {})()

        processed = conditional_menu.process(get_request)
        data = processed.to_dict()

        # Should only have one visible child (always_visible)
        assert len(data["children"]) == 1
        assert data["children"][0]["name"] == "always_visible"

    def test_selected_state(self, request_factory):
        """Test that selected state is properly serialized."""
        request = request_factory.get("/test/")
        item = MenuItem(name="test", url="/test/")
        processed = item.process(request)

        data = processed.to_dict()

        assert data["selected"] is True
        assert data["url"] == "/test/"

    def test_depth_levels(self, get_request, nested_menu):
        """Test that depth is correctly serialized at all levels."""
        processed = nested_menu.process(get_request)
        data = processed.to_dict()

        assert data["depth"] == 0  # root level
        parent_data = data["children"][0]
        assert parent_data["depth"] == 1  # first level
        child_data = parent_data["children"][0]
        assert child_data["depth"] == 2  # second level


@pytest.mark.django_db
class TestSerializeMenuFunction:
    """Test serialize_menu() utility function."""

    def test_serialize_menu_basic(self, get_request, simple_menu):
        """Test basic serialization to JSON."""
        processed = simple_menu.process(get_request)
        json_str = serialize_menu(processed)

        # Should return valid JSON
        data = json.loads(json_str)
        assert data["name"] == "simple_test_menu"
        assert len(data["children"]) == 2

    def test_serialize_menu_with_indent(self, get_request, simple_menu):
        """Test serialization with pretty printing."""
        processed = simple_menu.process(get_request)
        json_str = serialize_menu(processed, indent=2)

        # Should be valid JSON and contain indentation
        data = json.loads(json_str)
        assert data["name"] == "simple_test_menu"
        assert "\n" in json_str  # Should have newlines from indentation

    def test_serialize_menu_without_children(self, get_request, simple_menu):
        """Test serialization without children."""
        processed = simple_menu.process(get_request)
        json_str = serialize_menu(processed, include_children=False)

        data = json.loads(json_str)
        assert data["name"] == "simple_test_menu"
        assert "children" not in data

    def test_serialize_menu_invalid_input(self):
        """Test that serialize_menu raises TypeError for invalid input."""
        with pytest.raises(TypeError, match="must have a to_dict method"):
            serialize_menu("not a menu item")

    def test_serialize_nested_structure(self, get_request, nested_menu):
        """Test serialization preserves nested structure."""
        processed = nested_menu.process(get_request)
        json_str = serialize_menu(processed)

        data = json.loads(json_str)
        assert data["name"] == "nested_test_menu"
        assert len(data["children"]) == 1
        parent = data["children"][0]
        assert parent["name"] == "parent"
        assert len(parent["children"]) == 2


@pytest.mark.django_db
class TestMenuJsonTemplateTag:
    """Test menu_json template tag."""

    def test_menu_json_basic(self, get_request, simple_menu):
        """Test basic menu_json template tag usage."""
        template = Template(
            "{% load flex_menu %}"
            "{% menu_json 'simple_test_menu' as menu_data %}"
            "{{ menu_data }}"
        )
        context = Context({"request": get_request})
        result = template.render(context)

        # Should return valid JSON
        data = json.loads(result)
        assert data["name"] == "simple_test_menu"
        assert len(data["children"]) == 2

    def test_menu_json_with_indent(self, get_request, simple_menu):
        """Test menu_json with indentation."""
        template = Template(
            "{% load flex_menu %}"
            "{% menu_json 'simple_test_menu' indent=2 %}"
        )
        context = Context({"request": get_request})
        result = template.render(context)

        # Should be valid JSON with newlines
        data = json.loads(result)
        assert data["name"] == "simple_test_menu"
        assert "\n" in result

    def test_menu_json_without_children(self, get_request, simple_menu):
        """Test menu_json without children."""
        template = Template(
            "{% load flex_menu %}"
            "{% menu_json 'simple_test_menu' include_children=False %}"
        )
        context = Context({"request": get_request})
        result = template.render(context)

        data = json.loads(result)
        assert data["name"] == "simple_test_menu"
        assert "children" not in data

    def test_menu_json_nonexistent_menu(self, get_request):
        """Test menu_json with nonexistent menu."""
        template = Template(
            "{% load flex_menu %}"
            "{% menu_json 'nonexistent_menu' %}"
        )
        context = Context({"request": get_request})
        
        # Should raise TemplateSyntaxError for nonexistent menu
        with pytest.raises(Exception):  # Will be TemplateSyntaxError from process_menu
            template.render(context)

    def test_menu_json_with_context_vars(self, get_request, conditional_menu):
        """Test menu_json passes context variables correctly."""
        # Mock user with is_staff = True
        get_request.user = type("User", (), {"is_staff": True})()

        template = Template(
            "{% load flex_menu %}"
            "{% menu_json 'conditional_test_menu' %}"
        )
        context = Context({"request": get_request})
        result = template.render(context)

        data = json.loads(result)
        # Should have both items visible
        assert len(data["children"]) == 2

    def test_menu_json_caching(self, get_request, simple_menu):
        """Test that menu_json uses process_menu caching."""
        template = Template(
            "{% load flex_menu %}"
            "{% menu_json 'simple_test_menu' as data1 %}"
            "{% menu_json 'simple_test_menu' as data2 %}"
            "{{ data1 }}|{{ data2 }}"
        )
        context = Context({"request": get_request})
        result = template.render(context)

        # Both should be identical JSON
        parts = result.split("|")
        assert len(parts) == 2
        assert json.loads(parts[0]) == json.loads(parts[1])

    def test_menu_json_in_alpine_js_context(self, get_request, simple_menu):
        """Test menu_json output is safe for Alpine.js usage."""
        template = Template(
            "{% load flex_menu %}"
            "<div x-data='{% menu_json 'simple_test_menu' %}'>"
            "</div>"
        )
        context = Context({"request": get_request})
        result = template.render(context)

        # Extract JSON from x-data attribute
        start = result.find("x-data='") + len("x-data='")
        end = result.find("'>", start)
        json_str = result[start:end]

        # Should be valid JSON
        data = json.loads(json_str)
        assert data["name"] == "simple_test_menu"
        assert len(data["children"]) == 2


@pytest.mark.django_db
class TestSerializationEdgeCases:
    """Test edge cases and special scenarios."""

    def test_empty_menu_serialization(self, get_request):
        """Test serializing an empty menu."""
        menu = MenuItem(name="empty_menu")
        processed = menu.process(get_request)

        data = processed.to_dict()
        assert data["name"] == "empty_menu"
        assert data["children"] == []
        assert data["has_children"] is False

    def test_deep_nesting_serialization(self, get_request):
        """Test serializing deeply nested menu."""
        level1 = MenuItem(name="level1")
        level2 = MenuItem(name="level2", parent=level1)
        level3 = MenuItem(name="level3", parent=level2)
        MenuItem(name="level4", url="/level4/", parent=level3)

        processed = level1.process(get_request)
        data = processed.to_dict()

        # Navigate to level 4
        l2 = data["children"][0]
        l3 = l2["children"][0]
        l4 = l3["children"][0]

        assert l4["name"] == "level4"
        assert l4["depth"] == 3
        assert l4["url"] == "/level4/"

    def test_extra_context_types(self, get_request):
        """Test that various extra_context types are serialized correctly."""
        item = MenuItem(
            name="test",
            url="/test/",
            extra_context={
                "string": "value",
                "number": 42,
                "float": 3.14,
                "bool": True,
                "null": None,
                "list": [1, 2, 3],
                "dict": {"nested": "value"},
            },
        )
        processed = item.process(get_request)

        json_str = serialize_menu(processed)
        data = json.loads(json_str)

        ec = data["extra_context"]
        assert ec["string"] == "value"
        assert ec["number"] == 42
        assert ec["float"] == 3.14
        assert ec["bool"] is True
        assert ec["null"] is None
        assert ec["list"] == [1, 2, 3]
        assert ec["dict"] == {"nested": "value"}

    def test_url_none_serialization(self, get_request):
        """Test that items without URLs serialize url as None."""
        item = MenuItem(name="no_url")
        processed = item.process(get_request)

        data = processed.to_dict()
        assert data["url"] is None
        assert data["is_clickable"] is False
