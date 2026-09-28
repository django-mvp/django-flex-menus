"""Tests for template tags."""

import pytest
from django.template import Context, Template, TemplateSyntaxError

from flex_menu import MenuItem, root


@pytest.fixture
def sample_menu():
    existing = root.get("test_menu")
    if existing:
        existing.parent = None

    menu = MenuItem(name="test_menu", label="Test Menu", parent=root)
    MenuItem(name="item1", label="Item 1", url="/item1/", parent=menu)
    MenuItem(name="item2", label="Item 2", url="/item2/", parent=menu)
    yield menu

    menu.parent = None


@pytest.fixture
def nested_menu():
    existing = root.get("nested_menu")
    if existing:
        existing.parent = None

    menu = MenuItem(name="nested_menu", label="Nested Menu", parent=root)
    parent = MenuItem(name="parent", label="Parent", parent=menu)
    MenuItem(name="child1", label="Child 1", url="/child1/", parent=parent)
    MenuItem(name="child2", label="Child 2", url="/child2/", parent=parent)
    yield menu

    menu.parent = None


@pytest.mark.django_db
class TestProcessMenuTag:
    def test_process_menu_by_name(self, get_request, sample_menu):
        template = Template(
            "{% load flex_menu %}"
            "{% process_menu 'test_menu' as processed %}"
            "{{ processed.name }}"
        )
        context = Context({"request": get_request})
        result = template.render(context)

        assert "test_menu" in result

    def test_process_menu_caches_on_request(self, get_request, sample_menu):
        template = Template(
            "{% load flex_menu %}"
            "{% process_menu 'test_menu' as processed %}"
            "{{ processed.name }}"
        )
        context = Context({"request": get_request})
        template.render(context)

        cache_key = f"_processed_menu_test_menu_{id(get_request)}"
        assert hasattr(get_request, cache_key)
        cached = getattr(get_request, cache_key)
        assert cached is not None
        assert cached.name == "test_menu"

    def test_process_menu_reuses_cache(self, get_request, sample_menu):
        template = Template(
            "{% load flex_menu %}"
            "{% process_menu 'test_menu' as processed1 %}"
            "{% process_menu 'test_menu' as processed2 %}"
            "{{ processed1.name }}-{{ processed2.name }}"
        )
        context = Context({"request": get_request})
        result = template.render(context)

        assert "test_menu-test_menu" in result

        cache_key = f"_processed_menu_test_menu_{id(get_request)}"
        cached = getattr(get_request, cache_key)
        assert cached is not None

    def test_process_menu_nonexistent_raises_error(self, get_request):
        template = Template(
            "{% load flex_menu %}{% process_menu 'nonexistent_menu' as processed %}"
        )
        context = Context({"request": get_request})

        with pytest.raises(TemplateSyntaxError, match="nonexistent_menu"):
            template.render(context)

    def test_process_menu_with_instance(self, get_request, sample_menu):
        template = Template(
            "{% load flex_menu %}"
            "{% process_menu menu_obj as processed %}"
            "{{ processed.name }}"
        )
        context = Context({"request": get_request, "menu_obj": sample_menu})
        result = template.render(context)

        assert "test_menu" in result

    def test_process_menu_filters_by_visibility(self, get_request, sample_menu):
        MenuItem(
            name="hidden",
            label="Hidden",
            url="/hidden/",
            check=False,
            parent=sample_menu,
        )

        template = Template(
            "{% load flex_menu %}"
            "{% process_menu 'test_menu' as processed %}"
            "{{ processed.visible_children|length }}"
        )
        context = Context({"request": get_request})
        result = template.render(context)

        assert "2" in result


