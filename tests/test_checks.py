"""Tests for check functions in checks.py."""

import warnings

import pytest

from tests.factories import GroupFactory, PermissionFactory


@pytest.mark.django_db
class TestUserStatusChecks:
    """Test basic user status check functions."""

    def test_user_is_staff_true(self, get_request, staff_user):
        """Test user_is_staff returns True for staff users."""
        from flex_menu.checks import user_is_staff

        get_request.user = staff_user
        assert user_is_staff(get_request) is True

    def test_user_is_staff_false(self, get_request, user):
        """Test user_is_staff returns False for regular users."""
        from flex_menu.checks import user_is_staff

        get_request.user = user
        assert user_is_staff(get_request) is False

    def test_user_is_staff_no_user(self, get_request):
        """Test user_is_staff returns False when no user."""
        from flex_menu.checks import user_is_staff

        # Request without user attribute
        assert user_is_staff(get_request) is False

    def test_user_is_authenticated_true(self, get_request, user):
        """Test user_is_authenticated returns True for authenticated users."""
        from flex_menu.checks import user_is_authenticated

        get_request.user = user
        assert user_is_authenticated(get_request) is True

    def test_user_is_authenticated_false(self, get_request):
        """Test user_is_authenticated returns False for anonymous users."""
        from django.contrib.auth.models import AnonymousUser

        from flex_menu.checks import user_is_authenticated

        get_request.user = AnonymousUser()
        assert user_is_authenticated(get_request) is False

    def test_user_is_anonymous_true(self, get_request):
        """Test user_is_anonymous returns True for anonymous users."""
        from django.contrib.auth.models import AnonymousUser

        from flex_menu.checks import user_is_anonymous

        get_request.user = AnonymousUser()
        assert user_is_anonymous(get_request) is True

    def test_user_is_anonymous_false(self, get_request, user):
        """Test user_is_anonymous returns False for authenticated users."""
        from flex_menu.checks import user_is_anonymous

        get_request.user = user
        assert user_is_anonymous(get_request) is False

    def test_user_is_anonymous_no_user(self, get_request):
        """Test user_is_anonymous returns True when no user."""
        from flex_menu.checks import user_is_anonymous

        # Request without user attribute
        assert user_is_anonymous(get_request) is True

    def test_user_is_superuser_true(self, get_request, superuser):
        """Test user_is_superuser returns True for superusers."""
        from flex_menu.checks import user_is_superuser

        get_request.user = superuser
        assert user_is_superuser(get_request) is True

    def test_user_is_superuser_false(self, get_request, user):
        """Test user_is_superuser returns False for regular users."""
        from flex_menu.checks import user_is_superuser

        get_request.user = user
        assert user_is_superuser(get_request) is False

    def test_user_is_active_true(self, get_request, user):
        """Test user_is_active returns True for active users."""
        from flex_menu.checks import user_is_active

        get_request.user = user
        assert user_is_active(get_request) is True

    def test_user_is_active_false(self, get_request, user):
        """Test user_is_active returns False for inactive users."""
        from flex_menu.checks import user_is_active

        user.is_active = False
        user.save()
        get_request.user = user
        assert user_is_active(get_request) is False

    def test_user_is_active_no_user(self, get_request):
        """Test user_is_active returns False when no user."""
        from flex_menu.checks import user_is_active

        assert user_is_active(get_request) is False


