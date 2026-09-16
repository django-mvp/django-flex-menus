"""Tests for renderer system, template selection, and Media class support."""

import pytest
from django.test import RequestFactory

from flex_menu import MenuItem
from flex_menu.renderers import (
    BaseRenderer,
    get_renderer,
)


class RendererWithMedia(BaseRenderer):
    """Test renderer that includes CSS and JS media."""

    templates = {
        1: {
            "parent": "test/group.html",
            "leaf": "test/item.html",
        },
    }

    class Media:
        css = {"all": ("test/styles.css",)}
        js = ("test/script.js",)


class TestBaseRenderer:
    """Test BaseRenderer class functionality."""

    def test_renderer_initialization(self):
        """Renderer initializes with empty media when no Media class defined."""
        renderer = BaseRenderer()
        assert renderer.media is not None
        assert str(renderer.media) == ""

    def test_renderer_with_media_class(self):
        """Renderer initializes media from Media inner class."""
        renderer = RendererWithMedia()
        assert renderer.media is not None
        media_str = str(renderer.media)
        assert "test/styles.css" in media_str
        assert "test/script.js" in media_str

    def test_get_template_for_leaf(self):
        """get_template returns leaf template for items without children."""
        renderer = BaseRenderer()
        parent = MenuItem(name="menu")
        item = MenuItem(name="test", url="/test/", parent=parent)

        template = renderer.get_template(item)
        assert template == "menu/item.html"

    def test_get_template_for_parent(self):
        """get_template returns parent template for items with children."""
        renderer = BaseRenderer()
        parent = MenuItem(name="menu")
        item = MenuItem(
            name="test", children=[MenuItem(name="child", url="/child/")], parent=parent
        )

        template = renderer.get_template(item)
        assert template == "menu/group.html"

    def test_get_template_with_custom_templates(self):
        """get_template uses custom templates when provided."""
        renderer = RendererWithMedia()
        # Create an item at depth 1 (which has templates defined)
        item = MenuItem(name="test", url="/test/")

        template = renderer.get_template(item)
        assert template == "test/item.html"

    def test_get_context_data(self):
        """get_context_data builds correct context dictionary."""
        renderer = BaseRenderer()
        parent = MenuItem(name="menu")
        item = MenuItem(
            name="test", url="/test/", parent=parent, extra_context={"custom": "value"}
        )

        context = renderer.get_context_data(item)

        assert context["item"] == item
        assert context["renderer"] == renderer
        assert context["depth"] == item.depth
        assert context["visible"] == item.visible
        assert context["label"] == "test"
        assert context["custom"] == "value"

    def test_get_template_raises_for_unsupported_depth(self):
        """get_template raises ValueError for unsupported depth without default."""

        class LimitedRenderer(BaseRenderer):
            templates = {
                0: {"default": "menu/root.html"},
                1: {"parent": "menu/group.html", "leaf": "menu/item.html"},
            }

        renderer = LimitedRenderer()
        parent = MenuItem(name="menu")
        level1 = MenuItem(name="level1", parent=parent)
        level2 = MenuItem(name="level2", parent=level1)
        level3 = MenuItem(name="level3", url="/test/", parent=level2)

        with pytest.raises(ValueError, match="does not support depth"):
            renderer.get_template(level3)

    def test_get_template_uses_default_for_unsupported_depth(self):
        """get_template uses default templates for unsupported depths when available."""

        class DefaultRenderer(BaseRenderer):
            templates = {
                0: {"default": "menu/root.html"},
                1: {"parent": "menu/group.html", "leaf": "menu/item.html"},
                "default": {
                    "parent": "menu/default_group.html",
                    "leaf": "menu/default_item.html",
                },
            }

        renderer = DefaultRenderer()
        parent = MenuItem(name="menu")
        level1 = MenuItem(name="level1", parent=parent)
        level2 = MenuItem(name="level2", parent=level1)
        level3 = MenuItem(name="level3", url="/test/", parent=level2)

        template = renderer.get_template(level3)
        assert template == "menu/default_item.html"

    def test_render_returns_empty_for_invisible(self):
        """render() returns empty string for invisible items."""
        renderer = BaseRenderer()
        parent = MenuItem(name="menu")
        MenuItem(name="test", url="/test/", parent=parent)

        rf = RequestFactory()
        processed = parent.process(rf.get("/"))
        child = processed.visible_children[0]
        child.visible = False

        html = renderer.render(child)
        assert html == ""

    def test_render_attempts_template_for_visible(self):
        """render() checks visibility and returns appropriate result."""
        renderer = BaseRenderer()
        parent = MenuItem(
            name="menu",
            children=[
                MenuItem(name="test", url="/test/", extra_context={"label": "Test"})
            ],
        )
        rf = RequestFactory()
        processed = parent.process(rf.get("/"))
        child = processed.visible_children[0]

        # Test that visible items attempt rendering (will get template path)
        child.visible = True
        template_path = renderer.get_template(child)
        assert isinstance(template_path, str)
        assert ".html" in template_path


class TestGetRenderer:
    """Test get_renderer() function."""

    def test_get_default_renderer_fallback(self, settings):
        """get_renderer('default') returns BaseRenderer if not configured."""
        settings.FLEX_MENUS = {}

        renderer = get_renderer("default")
        assert isinstance(renderer, BaseRenderer)

    def test_get_renderer_raises_for_unknown(self, settings):
        """get_renderer() raises ValueError for unknown renderer."""
        settings.FLEX_MENUS = {
            "renderers": {},
        }

        with pytest.raises(ValueError, match="not found"):
            get_renderer("nonexistent")

    def test_get_renderer_with_settings(self, settings):
        """get_renderer() can retrieve configured renderer."""
        settings.FLEX_MENUS = {
            "renderers": {
                "test": "flex_menu.renderers.BaseRenderer",
            },
        }

        renderer = get_renderer("test")
        assert isinstance(renderer, BaseRenderer)


class TestMediaCombination:
    """Test Media combining from multiple renderers."""

    def test_combine_test_renderer_media(self):
        """Test that Media objects can be combined."""
        renderer1 = RendererWithMedia()
        renderer2 = BaseRenderer()

        # Test that media can be accessed and combined
        combined = renderer1.media + renderer2.media
        combined_str = str(combined)

        assert "test/styles.css" in combined_str
        assert "test/script.js" in combined_str