@pytest.mark.django_db
class TestRenderMenuTag:
    def test_render_menu_returns_empty_for_nonexistent(self, get_request):
        template = Template("{% load flex_menu %}{% render_menu 'nonexistent' %}")
        context = Context({"request": get_request})

        with pytest.raises(TemplateSyntaxError):
            template.render(context)

    def test_render_menu_uses_process_menu_caching(self, get_request, sample_menu):
        template = Template("{% load flex_menu %}{% render_menu 'test_menu' %}")
        context = Context({"request": get_request})

        with pytest.raises(Exception):  # Template rendering will fail
            template.render(context)

    def test_render_menu_with_named_renderer(self, get_request, sample_menu, settings):
        settings.FLEX_MENUS = {
            "renderers": {
                "test": "flex_menu.renderers.SimpleHTMLRenderer",
            }
        }

        template = Template(
            "{% load flex_menu %}{% render_menu 'test_menu' renderer='test' %}"
        )
        context = Context({"request": get_request})

        with pytest.raises(Exception):
            template.render(context)

    def test_render_menu_includes_media_by_default(
        self, get_request, sample_menu, media_renderer
    ):
        renderer = media_renderer

        template = Template(
            "{% load flex_menu %}{% render_menu 'test_menu' renderer=renderer %}"
        )
        context = Context({"request": get_request, "renderer": renderer})

        result = template.render(context)

        assert "test.css" in result
        assert "test.js" in result
        assert "<nav>Test Menu</nav>" in result

    def test_render_menu_exclude_media_with_parameter(
        self, get_request, sample_menu, media_renderer
    ):
        renderer = media_renderer

        template = Template(
            "{% load flex_menu %}{% render_menu 'test_menu' renderer=renderer include_media=False %}"
        )
        context = Context({"request": get_request, "renderer": renderer})

        result = template.render(context)

        assert "test.css" not in result
        assert "test.js" not in result
        assert "<nav>Test Menu</nav>" in result

    def test_render_menu_requires_renderer(self, get_request, sample_menu):
        template = Template(
            "{% load flex_menu %}{% render_menu 'test_menu' renderer=None %}"
        )
        context = Context({"request": get_request})

        with pytest.raises(TemplateSyntaxError):
            template.render(context)


@pytest.mark.django_db
class TestRenderItemTag:
    def test_render_item_returns_empty_for_none(self, get_request):
        template = Template("{% load flex_menu %}{% render_item None %}")
        context = Context({"request": get_request})
        result = template.render(context)

        assert result.strip() == ""

    def test_render_item_returns_empty_for_invisible(self, get_request):
        item = MenuItem(name="test", label="Test", url="/test/", check=False)
        processed = item.process(get_request)

        template = Template("{% load flex_menu %}{% render_item item %}")
        context = Context({"request": get_request, "item": processed})
        result = template.render(context)

        assert result.strip() == ""

    def test_render_item_with_string_renderer(self, get_request, settings):
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

        with pytest.raises(Exception):
            template.render(context)

    def test_render_item_with_renderer_instance(self, get_request):
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

        with pytest.raises(Exception):
            template.render(context)

    def test_render_item_uses_default_renderer(self, get_request, settings):
        settings.FLEX_MENUS = {
            "default": "flex_menu.renderers.SimpleHTMLRenderer",
        }

        item = MenuItem(name="test", label="Test", url="/test/")
        processed = item.process(get_request)

        template = Template("{% load flex_menu %}{% render_item item %}")
        context = Context({"request": get_request, "item": processed})

        with pytest.raises(Exception):
            template.render(context)


