"""Example models for demonstrating context-specific menus."""

from django.db import models


class Project(models.Model):
    """Simple project model for demonstration."""

    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ("draft", "Draft"),
            ("active", "Active"),
            ("archived", "Archived"),
        ],
        default="draft",
    )
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """Show the project's name."""
        return self.name

    class Meta:
        ordering = ["-created_at"]
