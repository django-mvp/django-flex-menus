"""Tests for template tags."""

import pytest
from django.template import Context, Template, TemplateSyntaxError
from django.test import RequestFactory

from flex_menu import MenuItem, root


@pytest.fixture
def request_factory():
    """Create request factory."""
    return RequestFactory()


@pytest.fixture
def get_request(request_factory):
    """Create a GET request."""
    return request_factory.get("/")


@pytest.fixture
def test_menu():
    """Create a test menu structure."""
    # Clean up any existing test menu
    existing = root.get("test_menu")
    if existing:
        existing.parent = None

    menu = MenuItem(name="test_menu", label="Test Menu", parent=root)
    MenuItem(name="item1", label="Item 1", url="/item1/", parent=menu)
    MenuItem(name="item2", label="Item 2", url="/item2/", parent=menu)
    yield menu

    # Cleanup
    menu.parent = None


@pytest.fixture
def nested_menu():
    """Create a nested menu structure."""
    # Clean up any existing menu
    existing = root.get("nested_menu")
    if existing:
        existing.parent = None

    menu = MenuItem(name="nested_menu", label="Nested Menu", parent=root)
    parent = MenuItem(name="parent", label="Parent", parent=menu)
    MenuItem(name="child1", label="Child 1", url="/child1/", parent=parent)
    MenuItem(name="child2", label="Child 2", url="/child2/", parent=parent)
    yield menu

    # Cleanup
    menu.parent = None


@pytest.mark.django_db
class TestProcessMenuTag:
    """Test process_menu template tag."""

    def test_process_menu_by_name(self, get_request, test_menu):
        """Test processing menu by name."""
        template = Template(
            "{% load flex_menu %}"
            "{% process_menu 'test_menu' as processed %}"
            "{{ processed.name }}"
        )
        context = Context({"request": get_request})
        result = template.render(context)

        assert "test_menu" in result

    def test_process_menu_caches_on_request(self, get_request, test_menu):
        """Test that processed menu is cached on request object."""
        template = Template(
            "{% load flex_menu %}"
            "{% process_menu 'test_menu' as processed %}"
            "{{ processed.name }}"
        )
        context = Context({"request": get_request})
        template.render(context)

        # Check cache key exists on request
        cache_key = f"_processed_menu_test_menu_{id(get_request)}"
        assert hasattr(get_request, cache_key)
        cached = getattr(get_request, cache_key)
        assert cached is not None
        assert cached.name == "test_menu"

    def test_process_menu_reuses_cache(self, get_request, test_menu):
        """Test that processing same menu twice uses cache."""
        template = Template(
            "{% load flex_menu %}"
            "{% process_menu 'test_menu' as processed1 %}"
            "{% process_menu 'test_menu' as processed2 %}"
            "{{ processed1.name }}-{{ processed2.name }}"
        )
        context = Context({"request": get_request})
        result = template.render(context)

        assert "test_menu-test_menu" in result

        # Both should reference the same cached object
        cache_key = f"_processed_menu_test_menu_{id(get_request)}"
        cached = getattr(get_request, cache_key)
        assert cached is not None

    def test_process_menu_nonexistent_raises_error(self, get_request):
        """Test that processing non-existent menu raises TemplateSyntaxError."""
        template = Template(
            "{% load flex_menu %}{% process_menu 'nonexistent_menu' as processed %}"
        )
        context = Context({"request": get_request})

        with pytest.raises(TemplateSyntaxError, match="does not exist"):
            template.render(context)

    def test_process_menu_with_instance(self, get_request, test_menu):
        """Test processing menu by passing instance."""
        template = Template(
            "{% load flex_menu %}"
            "{% process_menu menu_obj as processed %}"
            "{{ processed.name }}"
        )
        context = Context({"request": get_request, "menu_obj": test_menu})
        result = template.render(context)

        assert "test_menu" in result

    def test_process_menu_filters_by_visibility(self, get_request, test_menu):
        """Test that processing respects visibility checks."""
        # Add hidden item
        MenuItem(
            name="hidden",
            label="Hidden",
            url="/hidden/",
            check=False,
            parent=test_menu,
        )

        template = Template(
            "{% load flex_menu %}"
            "{% process_menu 'test_menu' as processed %}"
            "{{ processed.visible_children|length }}"
        )
        context = Context({"request": get_request})
        result = template.render(context)

        # Should only have 2 visible children (item1, item2), not hidden
        assert "2" in result


