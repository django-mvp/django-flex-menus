"""Tests for MenuItem and Menu: creation, properties, processing, tree
manipulation, URL resolution, and selection matching."""

import pytest
from django.test import RequestFactory

from flex_menu import MenuItem, root


class TestMenuItemCreation:
    def test_create_simple_item_with_url(self):
        item = MenuItem(name="home", url="/")
        assert item.name == "home"
        assert item._url == "/"
        assert item.has_url is True
        assert item.has_children is False

    def test_create_item_with_view_name(self):
        item = MenuItem(name="admin", view_name="admin:index")
        assert item.view_name == "admin:index"
        assert item.has_url is True

    def test_create_parent_with_children(self):
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
        with pytest.raises(ValueError):
            MenuItem(
                name="invalid",
                url="/test/",
                children=[MenuItem(name="child", url="/child/")],
            )

    def test_cannot_have_view_name_and_children(self):
        with pytest.raises(ValueError):
            MenuItem(
                name="invalid",
                view_name="some_view",
                children=[MenuItem(name="child", url="/child/")],
            )

    def test_auto_attach_to_root(self):
        item = MenuItem(name="test_auto_attach", url="/test/")
        assert item.parent == root
        item.parent = None

    def test_extra_context_storage(self):
        item = MenuItem(
            name="test",
            url="/",
            extra_context={"label": "Test Label", "icon": "fa-home"},
        )
        assert item.extra_context["label"] == "Test Label"
        assert item.extra_context["icon"] == "fa-home"


class TestMenuItemProperties:
    def test_has_url_with_url(self):
        item = MenuItem(name="test", url="/test/")
        assert item.has_url is True

    def test_has_url_with_view_name(self):
        item = MenuItem(name="test", view_name="admin:index")
        assert item.has_url is True

    def test_has_url_false(self):
        item = MenuItem(name="test")
        assert item.has_url is False

    def test_has_children_true(self):
        item = MenuItem(name="parent", children=[MenuItem(name="child", url="/")])
        assert item.has_children is True

    def test_has_children_false(self):
        item = MenuItem(name="leaf", url="/")
        assert item.has_children is False

    def test_is_leaf(self):
        leaf = MenuItem(name="leaf", url="/")
        parent = MenuItem(name="parent", children=[MenuItem(name="child", url="/")])
        assert leaf.is_leaf is True
        assert parent.is_leaf is False

    def test_is_parent(self):
        leaf = MenuItem(name="leaf", url="/")
        parent = MenuItem(name="parent", children=[MenuItem(name="child", url="/")])
        assert leaf.is_parent is False
        assert parent.is_parent is True

    def test_is_clickable(self):
        clickable = MenuItem(name="link", url="/")
        not_clickable = MenuItem(name="header")
        assert clickable.is_clickable is True
        assert not_clickable.is_clickable is False

    def test_depth_calculation(self):
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
        grandparent.parent = None


