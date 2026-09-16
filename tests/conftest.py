"""
Shared test configuration and fixtures for django-flex-menus.
"""

import pytest
from django.test import RequestFactory, override_settings

from flex_menu import MenuItem, root
from tests.factories import GroupFactory, PermissionFactory, UserFactory


@pytest.fixture
def request_factory():
    """Provides a Django RequestFactory for creating mock requests."""
    return RequestFactory()


@pytest.fixture
def get_request(request_factory):
    """Creates a basic GET request."""
    return request_factory.get("/")


@pytest.fixture
def mock_request(request_factory):
    """Creates a basic mock request."""
    request = request_factory.get("/test/")
    request.user = None  # Will be set by user fixtures
    return request


@pytest.fixture
def authenticated_request(request_factory, user):
    """Creates a mock request with an authenticated user."""
    request = request_factory.get("/test/")
    request.user = user
    return request


@pytest.fixture
def staff_request(request_factory, staff_user):
    """Creates a mock request with a staff user."""
    request = request_factory.get("/test/")
    request.user = staff_user
    return request


@pytest.fixture
def superuser_request(request_factory, superuser):
    """Creates a mock request with a superuser."""
    request = request_factory.get("/test/")
    request.user = superuser
    return request


@pytest.fixture
def user():
    """Creates a regular user."""
    return UserFactory()


@pytest.fixture
def staff_user():
    """Creates a staff user."""
    return UserFactory(is_staff=True)


@pytest.fixture
def superuser():
    """Creates a superuser."""
    return UserFactory(is_staff=True, is_superuser=True)


@pytest.fixture
def user_with_permissions(user):
    """Creates a user with specific permissions."""
    permission = PermissionFactory()
    user.user_permissions.add(permission)
    return user


@pytest.fixture
def user_with_group(user):
    """Creates a user in a specific group."""
    group = GroupFactory()
    user.groups.add(group)
    # Store the group name for test reference
    user._test_group_name = group.name
    return user


@pytest.fixture
def simple_menu_item():
    """Creates a basic MenuItem instance with URL."""
    return MenuItem(
        name="test_item", url="/test/", extra_context={"label": "Test Item"}
    )


@pytest.fixture
def menu_item_with_view():
    """Creates a MenuItem with a view name."""
    return MenuItem(
        name="test_item_view", view_name="admin:index", extra_context={"label": "Admin"}
    )


@pytest.fixture
def parent_menu_item():
    """Creates a MenuItem with children."""
    return MenuItem(
        name="parent_menu",
        extra_context={"label": "Parent Menu"},
        children=[
            MenuItem(name="child1", url="/child1/", extra_context={"label": "Child 1"}),
            MenuItem(name="child2", url="/child2/", extra_context={"label": "Child 2"}),
        ],
    )


@pytest.fixture
def complex_menu_tree():
    """Creates a complex menu tree for testing."""
    # Build tree structure
    return MenuItem(
        name="main_menu",
        extra_context={"label": "Main Menu"},
        children=[
            MenuItem(name="home", url="/", extra_context={"label": "Home"}),
            MenuItem(name="about", url="/about/", extra_context={"label": "About"}),
            # Products submenu
            MenuItem(
                name="products",
                extra_context={"label": "Products"},
                children=[
                    MenuItem(
                        name="product1",
                        url="/products/1/",
                        extra_context={"label": "Product 1"},
                    ),
                    MenuItem(
                        name="product2",
                        url="/products/2/",
                        extra_context={"label": "Product 2"},
                    ),
                ],
            ),
            # Admin submenu
            MenuItem(
                name="admin",
                extra_context={"label": "Admin"},
                children=[
                    MenuItem(
                        name="admin_users",
                        view_name="admin:auth_user_changelist",
                        extra_context={"label": "Users"},
                    ),
                    MenuItem(
                        name="admin_groups",
                        view_name="admin:auth_group_changelist",
                        extra_context={"label": "Groups"},
                    ),
                ],
            ),
        ],
    )


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """
    Grants database access to all tests.
    """
    pass


@pytest.fixture
def settings_with_debug():
    """Provides settings with DEBUG=True for testing URL failure logging."""
    with override_settings(DEBUG=True, FLEX_MENU_LOG_URL_FAILURES=True):
        yield


@pytest.fixture
def settings_without_debug():
    """Provides settings with DEBUG=False for testing URL failure logging."""
    with override_settings(DEBUG=False, FLEX_MENU_LOG_URL_FAILURES=False):
        yield


@pytest.fixture(autouse=True)
def clean_root():
    # Backup children
    original_children = list(root.children)
    yield
    # Restore children
    root.children = original_children
    for child in root.children:
        child.parent = root