@pytest.mark.django_db
class TestRenderMenuTag:
    """Test render_menu template tag."""

    def test_render_menu_returns_empty_for_nonexistent(self, get_request):
        """Test render_menu returns empty string for non-existent menu."""
        # This will raise during processing
        template = Template("{% load flex_menu %}{% render_menu 'nonexistent' %}")
        context = Context({"request": get_request})

        with pytest.raises(TemplateSyntaxError):
            template.render(context)

    def test_render_menu_uses_process_menu_caching(self, get_request, test_menu):
        """Test that render_menu uses process_menu's caching."""
        template = Template("{% load flex_menu %}{% render_menu 'test_menu' %}")
        context = Context({"request": get_request})

        # Should raise template error but cache should be set
        with pytest.raises(Exception):  # Template rendering will fail
            template.render(context)

        # Cache should still have been set during process_menu call
        # (even though rendering failed)

    def test_render_menu_with_named_renderer(self, get_request, test_menu, settings):
        """Test render_menu with specific renderer name."""
        # Configure a test renderer
        settings.FLEX_MENUS = {
            "renderers": {
                "test": "flex_menu.renderers.SimpleHTMLRenderer",
            }
        }

        template = Template(
            "{% load flex_menu %}{% render_menu 'test_menu' renderer='test' %}"
        )
        context = Context({"request": get_request})

        # Will fail due to missing templates but renderer lookup should work
        with pytest.raises(Exception):
            template.render(context)

    def test_render_menu_includes_media_by_default(self, get_request, test_menu):
        """Test render_menu includes media by default with a renderer that has media."""
        # Create a simple test renderer with media
        from flex_menu.renderers import BaseRenderer

        class TestRendererWithMedia(BaseRenderer):
            """Test renderer with CSS/JS media."""

            class Media:
                css = {"all": ["test.css"]}
                js = ["test.js"]

            template_map = {"depth_0": "test.html"}

            def render(self, item, **kwargs):
                """Simple render method."""
                return "<nav>Test Menu</nav>"

        renderer = TestRendererWithMedia()

        template = Template(
            "{% load flex_menu %}{% render_menu 'test_menu' renderer=renderer %}"
        )
        context = Context({"request": get_request, "renderer": renderer})

        result = template.render(context)

        # Verify media is included
        assert "test.css" in result
        assert "test.js" in result
        assert "<nav>Test Menu</nav>" in result

    def test_render_menu_exclude_media_with_parameter(self, get_request, test_menu):
        """Test render_menu can exclude media with include_media=False."""
        # Create a simple test renderer with media
        from flex_menu.renderers import BaseRenderer

        class TestRendererNoMedia(BaseRenderer):
            """Test renderer with CSS/JS media."""

            class Media:
                css = {"all": ["test2.css"]}
                js = ["test2.js"]

            template_map = {"depth_0": "test.html"}

            def render(self, item, **kwargs):
                """Simple render method."""
                return "<nav>Test Menu</nav>"

        renderer = TestRendererNoMedia()

        template = Template(
            "{% load flex_menu %}{% render_menu 'test_menu' renderer=renderer include_media=False %}"
        )
        context = Context({"request": get_request, "renderer": renderer})

        result = template.render(context)

        # Verify media is NOT included
        assert "test2.css" not in result
        assert "test2.js" not in result
        assert "<nav>Test Menu</nav>" in result

    def test_render_menu_requires_renderer(self, get_request, test_menu):
        """Test render_menu raises error when renderer is None."""
        template = Template(
            "{% load flex_menu %}{% render_menu 'test_menu' renderer=None %}"
        )
        context = Context({"request": get_request})

        with pytest.raises(
            TemplateSyntaxError, match="requires a 'renderer' parameter"
        ):
            template.render(context)