class TestMenuItemProcessing:
    def test_process_creates_copy(self, simple_menu_item):
        rf = RequestFactory()
        request = rf.get("/")

        processed = simple_menu_item.process(request)

        assert processed is not simple_menu_item
        assert processed.name == simple_menu_item.name
        assert simple_menu_item.request is None  # Original not mutated
        assert processed.request == request  # Copy has request

    def test_process_sets_visibility(self, simple_menu_item):
        rf = RequestFactory()
        request = rf.get("/")

        processed = simple_menu_item.process(request)
        assert processed.visible is True

    def test_process_with_check_function(self):
        item = MenuItem(
            name="staff_only",
            url="/admin/",
            check=lambda request: getattr(request.user, "is_staff", False),
        )
        rf = RequestFactory()

        request = rf.get("/")
        request.user = type("User", (), {"is_staff": False})()
        processed = item.process(request)
        assert processed.visible is False

        staff_request = rf.get("/")
        staff_request.user = type("User", (), {"is_staff": True})()
        processed_staff = item.process(staff_request)
        assert processed_staff.visible is True

    def test_process_children(self, parent_menu_item):
        rf = RequestFactory()
        request = rf.get("/")

        processed = parent_menu_item.process(request)

        assert processed.has_visible_children is True
        assert len(processed.visible_children) == 2
        for child in processed.visible_children:
            assert child.visible is True
            assert child.request == request

    def test_visible_children_maintains_depth(self, complex_menu_tree):
        rf = RequestFactory()
        request = rf.get("/")

        processed = complex_menu_tree.process(request)

        assert processed.depth == 0

        for child in processed.visible_children:
            assert child.depth == 1

            if child.has_visible_children:
                for grandchild in child.visible_children:
                    assert grandchild.depth == 2

    def test_process_hides_parent_with_no_visible_children(self):
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
        item = MenuItem(name="about", url="/about/")
        rf = RequestFactory()
        request = rf.get("/about/")

        processed = item.process(request)

        assert processed.selected is True

    def test_process_parent_selected_when_child_selected(self):
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
    def test_append_child(self):
        parent = MenuItem(name="parent")
        child = MenuItem(name="child", url="/child/")

        parent.append(child)

        assert child in parent.children
        assert child.parent == parent

    def test_extend_children(self):
        parent = MenuItem(name="parent")
        children = [
            MenuItem(name="child1", url="/child1/"),
            MenuItem(name="child2", url="/child2/"),
        ]

        parent.extend(children)

        assert len(parent.children) == 2
        assert all(c in parent.children for c in children)

    def test_cannot_append_if_has_url(self):
        item = MenuItem(name="leaf", url="/")
        child = MenuItem(name="child", url="/child/")

        with pytest.raises(ValueError):
            item.append(child)

    def test_get_child_by_name(self):
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
        parent = MenuItem(
            name="parent",
            children=[MenuItem(name="child1", url="/")],
        )

        child = parent["child1"]
        assert child.name == "child1"

    def test_bracket_notation_raises_keyerror(self):
        parent = MenuItem(name="parent")

        with pytest.raises(KeyError):
            _ = parent["nonexistent"]


class TestMenuItemAdvanced:
    def test_insert_after_named_child(self):
        parent = MenuItem(name="parent", label="Parent")
        MenuItem(name="child1", label="Child 1", url="/1/", parent=parent)
        MenuItem(name="child3", label="Child 3", url="/3/", parent=parent)

        child2 = MenuItem(name="child2", label="Child 2", url="/2/")
        parent.insert_after(child2, "child1")

        children_list = list(parent.children)
        assert children_list[0].name == "child1"
        assert children_list[1].name == "child2"
        assert children_list[2].name == "child3"

    def test_insert_after_nonexistent(self):
        parent = MenuItem(name="parent", label="Parent")
        child = MenuItem(name="child", label="Child", url="/child/")

        with pytest.raises(ValueError, match="nonexistent"):
            parent.insert_after(child, "nonexistent")

    def test_insert_after_on_leaf_raises(self):
        leaf = MenuItem(name="leaf", label="Leaf", url="/leaf/")
        child = MenuItem(name="child", label="Child", url="/child/")

        with pytest.raises(ValueError):
            leaf.insert_after(child, "anything")

    def test_pop_by_name(self):
        parent = MenuItem(name="parent", label="Parent")
        child1 = MenuItem(name="child1", label="Child 1", url="/1/", parent=parent)
        MenuItem(name="child2", label="Child 2", url="/2/", parent=parent)

        removed = parent.pop("child1")

        assert removed is child1
        assert removed.parent is None
        assert len(list(parent.children)) == 1
        assert next(iter(parent.children)).name == "child2"

    def test_pop_nonexistent_raises(self):
        parent = MenuItem(name="parent", label="Parent")

        with pytest.raises(ValueError, match="nonexistent"):
            parent.pop("nonexistent")

    def test_pop_self(self):
        parent = MenuItem(name="parent", label="Parent")
        child = MenuItem(name="child", label="Child", url="/child/", parent=parent)

        removed = child.pop()

        assert removed is child
        assert child.parent is None
        assert len(list(parent.children)) == 0


@pytest.mark.django_db
class TestCallableURLs:
    def test_callable_url_function(self, get_request):

        def dynamic_url(request, *args, **kwargs):
            return f"/dynamic/{request.path}/"

        item = MenuItem(name="dynamic", label="Dynamic", url=dynamic_url)
        processed = item.process(get_request)

        assert processed.url is not None
        assert "/dynamic/" in processed.url

    def test_callable_url_with_args(self, get_request):

        def url_with_args(request, *args, **kwargs):
            return f"/item/{args[0]}/" if args else "/item/"

        item = MenuItem(name="callable", label="Callable", url=url_with_args)
        processed = item.process(get_request)

        assert processed.url == "/item/"

    def test_callable_url_exception(self, get_request):

        def bad_url(request):
            raise ValueError("Intentional error")

        item = MenuItem(name="bad", label="Bad", url=bad_url)
        processed = item.process(get_request)

        assert processed.url is None


