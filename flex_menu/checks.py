"""
Predefined check functions for Django Flex Menu.

These functions can be used as the 'check' parameter when creating menu items
to control their visibility based on various conditions.

All check functions receive a Django request object and optional keyword arguments.
They should return a boolean value indicating whether the menu item should be visible.
"""


def user_is_staff(request, **kwargs):
    """
    Check if the user associated with the given request is a staff member.

    Args:
        request: The HTTP request object
        **kwargs: Additional arguments (ignored)

    Returns:
        bool: True if the user is a staff member, False otherwise.
    """
    return hasattr(request, "user") and request.user and request.user.is_staff


def user_is_authenticated(request, **kwargs):
    """
    Checks if the user associated with the given request is authenticated.

    Args:
        request: The HTTP request object
        **kwargs: Additional arguments (ignored)

    Returns:
        bool: True if the user is authenticated, False otherwise.
    """
    return hasattr(request, "user") and request.user and request.user.is_authenticated


def user_is_anonymous(request, **kwargs):
    """
    Check if the user associated with the given request is anonymous.

    Args:
        request: The HTTP request object
        **kwargs: Additional arguments (ignored)

    Returns:
        bool: True if the user is anonymous, False otherwise.
    """
    return not hasattr(request, "user") or not request.user or request.user.is_anonymous


def user_is_superuser(request, **kwargs):
    """
    Check if the user associated with the given request is a superuser.

    Args:
        request: The HTTP request object
        **kwargs: Additional arguments (ignored)

    Returns:
        bool: True if the user is a superuser, False otherwise.
    """
    return hasattr(request, "user") and request.user and request.user.is_superuser


def user_in_any_group(*groups):
    """
    Checks if the authenticated user belongs to any of the specified groups.

    Args:
        *groups: Variable length argument list of group names to check against.
    Returns:
        function: A function that takes a Django request object and optional keyword arguments,
                  and returns True if the user is authenticated and is a member of any of the specified groups,
                  otherwise False.
    Example:
        MenuLink(
            name="Authors only",
            view_name="author-management-page",
            check=user_in_any_group('authors'),
            )
    """

    def _function(request, **kwargs):
        return (
            hasattr(request, "user")
            and request.user
            and request.user.is_authenticated
            and request.user.groups.filter(name__in=groups).exists()
        )

    return _function


def user_has_any_permission(*perms: str):
    """
    Checks if the current user has at least one of the specified permissions.

    Args:
        *perms (str): One or more permission strings to check against the user.
    Returns:
        bool: True if the user has at least one of the specified permissions, False otherwise.
    Example:
        MenuLink(
            name="Authors",
            view_name="book-create",
            check=user_has_any_permission('book.add_book'),
            )
    """

    def _check(request, **kwargs):
        return (
            hasattr(request, "user")
            and request.user
            and request.user.is_authenticated
            and any(request.user.has_perm(perm) for perm in perms)
        )

    return _check


def user_has_object_permission(perm: str):
    """
    Checks if the requesting user has a specific object-level permission.

    Note: This function is removed as it depended on the instance parameter.
    For object-level permissions, create custom check functions that get
    the object from the request context or other means.

    Args:
        perm (str): The permission codename to check (e.g., 'blog.change_post').
    Returns:
        function: A function that always returns False with a warning.
    """

    def _check(request, **kwargs):
        import warnings

        warnings.warn(
            "user_has_object_permission is deprecated. Create custom check functions "
            "that retrieve objects from request context instead of relying on instance parameter.",
            DeprecationWarning,
            stacklevel=2,
        )
        return False

    return _check


def user_in_all_groups(*groups):
    """
    Checks if the authenticated user belongs to ALL of the specified groups.

    Args:
        *groups: Variable length argument list of group names to check against.
    Returns:
        function: A function that takes a Django request object and optional keyword arguments,
                  and returns True if the user is authenticated and is a member of ALL specified groups,
                  otherwise False.
    Example:
        MenuLink(
            name="Authors and Editors only",
            view_name="special-page",
            check=user_in_all_groups('authors', 'editors'),
            )
    """

    def _function(request, **kwargs):
        if not (hasattr(request, "user") and request.user and request.user.is_authenticated):
            return False

        user_groups = request.user.groups.values_list("name", flat=True)
        return all(group in user_groups for group in groups)

    return _function


def user_has_all_permissions(*perms: str):
    """
    Checks if the current user has ALL of the specified permissions.

    Args:
        *perms (str): One or more permission strings to check against the user.
    Returns:
        function: A function that returns True if the user has ALL specified permissions, False otherwise.
    Example:
        MenuLink(
            name="Full Admin",
            view_name="admin-panel",
            check=user_has_all_permissions('auth.add_user', 'auth.change_user', 'auth.delete_user'),
            )
    """

    def _check(request, **kwargs):
        if not (hasattr(request, "user") and request.user and request.user.is_authenticated):
            return False

        return all(request.user.has_perm(perm) for perm in perms)

    return _check


def user_is_active(request, **kwargs):
    """
    Check if the user associated with the given request is active.

    Args:
        request: The HTTP request object
        **kwargs: Additional arguments (ignored)

    Returns:
        bool: True if the user is active, False otherwise.
    """
    if not (hasattr(request, "user") and request.user):
        return False
    return bool(getattr(request.user, "is_active", False))