@pytest.mark.django_db
class TestGroupChecks:
    """Test group-related check functions."""

    def test_user_in_any_group_single_match(self, get_request, user):
        """Test user_in_any_group with user in one group."""
        from flex_menu.checks import user_in_any_group

        group = GroupFactory(name="authors")
        user.groups.add(group)
        get_request.user = user

        check = user_in_any_group("authors")
        assert check(get_request) is True

    def test_user_in_any_group_multiple_match(self, get_request, user):
        """Test user_in_any_group with multiple groups."""
        from flex_menu.checks import user_in_any_group

        group1 = GroupFactory(name="authors")
        GroupFactory(name="editors")
        user.groups.add(group1)
        get_request.user = user

        check = user_in_any_group("authors", "editors")
        assert check(get_request) is True

    def test_user_in_any_group_no_match(self, get_request, user):
        """Test user_in_any_group with user not in specified groups."""
        from flex_menu.checks import user_in_any_group

        group = GroupFactory(name="viewers")
        user.groups.add(group)
        get_request.user = user

        check = user_in_any_group("authors", "editors")
        assert check(get_request) is False

    def test_user_in_any_group_unauthenticated(self, get_request):
        """Test user_in_any_group returns False for unauthenticated users."""
        from django.contrib.auth.models import AnonymousUser

        from flex_menu.checks import user_in_any_group

        get_request.user = AnonymousUser()
        check = user_in_any_group("authors")
        assert check(get_request) is False

    def test_user_in_all_groups_match(self, get_request, user):
        """Test user_in_all_groups with user in all groups."""
        from flex_menu.checks import user_in_all_groups

        group1 = GroupFactory(name="authors")
        group2 = GroupFactory(name="editors")
        user.groups.add(group1, group2)
        get_request.user = user

        check = user_in_all_groups("authors", "editors")
        assert check(get_request) is True

    def test_user_in_all_groups_partial_match(self, get_request, user):
        """Test user_in_all_groups with user in only some groups."""
        from flex_menu.checks import user_in_all_groups

        group1 = GroupFactory(name="authors")
        GroupFactory(name="editors")
        user.groups.add(group1)
        get_request.user = user

        check = user_in_all_groups("authors", "editors")
        assert check(get_request) is False

    def test_user_in_all_groups_unauthenticated(self, get_request):
        """Test user_in_all_groups returns False for unauthenticated users."""
        from django.contrib.auth.models import AnonymousUser

        from flex_menu.checks import user_in_all_groups

        get_request.user = AnonymousUser()
        check = user_in_all_groups("authors")
        assert check(get_request) is False


@pytest.mark.django_db
class TestPermissionChecks:
    """Test permission-related check functions."""

    def test_user_has_any_permission_match(self, get_request, user):
        """Test user_has_any_permission with user having one permission."""
        from flex_menu.checks import user_has_any_permission

        perm = PermissionFactory(codename="test_permission", name="Test Permission")
        user.user_permissions.add(perm)
        get_request.user = user

        check = user_has_any_permission("auth.test_permission")
        assert check(get_request) is True

    def test_user_has_any_permission_no_match(self, get_request, user):
        """Test user_has_any_permission with user lacking permission."""
        from flex_menu.checks import user_has_any_permission

        get_request.user = user
        check = user_has_any_permission("auth.nonexistent_permission")
        assert check(get_request) is False

    def test_user_has_any_permission_unauthenticated(self, get_request):
        """Test user_has_any_permission returns False for unauthenticated users."""
        from django.contrib.auth.models import AnonymousUser

        from flex_menu.checks import user_has_any_permission

        get_request.user = AnonymousUser()
        check = user_has_any_permission("auth.add_user")
        assert check(get_request) is False

    def test_user_has_all_permissions_match(self, get_request, user):
        """Test user_has_all_permissions with user having all permissions."""
        from flex_menu.checks import user_has_all_permissions

        perm1 = PermissionFactory(codename="test_perm1", name="Test Perm 1")
        perm2 = PermissionFactory(codename="test_perm2", name="Test Perm 2")
        user.user_permissions.add(perm1, perm2)
        get_request.user = user

        check = user_has_all_permissions("auth.test_perm1", "auth.test_perm2")
        assert check(get_request) is True

    def test_user_has_all_permissions_partial_match(self, get_request, user):
        """Test user_has_all_permissions with user having only some permissions."""
        from flex_menu.checks import user_has_all_permissions

        perm1 = PermissionFactory(codename="test_perm1", name="Test Perm 1")
        user.user_permissions.add(perm1)
        get_request.user = user

        check = user_has_all_permissions("auth.test_perm1", "auth.test_perm2")
        assert check(get_request) is False

    def test_user_has_object_permission_deprecated(self, get_request, user):
        """Test user_has_object_permission shows deprecation warning."""
        from flex_menu.checks import user_has_object_permission

        get_request.user = user
        check = user_has_object_permission("auth.change_user")

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = check(get_request)

            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "deprecated" in str(w[0].message).lower()
            assert result is False