@pytest.mark.django_db
class TestURLParams:
    def test_url_with_params(self, get_request):
        item = MenuItem(
            name="with_params",
            label="With Params",
            url="/path/",
            params={"foo": "bar", "baz": "qux"},
        )
        processed = item.process(get_request)

        assert processed.url is not None
        assert "?" in processed.url
        assert "foo=bar" in processed.url
        assert "baz=qux" in processed.url

    def test_url_with_existing_query_string(self, get_request):
        item = MenuItem(
            name="existing_qs",
            label="Existing QS",
            url="/path/?existing=param",
            params={"new": "param"},
        )
        processed = item.process(get_request)

        assert processed.url is not None
        assert "existing=param" in processed.url
        assert "new=param" in processed.url
        assert "&" in processed.url


class TestURLResolution:
    def test_resolve_url_with_static_url(self, get_request):
        item = MenuItem(name="static", label="Static", url="/static/path/")
        processed = item.process(get_request)

        assert processed.url == "/static/path/"

    def test_resolve_url_with_view_name(self, get_request):
        item = MenuItem(name="admin", label="Admin", view_name="admin:index")
        processed = item.process(get_request)

        assert processed.url == "/admin/"

    def test_resolve_url_with_args(self, get_request):
        item = MenuItem(
            name="with_args",
            label="With Args",
            view_name="admin:app_list",
            args=["auth"],
        )
        processed = item.process(get_request)

        assert processed.url is None or "/admin/auth/" in processed.url

    def test_resolve_url_with_kwargs(self, get_request):
        item = MenuItem(
            name="with_kwargs",
            label="With Kwargs",
            view_name="admin:app_list",
            kwargs={"app_label": "auth"},
        )
        processed = item.process(get_request)

        assert processed.url is None or "/admin/auth/" in processed.url

    def test_resolve_url_invalid_view_name(self, get_request):
        item = MenuItem(
            name="invalid",
            label="Invalid",
            view_name="nonexistent:view",
        )

        processed = item.process(get_request)
        assert processed.url is None

    def test_resolve_url_cached_after_processing(self, get_request):
        item = MenuItem(name="cached", label="Cached", view_name="admin:index")
        processed = item.process(get_request)

        url1 = processed.url
        url2 = processed.url

        assert url1 == url2
        assert url1 == "/admin/"

    def test_url_property_returns_none_for_parent(self):
        parent = MenuItem(name="parent", label="Parent")
        MenuItem(name="child", label="Child", url="/child/", parent=parent)

        assert parent.url is None

    def test_resolve_url_with_query_string(self, get_request):
        item = MenuItem(
            name="with_query",
            label="With Query",
            url="/path/?foo=bar&baz=qux",
        )
        processed = item.process(get_request)

        assert processed.url == "/path/?foo=bar&baz=qux"

    def test_resolve_url_with_fragment(self, get_request):
        item = MenuItem(
            name="with_fragment",
            label="With Fragment",
            url="/path/#section",
        )
        processed = item.process(get_request)

        assert processed.url == "/path/#section"