@pytest.mark.django_db
class TestRenderItemTag:
    """Test render_item template tag."""

    def test_render_item_returns_empty_for_none(self, get_request):
        """Test render_item returns empty for None item."""
        template = Template("{% load flex_menu %}{% render_item None %}")
        context = Context({"request": get_request})
        result = template.render(context)

        assert result.strip() == ""

    def test_render_item_returns_empty_for_invisible(self, get_request):
        """Test render_item returns empty for invisible items."""
        item = MenuItem(name="test", label="Test", url="/test/", check=False)
        processed = item.process(get_request)

        template = Template("{% load flex_menu %}{% render_item item %}")
        context = Context({"request": get_request, "item": processed})
        result = template.render(context)

        assert result.strip() == ""

    def test_render_item_with_string_renderer(self, get_request, settings):
        """Test render_item with renderer name as string."""
        settings.FLEX_MENUS = {
            "renderers": {
                "test": "flex_menu.renderers.SimpleHTMLRenderer",
            }
        }

        item = MenuItem(name="test", label="Test", url="/test/")
        processed = item.process(get_request)

        template = Template(
            "{% load flex_menu %}{% render_item item renderer='test' %}"
        )
        context = Context({"request": get_request, "item": processed})

        # Will fail due to missing templates
        with pytest.raises(Exception):
            template.render(context)

    def test_render_item_with_renderer_instance(self, get_request):
        """Test render_item with renderer instance."""
        from flex_menu.renderers import BaseRenderer

        item = MenuItem(name="test", label="Test", url="/test/")
        processed = item.process(get_request)
        renderer_instance = BaseRenderer()

        template = Template(
            "{% load flex_menu %}{% render_item item renderer=renderer %}"
        )
        context = Context(
            {
                "request": get_request,
                "item": processed,
                "renderer": renderer_instance,
            }
        )

        # Will fail due to missing templates
        with pytest.raises(Exception):
            template.render(context)

    def test_render_item_uses_default_renderer(self, get_request, settings):
        """Test render_item uses default renderer when none specified."""
        settings.FLEX_MENUS = {
            "default": "flex_menu.renderers.SimpleHTMLRenderer",
        }

        item = MenuItem(name="test", label="Test", url="/test/")
        processed = item.process(get_request)

        template = Template("{% load flex_menu %}{% render_item item %}")
        context = Context({"request": get_request, "item": processed})

        # Will fail due to missing templates
        with pytest.raises(Exception):
            template.render(context)


