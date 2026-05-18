from django.apps import AppConfig
from django.utils.module_loading import autodiscover_modules


class FlexMenuConfig(AppConfig):
    name = "flex_menu"

    def ready(self):
        autodiscover_modules("menus")