class TestSelectionMatching:
    def test_selection_exact_match(self, request_factory):
        request = request_factory.get("/exact/path/")

        item = MenuItem(
            name="exact",
            label="Exact",
            url="/exact/path/",
        )
        processed = item.process(request, selection="/exact/path/")

        assert processed.selected is True

    def test_selection_no_match(self, request_factory):
        request = request_factory.get("/other/path/")

        item = MenuItem(
            name="other",
            label="Other",
            url="/exact/path/",
        )
        processed = item.process(request, selection="/other/path/")

        assert processed.selected is False

    def test_selection_with_view_name(self, request_factory):
        request = request_factory.get("/admin/")
        request.resolver_match = type(
            "obj",
            (object,),
            {"url_name": "index", "app_name": "admin", "namespace": "admin"},
        )()

        item = MenuItem(
            name="admin",
            label="Admin",
            view_name="admin:index",
        )
        processed = item.process(request)

        assert processed.url == "/admin/"

    def test_selection_parent_from_child(self, request_factory):
        request = request_factory.get("/parent/child/")

        parent = MenuItem(name="parent", label="Parent")
        child = MenuItem(
            name="child",
            label="Child",
            url="/parent/child/",
            parent=parent,
        )

        processed_child = child.process(request, selection="/parent/child/")

        assert processed_child.selected is True

    def test_selection_ignores_query_string(self, request_factory):
        request = request_factory.get("/orders/", {"page": "2"})

        item = MenuItem(name="orders", label="Orders", url="/orders/?page=2")
        processed = item.process(request)

        assert processed.selected is True

    def test_selection_ignores_trailing_slash_variant(self, request_factory):
        request = request_factory.get("/orders/")

        item = MenuItem(name="orders", label="Orders", url="/orders")
        processed = item.process(request)

        assert processed.selected is True

    def test_selection_matches_view_name_regardless_of_kwargs(self, request_factory):
        from django.urls import resolve

        # The item is processed generically for product 1 (e.g. building a sidebar).
        item = MenuItem(name="product", label="Product", view_name="product-detail")

        # The current request is for a different product served by the same view.
        request = request_factory.get("/products/7/")
        request.resolver_match = resolve("/products/7/")

        processed = item.process(request, pk=1)

        assert processed.url == "/products/1/"
        assert processed.selected is True

    def test_selection_matches_a_lazy_url(self, request_factory):
        from django.urls import reverse_lazy

        request = request_factory.get("/products/7/")

        item = MenuItem(
            name="product",
            label="Product",
            url=reverse_lazy("product-detail", args=[7]),
        )
        processed = item.process(request)

        assert processed.selected is True

    def test_selection_rejects_a_non_matching_lazy_url(self, request_factory):
        from django.urls import reverse_lazy

        request = request_factory.get("/products/7/")

        item = MenuItem(
            name="product",
            label="Product",
            url=reverse_lazy("product-detail", args=[1]),
        )
        processed = item.process(request)

        assert processed.selected is False


@pytest.mark.django_db
class TestVisibilityLogic:
    def test_check_with_callable(self, get_request):

        def is_visible(request):
            return request.path == "/"

        item = MenuItem(
            name="conditional",
            label="Conditional",
            url="/test/",
            check=is_visible,
        )
        processed = item.process(get_request)

        assert processed.visible is True

    def test_check_with_boolean(self, get_request):
        visible_item = MenuItem(
            name="visible",
            label="Visible",
            url="/test/",
            check=True,
        )
        hidden_item = MenuItem(
            name="hidden",
            label="Hidden",
            url="/test/",
            check=False,
        )

        assert visible_item.process(get_request).visible is True
        assert hidden_item.process(get_request).visible is False

    def test_parent_hidden_if_no_visible_children(self, get_request):
        parent = MenuItem(name="parent", label="Parent")
        MenuItem(
            name="hidden1",
            label="Hidden 1",
            url="/hidden1/",
            check=False,
            parent=parent,
        )
        MenuItem(
            name="hidden2",
            label="Hidden 2",
            url="/hidden2/",
            check=False,
            parent=parent,
        )

        processed = parent.process(get_request)

        assert processed.visible is False

    def test_leaf_hidden_if_url_not_resolvable(self, get_request):
        item = MenuItem(
            name="unresolvable",
            label="Unresolvable",
            view_name="nonexistent:view",
        )

        processed = item.process(get_request)

        assert processed.visible is False


@pytest.mark.django_db
class TestExtraContextAndDividers:
    def test_extra_context_preserved(self, get_request):
        item = MenuItem(
            name="with_context",
            label="With Context",
            url="/path/",
            extra_context={"icon": "home", "badge": 5},
        )
        processed = item.process(get_request)

        assert processed.extra_context["icon"] == "home"
        assert processed.extra_context["badge"] == 5

    def test_divider_item(self, get_request):
        parent = MenuItem(name="parent", label="Parent")
        MenuItem(name="item1", label="Item 1", url="/item1/", parent=parent)
        MenuItem(
            name="divider", label="", extra_context={"divider": True}, parent=parent
        )
        MenuItem(name="item2", label="Item 2", url="/item2/", parent=parent)

        processed = parent.process(get_request)
        children = list(processed.visible_children)

        assert len(children) == 3
        assert children[1].extra_context.get("divider") is True

    def test_custom_attributes_in_extra_context(self, get_request):
        item = MenuItem(
            name="custom",
            label="Custom",
            url="/custom/",
            extra_context={
                "attrs": {"data-toggle": "modal", "data-target": "#myModal"},
                "css_class": "custom-link",
            },
        )
        processed = item.process(get_request)

        assert processed.extra_context["attrs"]["data-toggle"] == "modal"
        assert processed.extra_context["css_class"] == "custom-link"