@pytest.mark.django_db
class TestUserAttributeChecks:
    """Test user attribute-related check functions."""

    def test_user_email_verified_true(self, get_request, user):
        """Test user_email_verified when email is verified."""
        from flex_menu.checks import user_email_verified

        # Add email_verified attribute to user
        user.email_verified = True
        get_request.user = user

        assert user_email_verified(get_request) is True

    def test_user_email_verified_false(self, get_request, user):
        """Test user_email_verified when email is not verified."""
        from flex_menu.checks import user_email_verified

        user.email_verified = False
        get_request.user = user

        assert user_email_verified(get_request) is False

    def test_user_email_verified_no_field(self, get_request, user):
        """Test user_email_verified defaults to True when field doesn't exist."""
        from flex_menu.checks import user_email_verified

        get_request.user = user
        # User model doesn't have email_verified by default
        assert user_email_verified(get_request) is True

    def test_user_email_verified_unauthenticated(self, get_request):
        """Test user_email_verified returns False for unauthenticated users."""
        from django.contrib.auth.models import AnonymousUser

        from flex_menu.checks import user_email_verified

        get_request.user = AnonymousUser()
        assert user_email_verified(get_request) is False

    def test_user_has_profile_with_profile(self, get_request, user):
        """Test user_has_profile when profile exists."""
        from flex_menu.checks import user_has_profile

        # Mock a profile attribute
        user.profile = type("Profile", (), {"name": "Test Profile"})()
        get_request.user = user

        assert user_has_profile(get_request) is True

    def test_user_has_profile_no_profile_attr(self, get_request, user):
        """Test user_has_profile defaults to True when no profile attribute."""
        from flex_menu.checks import user_has_profile

        get_request.user = user
        # No profile attribute by default
        assert user_has_profile(get_request) is True

    def test_user_has_profile_unauthenticated(self, get_request):
        """Test user_has_profile returns False for unauthenticated users."""
        from django.contrib.auth.models import AnonymousUser

        from flex_menu.checks import user_has_profile

        get_request.user = AnonymousUser()
        assert user_has_profile(get_request) is False

    def test_user_attribute_equals_match(self, get_request, user):
        """Test user_attribute_equals when attribute matches."""
        from flex_menu.checks import user_attribute_equals

        user.subscription_type = "premium"
        get_request.user = user

        check = user_attribute_equals("subscription_type", "premium")
        assert check(get_request) is True

    def test_user_attribute_equals_no_match(self, get_request, user):
        """Test user_attribute_equals when attribute doesn't match."""
        from flex_menu.checks import user_attribute_equals

        user.subscription_type = "basic"
        get_request.user = user

        check = user_attribute_equals("subscription_type", "premium")
        assert check(get_request) is False

    def test_user_attribute_equals_no_attribute(self, get_request, user):
        """Test user_attribute_equals when attribute doesn't exist."""
        from flex_menu.checks import user_attribute_equals

        get_request.user = user
        check = user_attribute_equals("nonexistent_attr", "value")
        assert check(get_request) is False

    def test_user_attribute_equals_unauthenticated(self, get_request):
        """Test user_attribute_equals returns False for unauthenticated users."""
        from django.contrib.auth.models import AnonymousUser

        from flex_menu.checks import user_attribute_equals

        get_request.user = AnonymousUser()
        check = user_attribute_equals("attribute", "value")
        assert check(get_request) is False


