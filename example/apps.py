"""App configuration for the example project."""

from django.apps import AppConfig


class ExampleConfig(AppConfig):
    """Django app config for the example project."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "example"