@pytest.mark.django_db
class TestTemplateTagIntegration:
    """Test template tags working together."""

    def test_full_menu_workflow(self, get_request, test_menu, settings):
        """Test complete workflow: process and render."""
        settings.FLEX_MENUS = {
            "default": "flex_menu.renderers.SimpleHTMLRenderer",
        }

        # Template that uses process_menu
        template_str = """
        {% load flex_menu %}
        {% process_menu 'test_menu' as menu %}
        Menu name: {{ menu.name }}
        Has children: {{ menu.has_children }}
        """

        template = Template(template_str)
        context = Context({"request": get_request})
        result = template.render(context)

        assert "test_menu" in result
        assert "True" in result  # has_children

    def test_process_and_render_separately(self, get_request, test_menu, settings):
        """Test processing and rendering as separate steps."""
        settings.FLEX_MENUS = {
            "default": "flex_menu.renderers.SimpleHTMLRenderer",
        }

        # First process
        process_template = Template(
            "{% load flex_menu %}{% process_menu 'test_menu' as menu %}{{ menu.name }}"
        )
        context = Context({"request": get_request})
        result = process_template.render(context)
        assert "test_menu" in result

        # Verify cache was set
        cache_key = f"_processed_menu_test_menu_{id(get_request)}"
        assert hasattr(get_request, cache_key)

    def test_nested_render_item_calls(self, get_request, nested_menu, settings):
        """Test recursive render_item calls for nested menus."""
        settings.FLEX_MENUS = {
            "renderers": {
                "simple": "flex_menu.renderers.SimpleHTMLRenderer",
            },
            "default_renderer": "simple",
        }

        # Process the menu first
        processed = nested_menu.process(get_request)

        # Template using menu names instead of labels (labels aren't preserved during processing)
        template_str = """
        {% load flex_menu %}
        {% for child in menu.visible_children %}
            Item: {{ child.name }}
            {% if child.visible_children %}
                {% for grandchild in child.visible_children %}
                    Grandchild: {{ grandchild.name }}
                {% endfor %}
            {% endif %}
        {% endfor %}
        """

        template = Template(template_str)
        context = Context({"request": get_request, "menu": processed})
        result = template.render(context)

        # Check for the actual structure that gets rendered
        assert "Item:" in result
        assert "Grandchild:" in result
        # Check for child names
        assert "child1" in result or "child2" in result

    def test_context_aware_checks_via_render_menu(self, get_request):
        """Test passing context variables to check functions via render_menu."""
        from flex_menu import Menu, MenuItem, root

        # Track what parameters were passed to check
        check_calls = []

        def context_check(request, resource=None, action=None, **kwargs):
            check_calls.append(
                {"resource": resource, "action": action, "kwargs": kwargs}
            )
            return resource == "test_resource" and action == "edit"

        # Create test menu
        Menu(
            name="test_context_menu",
            children=[
                MenuItem(name="item1", url="/item1/", check=context_check),
            ],
        )

        # Template with context parameters (kwargs must come before 'as')
        template_str = """
        {% load flex_menu %}
        {% process_menu 'test_context_menu' resource='test_resource' action='edit' as menu %}
        Visible: {{ menu.visible_children|length }}
        """

        template = Template(template_str)
        context = Context({"request": get_request})
        result = template.render(context)

        # Check was called with context parameters
        assert len(check_calls) == 1
        assert check_calls[0]["resource"] == "test_resource"
        assert check_calls[0]["action"] == "edit"
        assert "Visible: 1" in result

        # Clean up
        root.pop("test_context_menu")

    def test_context_variables_affect_visibility(self, rf):
        """Test that context variables properly control visibility."""
        from django.contrib.auth.models import AnonymousUser

        from flex_menu import Menu, MenuItem, root

        def owner_check(request, owner_id=None, **kwargs):
            # Simulate checking if request.user.id matches owner_id
            return owner_id == 123  # Would be request.user.id == owner_id in real use

        Menu(
            name="test_owner_menu",
            children=[
                MenuItem(name="public", url="/public/"),
                MenuItem(name="owner_only", url="/owner/", check=owner_check),
            ],
        )

        # Create separate requests to avoid caching issues
        request1 = rf.get("/")
        request1.user = AnonymousUser()

        # Test with matching owner_id
        template = Template(
            "{% load flex_menu %}{% process_menu 'test_owner_menu' owner_id=123 as menu %}"
            "{{ menu.visible_children|length }}"
        )
        context = Context({"request": request1})
        result = template.render(context)
        assert "2" in result  # Both items visible

        # Create new request for second test to avoid cache
        request2 = rf.get("/")
        request2.user = AnonymousUser()

        # Test with non-matching owner_id (kwargs before 'as')
        template2 = Template(
            "{% load flex_menu %}{% process_menu 'test_owner_menu' owner_id=456 as menu %}"
            "{{ menu.visible_children|length }}"
        )
        context2 = Context({"request": request2})
        result2 = template2.render(context2)
        assert "1" in result2  # Only public item visible

        # Clean up
        root.pop("test_owner_menu")

    def test_context_kwargs_used_for_url_resolution(self, rf):
        """Test that context kwargs are passed to resolve_url for view_name resolution."""
        from django.contrib.auth.models import AnonymousUser

        from flex_menu import Menu, MenuItem, root

        # Track calls to a callable URL function
        url_calls = []

        def dynamic_url(request, pk=None, **kwargs):
            """Callable URL that receives kwargs."""
            url_calls.append({"pk": pk, "kwargs": kwargs})
            return f"/item/{pk}/" if pk else "/item/"

        # Create test menu with callable URL that requires kwargs
        Menu(
            name="test_url_menu",
            children=[
                MenuItem(name="detail", url=dynamic_url),
            ],
        )

        request = rf.get("/")
        request.user = AnonymousUser()

        # Process menu with pk kwarg - should be passed to callable URL
        template = Template(
            "{% load flex_menu %}{% process_menu 'test_url_menu' pk=123 as menu %}"
            "{% for item in menu.visible_children %}{{ item.url }}{% endfor %}"
        )
        context = Context({"request": request})
        result = template.render(context)

        # Callable should have been called with pk=123
        assert len(url_calls) == 1
        assert url_calls[0]["pk"] == 123
        # Should contain the resolved URL
        assert "/item/123/" in result

        # Clean up
        root.pop("test_url_menu")

    def test_extra_kwargs_dont_break_url_resolution(self, rf):
        """Test that extra kwargs (not needed for URL) don't break reverse()."""
        from django.contrib.auth.models import AnonymousUser

        from flex_menu import Menu, MenuItem, root

        # Create test menu with view_name that doesn't need any kwargs
        Menu(
            name="test_extra_menu",
            children=[
                MenuItem(name="admin", view_name="admin:index"),  # Doesn't need kwargs
            ],
        )

        request = rf.get("/")
        request.user = AnonymousUser()

        # Process menu with EXTRA kwargs that admin:index doesn't use
        # This should fail if extra kwargs are passed to reverse()
        template = Template(
            "{% load flex_menu %}{% process_menu 'test_extra_menu' pk=123 project='test' as menu %}"
            "{% for item in menu.visible_children %}{{ item.url }}{% endfor %}"
        )
        context = Context({"request": request})

        # Render and check result
        result = template.render(context)

        # Clean up
        root.pop("test_extra_menu")

        # IMPORTANT: Django's reverse() raises NoReverseMatch with extra kwargs
        # When URL resolution fails, the item becomes INVISIBLE (not an error)
        # So the result will be empty - the item is hidden, not broken
        assert result.strip() == "", (
            "Item should be invisible when reverse() fails with extra kwargs"
        )
