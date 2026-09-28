"""
Tests for flex_menu.utils module.
"""

import pytest
from django.urls.exceptions import NoReverseMatch

from flex_menu.utils import get_required_url_params


@pytest.mark.django_db
class TestGetRequiredUrlParams:
    def test_namespaced_url_no_params(self):
        params = get_required_url_params("admin:index")
        assert params == set()

    def test_namespaced_url_with_params(self):
        params = get_required_url_params("admin:app_list")
        assert "app_label" in params
        assert len(params) == 1

    def test_invalid_view_name(self):
        with pytest.raises(NoReverseMatch):
            get_required_url_params("nonexistent_view")

    def test_invalid_namespace(self):
        with pytest.raises(NoReverseMatch):
            get_required_url_params("badnamespace:view")

    def test_nested_namespace_with_parent_params(self, settings):
        from django.urls import clear_url_caches, include, path
        from django.views import View

        class DummyView(View):
            pass

        nested_urls = [
            path("", DummyView.as_view(), name="overview"),
            path("edit/<int:pk>/", DummyView.as_view(), name="edit"),
        ]

        test_urlpatterns = [
            path("test/<str:uuid>/", include((nested_urls, "test"))),
        ]

        original_urlconf = settings.ROOT_URLCONF
        settings.ROOT_URLCONF = __name__

        import sys

        sys.modules[__name__].urlpatterns = test_urlpatterns  # type: ignore[attr-defined]

        clear_url_caches()

        try:
            params = get_required_url_params("test:overview")
            assert params == {"uuid"}

            params = get_required_url_params("test:edit")
            assert params == {"uuid", "pk"}
        finally:
            settings.ROOT_URLCONF = original_urlconf
            clear_url_caches()

    def test_url_conf_switch_returns_correct_params(self, settings):
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