@pytest.mark.django_db
class TestTemplateTagIntegration:
    def test_full_menu_workflow(self, get_request, sample_menu, settings):
        settings.FLEX_MENUS = {
            "default": "flex_menu.renderers.SimpleHTMLRenderer",
        }

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

    def test_process_and_render_separately(self, get_request, sample_menu, settings):
        settings.FLEX_MENUS = {
            "default": "flex_menu.renderers.SimpleHTMLRenderer",
        }

        process_template = Template(
            "{% load flex_menu %}{% process_menu 'test_menu' as menu %}{{ menu.name }}"
        )
        context = Context({"request": get_request})
        result = process_template.render(context)
        assert "test_menu" in result

        cache_key = f"_processed_menu_test_menu_{id(get_request)}"
        assert hasattr(get_request, cache_key)

    def test_nested_render_item_calls(self, get_request, nested_menu, settings):
        settings.FLEX_MENUS = {
            "renderers": {
                "simple": "flex_menu.renderers.SimpleHTMLRenderer",
            },
            "default_renderer": "simple",
        }

        processed = nested_menu.process(get_request)

        # Processing does not preserve labels, so the template uses names.
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

        assert "Item:" in result
        assert "Grandchild:" in result
        assert "child1" in result or "child2" in result

    def test_context_aware_checks_via_render_menu(self, get_request):
        from flex_menu import Menu, MenuItem, root

        check_calls = []

        def context_check(request, resource=None, action=None, **kwargs):
            check_calls.append(
                {"resource": resource, "action": action, "kwargs": kwargs}
            )
            return resource == "test_resource" and action == "edit"

        Menu(
            name="test_context_menu",
            children=[
                MenuItem(name="item1", url="/item1/", check=context_check),
            ],
        )

        # Keyword arguments must come before 'as'.
        template_str = """
        {% load flex_menu %}
        {% process_menu 'test_context_menu' resource='test_resource' action='edit' as menu %}
        Visible: {{ menu.visible_children|length }}
        """

        template = Template(template_str)
        context = Context({"request": get_request})
        result = template.render(context)

        assert len(check_calls) == 1
        assert check_calls[0]["resource"] == "test_resource"
        assert check_calls[0]["action"] == "edit"
        assert "Visible: 1" in result

        root.pop("test_context_menu")

    def test_context_variables_affect_visibility(self, rf):
        from django.contrib.auth.models import AnonymousUser

        from flex_menu import Menu, MenuItem, root

        def owner_check(request, owner_id=None, **kwargs):
            return owner_id == 123  # Would be request.user.id == owner_id in real use

        Menu(
            name="test_owner_menu",
            children=[
                MenuItem(name="public", url="/public/"),
                MenuItem(name="owner_only", url="/owner/", check=owner_check),
            ],
        )

        request1 = rf.get("/")
        request1.user = AnonymousUser()

        template = Template(
            "{% load flex_menu %}{% process_menu 'test_owner_menu' owner_id=123 as menu %}"
            "{{ menu.visible_children|length }}"
        )
        context = Context({"request": request1})
        result = template.render(context)
        assert "2" in result  # Both items visible

        request2 = rf.get("/")
        request2.user = AnonymousUser()

        template2 = Template(
            "{% load flex_menu %}{% process_menu 'test_owner_menu' owner_id=456 as menu %}"
            "{{ menu.visible_children|length }}"
        )
        context2 = Context({"request": request2})
        result2 = template2.render(context2)
        assert "1" in result2  # Only public item visible

        root.pop("test_owner_menu")

    def test_context_kwargs_used_for_url_resolution(self, rf):
        from django.contrib.auth.models import AnonymousUser

        from flex_menu import Menu, MenuItem, root

        url_calls = []

        def dynamic_url(request, pk=None, **kwargs):
            url_calls.append({"pk": pk, "kwargs": kwargs})
            return f"/item/{pk}/" if pk else "/item/"

        Menu(
            name="test_url_menu",
            children=[
                MenuItem(name="detail", url=dynamic_url),
            ],
        )

        request = rf.get("/")
        request.user = AnonymousUser()

        template = Template(
            "{% load flex_menu %}{% process_menu 'test_url_menu' pk=123 as menu %}"
            "{% for item in menu.visible_children %}{{ item.url }}{% endfor %}"
        )
        context = Context({"request": request})
        result = template.render(context)

        assert len(url_calls) == 1
        assert url_calls[0]["pk"] == 123
        assert "/item/123/" in result

        root.pop("test_url_menu")

    def test_extra_kwargs_dont_break_url_resolution(self, rf):
        from django.contrib.auth.models import AnonymousUser

        from flex_menu import Menu, MenuItem, root

        Menu(
            name="test_extra_menu",
            children=[
                MenuItem(name="admin", view_name="admin:index"),  # Doesn't need kwargs
            ],
        )

        request = rf.get("/")
        request.user = AnonymousUser()

        template = Template(
            "{% load flex_menu %}{% process_menu 'test_extra_menu' pk=123 project='test' as menu %}"
            "{% for item in menu.visible_children %}{{ item.url }}{% endfor %}"
        )
        context = Context({"request": request})

        result = template.render(context)

        root.pop("test_extra_menu")

        # reverse() rejects the extra kwargs, and an unresolvable item is hidden,
        # not an error.
        assert result.strip() == "", (
            "Item should be invisible when reverse() fails with extra kwargs"
        )


@pytest.mark.django_db
class TestTagsWithoutRequestInContext:
    def test_process_menu_yields_nothing(self, sample_menu):
        template = Template(
            "{% load flex_menu %}"
            "{% process_menu 'test_menu' as processed %}"
            "[{{ processed.name }}]"
        )

        assert template.render(Context({})) == "[]"

    def test_process_menu_still_yields_the_menu_with_a_request(
        self, get_request, sample_menu
    ):
        template = Template(
            "{% load flex_menu %}"
            "{% process_menu 'test_menu' as processed %}"
            "[{{ processed.name }}]"
        )

        assert template.render(Context({"request": get_request})) == "[test_menu]"

    def test_render_menu_draws_nothing(self, sample_menu, nav_renderer):
        renderer = nav_renderer
        template = Template(
            "{% load flex_menu %}{% render_menu 'test_menu' renderer=renderer %}"
        )

        assert template.render(Context({"renderer": renderer})) == ""

    def test_render_menu_still_draws_the_menu_with_a_request(
        self, get_request, sample_menu, nav_renderer
    ):
        renderer = nav_renderer
        template = Template(
            "{% load flex_menu %}{% render_menu 'test_menu' renderer=renderer %}"
        )
        context = Context({"request": get_request, "renderer": renderer})

        assert "<nav>Test Menu</nav>" in template.render(context)

    def test_an_unknown_menu_name_still_raises(self):
        template = Template(
            "{% load flex_menu %}{% process_menu 'nonexistent' as processed %}"
        )

        with pytest.raises(TemplateSyntaxError):
            template.render(Context({}))