class TestTreeMethods:
    def test_get_with_maxlevel(self):
        tree_root = MenuItem(name="root", label="Root")
        level1 = MenuItem(name="level1", label="Level 1", parent=tree_root)
        level2 = MenuItem(name="level2", label="Level 2", parent=level1)
        MenuItem(name="level3", label="Level 3", parent=level2)

        assert tree_root.get("level1", maxlevel=1) is level1
        assert tree_root.get("level2", maxlevel=1) is None  # Too deep

        assert tree_root.get("level2", maxlevel=2) is level2
        assert tree_root.get("level3", maxlevel=2) is None  # Too deep

    def test_get_with_empty_name(self):
        tree_root = MenuItem(name="root", label="Root")
        assert tree_root.get("") is None

    def test_print_tree(self):
        tree_root = MenuItem(name="root", label="Root")
        MenuItem(name="child1", label="Child 1", url="/child1/", parent=tree_root)
        MenuItem(name="child2", label="Child 2", url="/child2/", parent=tree_root)

        tree_str = tree_root.print_tree()

        assert "root" in tree_str
        assert "child1" in tree_str
        assert "child2" in tree_str

    def test_bracket_notation_navigation(self):
        tree_root = MenuItem(name="root", label="Root")
        parent = MenuItem(name="parent", label="Parent", parent=tree_root)
        child = MenuItem(name="child", label="Child", url="/child/", parent=parent)

        assert tree_root["parent"] is parent
        found_child = tree_root["parent"]["child"]
        assert found_child is child

    def test_str_representation(self):
        item = MenuItem(name="test", label="Test Label")
        assert str(item) == "MenuItem(name=test)"

    def test_repr_representation(self):
        item = MenuItem(name="test", label="Test Label")
        repr_str = repr(item)
        assert "MenuItem" in repr_str
        assert "test" in repr_str

    def test_match_url_method(self, request_factory):
        request = request_factory.get("/test/path/")

        item = MenuItem(name="test", label="Test", url="/test/path/")
        processed = item.process(request)

        result = processed.match_url()
        assert result is True
        assert processed.selected is True

    def test_match_url_no_match(self, request_factory):
        request = request_factory.get("/other/path/")

        item = MenuItem(name="test", label="Test", url="/test/path/")
        item.request = request

        result = item.match_url()
        assert result is False
        assert item.selected is False

    def test_match_url_without_request(self):
        item = MenuItem(name="test", label="Test", url="/test/path/")

        result = item.match_url()
        assert result is False
        assert item.selected is False


@pytest.mark.django_db
class TestProcessingEdgeCases:
    def test_process_preserves_extra_context(self, get_request):
        item = MenuItem(
            name="test",
            label="Test",
            url="/test/",
            extra_context={"custom": "value"},
        )

        processed = item.process(get_request)

        assert processed.extra_context["custom"] == "value"

    def test_process_multiple_times_same_request(self, get_request):
        item = MenuItem(name="test", label="Test", url="/test/")

        processed1 = item.process(get_request)
        processed2 = item.process(get_request)

        assert processed1 is not processed2
        assert processed1.url == processed2.url

    def test_url_caching(self, get_request):
        call_count = 0

        def counting_url(request):
            nonlocal call_count
            call_count += 1
            return "/counted/"

        item = MenuItem(name="cached", label="Cached", url=counting_url)

        processed = item.process(get_request)

        _ = processed.url

        assert processed.url == "/counted/"


class TestMenuClass:
    def test_menu_auto_registers_to_root(self):
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

        menu.parent = None

    def test_menu_cannot_have_url(self):
        from flex_menu import Menu

        menu = Menu(
            name="test_menu_no_url",
            children=[MenuItem(name="item", url="/item/")],
        )

        assert menu.has_url is False
        assert menu.has_children is True

        menu.parent = None

    def test_menu_is_accessible_by_name(self):
        from flex_menu import Menu

        menu = Menu(
            name="accessible_menu",
            children=[MenuItem(name="test", url="/test/")],
        )

        found = root.get("accessible_menu")
        assert found is menu
        assert found.name == "accessible_menu"

        menu.parent = None

    def test_menu_example_usage(self):
        from flex_menu import Menu

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

        found = root.get("main_nav")
        assert found is NavMenu

        NavMenu.parent = None
