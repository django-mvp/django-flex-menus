"""Factories for auth models used across the test suite."""

import factory
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = get_user_model()

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.Sequence(lambda n: f"user{n}@example.com")
    password = factory.PostGenerationMethodCall("set_password", "testpass123")


class GroupFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Group

    name = factory.Sequence(lambda n: f"group{n}")


class PermissionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Permission

    codename = factory.Sequence(lambda n: f"perm{n}")
    name = factory.Sequence(lambda n: f"Permission {n}")
    content_type = factory.LazyFunction(
        lambda: ContentType.objects.get_for_model(get_user_model())
    )