def user_email_verified(request, **kwargs):
    """
    Check if the user's email is verified (if the user model has an email_verified field).

    Args:
        request: The HTTP request object
        **kwargs: Additional arguments (ignored)

    Returns:
        bool: True if the user's email is verified, False otherwise.
    """
    if not (hasattr(request, "user") and request.user and request.user.is_authenticated):
        return False

    # Check if the user model has email_verified field
    if hasattr(request.user, "email_verified"):
        return request.user.email_verified

    # If no email_verified field, assume verified for authenticated users
    return True


def user_has_profile(request, **kwargs):
    """
    Check if the user has an associated profile (if using a profile model).

    Args:
        request: The HTTP request object
        **kwargs: Additional arguments (ignored)

    Returns:
        bool: True if the user has a profile, False otherwise.
    """
    if not (hasattr(request, "user") and request.user and request.user.is_authenticated):
        return False

    # Check common profile relationship names
    profile_attrs = ["profile", "userprofile", "user_profile"]

    for attr in profile_attrs:
        if hasattr(request.user, attr):
            try:
                profile = getattr(request.user, attr)
                return profile is not None
            except AttributeError:
                continue

    return True  # Assume profile exists if no profile model detected


def request_is_ajax(request, **kwargs):
    """
    Check if the request is an AJAX request.

    Args:
        request: The HTTP request object
        **kwargs: Additional arguments (ignored)

    Returns:
        bool: True if the request is AJAX, False otherwise.
    """
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


def request_is_secure(request, **kwargs):
    """
    Check if the request is secure (HTTPS).

    Args:
        request: The HTTP request object
        **kwargs: Additional arguments (ignored)

    Returns:
        bool: True if the request is secure, False otherwise.
    """
    return request.is_secure()


def request_method_is(*methods):
    """
    Check if the request method matches any of the specified methods.

    Args:
        *methods: Variable length argument list of HTTP methods to check against.
    Returns:
        function: A function that takes a Django request object and returns True
                  if the request method matches any of the specified methods.
    Example:
        MenuLink(
            name="POST only action",
            view_name="post-handler",
            check=request_method_is('POST'),
            )
    """

    def _check(request, **kwargs):
        return request.method.upper() in [method.upper() for method in methods]

    return _check


def user_attribute_equals(attribute_name: str, expected_value):
    """
    Check if a user attribute equals a specific value.

    Args:
        attribute_name (str): The name of the user attribute to check.
        expected_value: The expected value to compare against.
    Returns:
        function: A function that returns True if the user attribute equals the expected value.
    Example:
        MenuLink(
            name="Premium users only",
            view_name="premium-content",
            check=user_attribute_equals('subscription_type', 'premium'),
            )
    """

    def _check(request, **kwargs):
        if not (hasattr(request, "user") and request.user and request.user.is_authenticated):
            return False

        if hasattr(request.user, attribute_name):
            return getattr(request.user, attribute_name) == expected_value

        return False

    return _check


def user_in_group_with_permission(group_name: str, permission: str):
    """
    Check if the user is in a specific group AND has a specific permission.

    Args:
        group_name (str): The name of the group to check.
        permission (str): The permission to check.
    Returns:
        function: A function that returns True if the user is in the group and has the permission.
    Example:
        MenuLink(
            name="Editor with publish rights",
            view_name="publish-content",
            check=user_in_group_with_permission('editors', 'blog.publish_post'),
            )
    """

    def _check(request, **kwargs):
        if not (hasattr(request, "user") and request.user and request.user.is_authenticated):
            return False

        has_group = request.user.groups.filter(name=group_name).exists()
        has_permission = request.user.has_perm(permission)

        return has_group and has_permission

    return _check


def debug_mode_only(request, **kwargs):
    """
    Check if Django is running in debug mode.

    Args:
        request: The HTTP request object
        **kwargs: Additional arguments (ignored)

    Returns:
        bool: True if DEBUG=True, False otherwise.
    """
    from django.conf import settings

    return settings.DEBUG


def combine_checks(*check_functions, operator="and"):
    """
    Combine multiple check functions with AND or OR logic.

    Args:
        *check_functions: Variable length argument list of check functions.
        operator (str): Either 'and' or 'or' to specify the combination logic.
    Returns:
        function: A combined check function.
    Example:
        MenuLink(
            name="Staff or superuser",
            view_name="admin-area",
            check=combine_checks(user_is_staff, user_is_superuser, operator='or'),
            )
    """

    def _check(request, **kwargs):
        if operator.lower() == "or":
            return any(check_func(request, **kwargs) for check_func in check_functions)
        else:  # default to 'and'
            return all(check_func(request, **kwargs) for check_func in check_functions)

    return _check


def negate_check(check_function):
    """
    Negate a check function (NOT logic).

    Args:
        check_function: The check function to negate.
    Returns:
        function: A negated check function.
    Example:
        MenuLink(
            name="Non-staff only",
            view_name="public-area",
            check=negate_check(user_is_staff),
            )
    """

    def _check(request, **kwargs):
        return not check_function(request, **kwargs)

    return _check