@pytest.mark.django_db
class TestRequestChecks:
    """Test request-related check functions."""

    def test_request_is_ajax_true(self, request_factory):
        """Test request_is_ajax returns True for AJAX requests."""
        from flex_menu.checks import request_is_ajax

        request = request_factory.get("/", HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        assert request_is_ajax(request) is True

    def test_request_is_ajax_false(self, request_factory):
        """Test request_is_ajax returns False for regular requests."""
        from flex_menu.checks import request_is_ajax

        request = request_factory.get("/")
        assert request_is_ajax(request) is False

    def test_request_is_secure_true(self, request_factory):
        """Test request_is_secure returns True for HTTPS requests."""
        from flex_menu.checks import request_is_secure

        request = request_factory.get("/", secure=True)
        assert request_is_secure(request) is True

    def test_request_is_secure_false(self, request_factory):
        """Test request_is_secure returns False for HTTP requests."""
        from flex_menu.checks import request_is_secure

        request = request_factory.get("/")
        assert request_is_secure(request) is False

    def test_request_method_is_match(self, request_factory):
        """Test request_method_is with matching method."""
        from flex_menu.checks import request_method_is

        request = request_factory.post("/")
        check = request_method_is("POST")
        assert check(request) is True

    def test_request_method_is_multiple_match(self, request_factory):
        """Test request_method_is with multiple methods."""
        from flex_menu.checks import request_method_is

        request = request_factory.put("/")
        check = request_method_is("POST", "PUT", "PATCH")
        assert check(request) is True

    def test_request_method_is_no_match(self, request_factory):
        """Test request_method_is with non-matching method."""
        from flex_menu.checks import request_method_is

        request = request_factory.get("/")
        check = request_method_is("POST", "PUT")
        assert check(request) is False

    def test_request_method_is_case_insensitive(self, request_factory):
        """Test request_method_is is case-insensitive."""
        from flex_menu.checks import request_method_is

        request = request_factory.get("/")
        check = request_method_is("get", "GET", "Get")
        assert check(request) is True


@pytest.mark.django_db
class TestCombinedChecks:
    """Test combined and composite check functions."""

    def test_user_in_group_with_permission_both_true(self, get_request, user):
        """Test user_in_group_with_permission when both conditions are met."""
        from flex_menu.checks import user_in_group_with_permission

        group = GroupFactory(name="editors")
        user.groups.add(group)

        perm = PermissionFactory(codename="publish_post", name="Publish Post")
        user.user_permissions.add(perm)
        get_request.user = user

        check = user_in_group_with_permission("editors", "auth.publish_post")
        assert check(get_request) is True

    def test_user_in_group_with_permission_only_group(self, get_request, user):
        """Test user_in_group_with_permission when only in group."""
        from flex_menu.checks import user_in_group_with_permission

        group = GroupFactory(name="editors")
        user.groups.add(group)
        get_request.user = user

        check = user_in_group_with_permission("editors", "auth.publish_post")
        assert check(get_request) is False

    def test_user_in_group_with_permission_only_permission(self, get_request, user):
        """Test user_in_group_with_permission when only has permission."""
        from flex_menu.checks import user_in_group_with_permission

        GroupFactory(name="editors")
        perm = PermissionFactory(codename="publish_post", name="Publish Post")
        user.user_permissions.add(perm)
        get_request.user = user

        check = user_in_group_with_permission("editors", "auth.publish_post")
        assert check(get_request) is False

    def test_combine_checks_and_all_true(self, get_request, staff_user):
        """Test combine_checks with AND logic when all checks pass."""
        from flex_menu.checks import (
            combine_checks,
            user_is_authenticated,
            user_is_staff,
        )

        get_request.user = staff_user
        check = combine_checks(user_is_authenticated, user_is_staff, operator="and")
        assert check(get_request) is True

    def test_combine_checks_and_one_false(self, get_request, user):
        """Test combine_checks with AND logic when one check fails."""
        from flex_menu.checks import (
            combine_checks,
            user_is_authenticated,
            user_is_staff,
        )

        get_request.user = user
        check = combine_checks(user_is_authenticated, user_is_staff, operator="and")
        assert check(get_request) is False

    def test_combine_checks_or_one_true(self, get_request, staff_user):
        """Test combine_checks with OR logic when one check passes."""
        from flex_menu.checks import combine_checks, user_is_staff, user_is_superuser

        get_request.user = staff_user
        check = combine_checks(user_is_staff, user_is_superuser, operator="or")
        assert check(get_request) is True

    def test_combine_checks_or_all_false(self, get_request, user):
        """Test combine_checks with OR logic when all checks fail."""
        from flex_menu.checks import combine_checks, user_is_staff, user_is_superuser

        get_request.user = user
        check = combine_checks(user_is_staff, user_is_superuser, operator="or")
        assert check(get_request) is False

    def test_combine_checks_default_operator(self, get_request, staff_user):
        """Test combine_checks defaults to AND operator."""
        from flex_menu.checks import (
            combine_checks,
            user_is_authenticated,
            user_is_staff,
        )

        get_request.user = staff_user
        check = combine_checks(user_is_authenticated, user_is_staff)
        assert check(get_request) is True

    def test_negate_check_true_becomes_false(self, get_request, staff_user):
        """Test negate_check inverts True to False."""
        from flex_menu.checks import negate_check, user_is_staff

        get_request.user = staff_user
        check = negate_check(user_is_staff)
        assert check(get_request) is False

    def test_negate_check_false_becomes_true(self, get_request, user):
        """Test negate_check inverts False to True."""
        from flex_menu.checks import negate_check, user_is_staff

        get_request.user = user
        check = negate_check(user_is_staff)
        assert check(get_request) is True


@pytest.mark.django_db
class TestDebugCheck:
    """Test debug mode check."""

    def test_debug_mode_only(self, get_request, settings):
        """Test debug_mode_only returns DEBUG setting value."""
        from flex_menu.checks import debug_mode_only

        settings.DEBUG = True
        assert debug_mode_only(get_request) is True

        settings.DEBUG = False
        assert debug_mode_only(get_request) is False
