"""
Example menu definitions using the unified MenuItem class.

This demonstrates how a single menu structure can be rendered
multiple ways using different renderers.
"""

from django.urls import reverse

from flex_menu import Menu, MenuItem

# ============================================================================
# Main Navigation Menu
# ============================================================================
# Define menu structure ONCE
# This same structure will be rendered as both navbar and sidebar
main_navigation = MenuItem(
    "main_navigation",
    extra_context={"label": "Main Navigation"},
    children=[
        MenuItem(
            "home",
            view_name="home",
            extra_context={"label": "Home", "icon": "fas fa-home"},
        ),
        MenuItem(
            "about",
            view_name="about",
            extra_context={"label": "About", "icon": "fas fa-info-circle"},
        ),
        MenuItem(
            "services",
            extra_context={"label": "Services", "icon": "fas fa-cogs"},
            children=[
                MenuItem(
                    "web_design",
                    view_name="web_design",
                    extra_context={
                        "label": "Web Design",
                        "icon": "fas fa-palette",
                    },
                ),
                MenuItem(
                    "development",
                    view_name="development",
                    extra_context={
                        "label": "Development",
                        "icon": "fas fa-code",
                    },
                ),
                MenuItem("divider_1", extra_context={"divider": True}),
                MenuItem(
                    "consulting",
                    view_name="consulting",
                    extra_context={
                        "label": "Consulting",
                        "icon": "fas fa-handshake",
                    },
                ),
            ],
        ),
        MenuItem(
            "contact",
            view_name="contact",
            extra_context={"label": "Contact", "icon": "fas fa-envelope"},
        ),
        MenuItem(
            "context_demo",
            url=lambda request: reverse("context_menu_demo", kwargs={"slug": "demo-project"}),
            extra_context={
                "label": "Context Menus Demo",
                "icon": "fas fa-flask",
            },
        ),
    ],
)


# ============================================================================
# Context-Specific Menus for Database Objects
# ============================================================================


def check_project_status(request, project=None, status=None, **kwargs):
    """Check if project has specific status."""
    if not project:
        return False
    return project.status == status


def check_project_public(request, project=None, **kwargs):
    """Check if project is public."""
    if not project:
        return False
    return project.is_public


def check_project_editable(request, project=None, **kwargs):
    """Check if project can be edited (not archived)."""
    if not project:
        return False
    return project.status != "archived"


# Project Actions Menu - Changes based on project state
# Usage: {% render_menu 'project_actions' project=project slug=project.slug renderer='sidebar' %}
project_actions = Menu(
    name="project_actions",
    children=[
        MenuItem(
            "view_project",
            view_name="context_menu_demo",
            extra_context={
                "label": "View Details",
                "icon": "fas fa-eye",
            },
        ),
        MenuItem(
            "edit_project",
            view_name="context_menu_demo",
            check=check_project_editable,
            extra_context={
                "label": "Edit Project",
                "icon": "fas fa-edit",
                "description": "Only visible for non-archived projects",
            },
        ),
        MenuItem(
            "publish_project",
            view_name="context_menu_demo",
            check=lambda request, project=None, **kwargs: project and project.status == "draft",
            extra_context={
                "label": "Publish",
                "icon": "fas fa-rocket",
                "description": "Only visible for draft projects",
            },
        ),
        MenuItem(
            "archive_project",
            view_name="context_menu_demo",
            check=lambda request, project=None, **kwargs: project and project.status == "active",
            extra_context={
                "label": "Archive",
                "icon": "fas fa-archive",
                "description": "Only visible for active projects",
            },
        ),
    ],
)


# Project Status Menu - Dynamic sections based on project state
# Usage: {% render_menu 'project_status_menu' project=project %}
project_status_menu = Menu(
    name="project_status_menu",
    children=[
        MenuItem(
            "draft_section",
            check=lambda request, project=None, **kwargs: project and project.status == "draft",
            extra_context={
                "label": "Draft Actions",
                "is_header": True,
            },
            children=[
                MenuItem(
                    "save_draft",
                    url="/fake/save/",
                    extra_context={"label": "Save Draft", "icon": "fas fa-save"},
                ),
                MenuItem(
                    "preview_draft",
                    url="/fake/preview/",
                    extra_context={"label": "Preview", "icon": "fas fa-eye"},
                ),
            ],
        ),
        MenuItem(
            "active_section",
            check=lambda request, project=None, **kwargs: project and project.status == "active",
            extra_context={
                "label": "Active Project",
                "is_header": True,
            },
            children=[
                MenuItem(
                    "view_stats",
                    url="/fake/stats/",
                    extra_context={
                        "label": "View Statistics",
                        "icon": "fas fa-chart-bar",
                    },
                ),
                MenuItem(
                    "export_data",
                    url="/fake/export/",
                    extra_context={"label": "Export Data", "icon": "fas fa-download"},
                ),
            ],
        ),
    ],
)
