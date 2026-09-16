"""Tests for tests/factories.py."""

import pytest

from tests.factories import GroupFactory, PermissionFactory, UserFactory


@pytest.mark.django_db
class TestUserFactory:
    def test_creates_unique_users(self):
        user1 = UserFactory()
        user2 = UserFactory()

        assert user1.username != user2.username
        assert user1.email != user2.email

    def test_password_is_usable(self):
        user = UserFactory()
        assert user.check_password("testpass123") is True

    def test_overrides_are_applied(self):
        user = UserFactory(is_staff=True, is_superuser=True)
        assert user.is_staff is True
        assert user.is_superuser is True


@pytest.mark.django_db
class TestGroupFactory:
    def test_creates_unique_groups(self):
        group1 = GroupFactory()
        group2 = GroupFactory()

        assert group1.name != group2.name


@pytest.mark.django_db
class TestPermissionFactory:
    def test_creates_unique_permissions(self):
        perm1 = PermissionFactory()
        perm2 = PermissionFactory()

        assert perm1.codename != perm2.codename

    def test_overrides_are_applied(self):
        perm = PermissionFactory(codename="custom_perm", name="Custom Permission")
        assert perm.codename == "custom_perm"
        assert perm.name == "Custom Permission"
