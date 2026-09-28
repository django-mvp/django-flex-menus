"""Views for demonstrating context-specific menus."""

from django.shortcuts import redirect
from django.views.generic import TemplateView

from .models import Project


class ContextMenuDemoView(TemplateView):
    """Demonstration page showing various context-specific menu patterns."""

    template_name = "context_menu_demo.html"

    def get_context_data(self, **kwargs):
        """Provide sample data for demonstration."""
        context = super().get_context_data(**kwargs)

        slug = self.kwargs.get("slug", "demo-project")

        demo_project, _ = Project.objects.get_or_create(
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
        slug = self.kwargs.get("slug", "demo-project")

        project = Project.objects.get(slug=slug)

        new_status = request.POST.get("new_status")

        if new_status in ["draft", "active", "archived"]:
            project.status = new_status
            project.is_public = new_status == "active"
            project.save()

        return redirect("context_menu_demo", slug=slug)
