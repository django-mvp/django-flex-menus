"""Tests for the ``render_menu`` management command."""

from io import StringIO

import pytest
from django.core.management import call_command

from flex_menu import Menu, MenuItem


@pytest.fixture
def registered_menu():
    """A named menu attached to the global root, as the command expects to find one."""
    return Menu(
        "site_nav",
        children=[
            MenuItem(name="home", url="/", extra_context={"label": "Home"}),
            MenuItem(name="about", url="/about/", extra_context={"label": "About"}),
        ],
    )


class TestRenderMenuCommand:
    def test_without_name_prints_the_whole_tree(self, registered_menu):
        out = StringIO()

        call_command("render_menu", stdout=out)

        output = out.getvalue()
        assert "Django Flex Menu:" in output
        assert "site_nav" in output
        assert "home" in output
        assert "about" in output

    def test_with_name_prints_only_that_menu(self, registered_menu):
        out = StringIO()

        call_command("render_menu", "--name", "site_nav", stdout=out)

        output = out.getvalue()
        assert "site_nav" in output
        assert "home" in output

    def test_unknown_name_reports_it_was_not_found(self, registered_menu):
        out = StringIO()

        call_command("render_menu", "--name", "no_such_menu", stdout=out)

        output = out.getvalue()
        assert "no_such_menu" in output
        assert "not found" in output
        # The tree is not printed as a consolation prize — the caller asked for
        # one menu and gets told that menu is missing.
        assert "site_nav" not in output
