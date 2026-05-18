"""
Tests for flex_menu.utils module.
"""

import pytest
from django.urls.exceptions import NoReverseMatch

from flex_menu.utils import get_required_url_params


@pytest.mark.django_db
class TestGetRequiredUrlParams:
    """Test get_required_url_params function."""

    def test_namespaced_url_no_params(self):
        """Test namespaced URL with no parameters."""
        # 'admin:index' has no parameters
        params = get_required_url_params("admin:index")
        assert params == set()

    def test_namespaced_url_with_params(self):
        """Test namespaced URL with parameters."""
        # 'admin:app_list' requires 'app_label' parameter
        params = get_required_url_params("admin:app_list")
        assert "app_label" in params
        assert len(params) == 1

    def test_invalid_view_name(self):
        """Test that invalid view name raises NoReverseMatch."""
        with pytest.raises(NoReverseMatch):
            get_required_url_params("nonexistent_view")

    def test_invalid_namespace(self):
        """Test that invalid namespace raises NoReverseMatch."""
        with pytest.raises(NoReverseMatch):
            get_required_url_params("badnamespace:view")

    def test_nested_namespace_with_parent_params(self, settings):
        """Test that parameters from parent URLResolvers are included.

        This simulates a structure like:
            path("project/<str:uuid>/", include((urls, "project")))
        where the parent resolver has a parameter (uuid) and the nested
        patterns also have their own parameters.
        """
        from django.urls import clear_url_caches, include, path
        from django.views import View

        class DummyView(View):
            pass

        # Create nested URL patterns like fairdm uses
        nested_urls = [
            path("", DummyView.as_view(), name="overview"),
            path("edit/<int:pk>/", DummyView.as_view(), name="edit"),
        ]

        # Create a test URL configuration
        test_urlpatterns = [
            path("test/<str:uuid>/", include((nested_urls, "test"))),
        ]

        # Temporarily replace URL conf
        original_urlconf = settings.ROOT_URLCONF
        settings.ROOT_URLCONF = __name__

        # Inject the test patterns into this module
        import sys

        sys.modules[__name__].urlpatterns = test_urlpatterns  # type: ignore[attr-defined]

        clear_url_caches()

        try:
            # Test that parent parameter (uuid) is included
            params = get_required_url_params("test:overview")
            assert params == {"uuid"}

            # Test that both parent and child parameters are included
            params = get_required_url_params("test:edit")
            assert params == {"uuid", "pk"}
        finally:
            # Restore original URL conf
            settings.ROOT_URLCONF = original_urlconf
            clear_url_caches()

    def test_url_conf_switch_returns_correct_params(self, settings):
        """Switching ROOT_URLCONF returns params for the new conf, not the old one.

        Since get_required_url_params is no longer cached, this is trivially
        correct; the test documents the expected behaviour.
        """
        from django.urls import clear_url_caches, include, path
        from django.views import View

        class DummyView(View):
            pass

        original_urlconf = settings.ROOT_URLCONF
        settings.ROOT_URLCONF = __name__
        import sys

        sys.modules[__name__].urlpatterns = [
            path(
                "alt/<str:slug>/",
                include(([path("", DummyView.as_view(), name="detail")], "alt")),
            ),
        ]
        clear_url_caches()

        try:
            params = get_required_url_params("alt:detail")
            assert params == {"slug"}
        finally:
            settings.ROOT_URLCONF = original_urlconf
            clear_url_caches()
