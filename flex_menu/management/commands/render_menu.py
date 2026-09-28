"""Management command printing the registered menu tree."""

import logging

from django.core.management.base import BaseCommand

from flex_menu import root

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Print the full menu tree, or a single named menu's subtree."""

    def add_arguments(self, parser):
        """Add the optional ``--name`` argument selecting a single menu."""
        parser.add_argument("--name", type=str, required=False)

    def handle(self, *args, **options):
        """Print the requested menu's tree, or the full tree if none is named."""
        self.stdout.write(self.style.HTTP_INFO("Django Flex Menu:"))
        self.stdout.write(
            self.style.HTTP_INFO("========================================\n")
        )
        if name := options.get("name"):
            menu = root.get(name)
            if menu:
                self.stdout.write(menu.print_tree())
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f"Menu '{name}' not found. Try running the command without arguments to see the entire menu tree and validate that the specified menu is present."
                    )
                )
        else:
            self.stdout.write(root.print_tree())
