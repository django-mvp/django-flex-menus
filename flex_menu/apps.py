"""App configuration for flex_menu."""

from django.apps import AppConfig
from django.utils.module_loading import autodiscover_modules


class FlexMenuConfig(AppConfig):
    """Django app config for flex_menu."""

    name = "flex_menu"

    def ready(self):
        """Autodiscover each installed app's menus module."""
        autodiscover_modules("menus")
