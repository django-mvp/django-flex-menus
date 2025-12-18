"""
Views for demonstrating context-specific menus.
"""

from django.shortcuts import redirect
from django.views.generic import TemplateView

from .models import Project


class ContextMenuDemoView(TemplateView):
    """Demonstration page showing various context-specific menu patterns."""

    template_name = "context_menu_demo.html"

    def get_context_data(self, **kwargs):
        """Provide sample data for demonstration."""
        context = super().get_context_data(**kwargs)

        # Get slug from URL or use default
        slug = self.kwargs.get("slug", "demo-project")

        # Get or create a demo project with the specified slug
        demo_project, created = Project.objects.get_or_create(
            slug=slug,
            defaults={
                "name": "Demo Project",
                "status": "draft",
                "is_public": False,
            },
        )

        context["project"] = demo_project
        return context

    def post(self, request, *args, **kwargs):
        """Handle status change from select dropdown."""
        # Get slug from URL or use default
        slug = self.kwargs.get("slug", "demo-project")

        # Get the demo project
        project = Project.objects.get(slug=slug)

        # Get the selected status from the form
        new_status = request.POST.get("new_status")

        if new_status in ["draft", "active", "archived"]:
            project.status = new_status

            # Set public status based on status
            project.is_public = new_status == "active"
            project.save()

        # Redirect to same page to show updated menu
        return redirect("context_menu_demo", slug=slug)


class SerializationDemoView(TemplateView):
    """Demonstration page showing menu serialization features."""

    template_name = "serialization_demo.html"

    def get_context_data(self, **kwargs):
        """Provide sample data for demonstration."""
        context = super().get_context_data(**kwargs)

        # Get or create a demo project for the context-aware menu example
        demo_project, created = Project.objects.get_or_create(
            slug="serialization-demo-project",
            defaults={
                "name": "Serialization Demo Project",
                "status": "active",
                "is_public": True,
            },
        )

        context["project"] = demo_project
        return context
