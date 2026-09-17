# Template Usage

Guide to using django-flex-menus template tags.

## Template Tags

Load the template tag library:

```django
{% load flex_menu %}
```

### render_menu

Render a complete menu by name or instance. Media (CSS/JS) is automatically included.

```django
{% render_menu 'menu_name' renderer='bootstrap5' %}
```

If you are providing a menu as a context variable to your template, you can pass it directly:

```django
{% render_menu menu_object renderer='bootstrap5' %}
```

**Disable media inclusion:**

Sometimes you may want to include CSS/JS manually or only once per page. Disable automatic media inclusion with `include_media=False`:

```django
{% render_menu 'menu_name' renderer='bootstrap5' include_media=False %}
```

**Extra kwargs:**

You can pass any number of keyword arguments to `render_menu`. These arguments are used in two ways:

```django
{% render_menu 'menu_name' renderer='bootstrap5' pk=object.pk project=project user=owner %}
```

Kwargs are handled in the following ways:

1. **Check functions** - **All** kwargs are passed unaltered to `check` functions to enable context-aware visibility decisions.
2. **URL functions** - **All** kwargs are passed unaltered to `url` functions to enable context-aware url resolution.
3. **View resolution** - Only kwargs specific to the specified `view_name` are passed to Django's `reverse()` function for URL resolution.

See [Visibility Checks](visibility-checks.md) and [Dynamic URL Resolution](#dynamic-url-resolution) for details.

## Common Patterns

### Base Template

```django
{% load flex_menu %}
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}My Site{% endblock %}</title>
</head>
<body>
    <header>
        {% render_menu 'main_nav' renderer='navbar' %}
    </header>
    
    <main>
        {% block content %}{% endblock %}
    </main>
    
    <footer>
        {% render_menu 'footer_nav' renderer='simple' %}
    </footer>
</body>
</html>
```

:::{note}
Media (CSS/JS) is automatically included before each menu.
:::

### Multiple Menus

```django
{# Top navigation #}
<nav class="navbar">
    {% render_menu 'top_nav' renderer='navbar' %}
</nav>

{# Sidebar navigation #}
<aside class="sidebar">
    {% render_menu 'sidebar_nav' renderer='sidebar' %}
</aside>

{# Footer links #}
<footer>
    {% render_menu 'footer_nav' renderer='simple' %}
</footer>
```

### Active Item Highlighting

Active items are automatically determined. An item configured with `view_name` is matched against the request's resolved view name, so it stays active for query strings, trailing-slash variants, other objects served by the same view, and translated URLs. An item configured with a literal `url` or a callable has no resolved view to compare against, so it falls back to comparing its URL to `request.path`, ignoring any query string, fragment and trailing slash. When an item matches, its `selected` property is set to `True`.

Renderers typically add CSS classes like `active` or `selected` to items where `item.selected` is `True`.

### Context-Aware Menus

Pass context variables to control visibility based on database objects:

```django
{# In a project detail view #}
<div class="project-header">
    <h1>{{ project.name }}</h1>
    {% render_menu 'project_actions' renderer='bootstrap5' project=project %}
</div>
```

```python
# Menu definition with context-aware checks
from flex_menu import Menu, MenuItem

def can_edit_project(request, project=None, **kwargs):
    if not project or not request.user.is_authenticated:
        return False
    return project.owner == request.user

Menu(
    name="project_actions",
    children=[
        MenuItem(name="view", view_name="project_detail"),
        MenuItem(name="edit", view_name="project_edit", check=can_edit_project),
        MenuItem(name="delete", view_name="project_delete", check=can_edit_project),
    ],
)
```

See [Context-Aware Checks](visibility-checks.md) for more examples.

(dynamic-url-resolution)=
### Dynamic URL Resolution

Context parameters are also used for URL resolution, allowing menu items to adapt URLs based on the current view context.

**Automatic Parameter Filtering for view_name**

When using `view_name`, django-flex-menus automatically filters kwargs to only include parameters that the URL pattern actually requires. This means you can pass extra context without worrying about breaking URL resolution:

```django
{# Pass many kwargs - only 'pk' will be used for URL resolution #}
{% render_menu 'post_actions' renderer='bootstrap5' pk=post.pk project=project user=user %}
```

```python
# URL patterns
urlpatterns = [
    path('posts/<int:pk>/edit/', views.edit_post, name='post_edit'),
    path('posts/<int:pk>/delete/', views.delete_post, name='post_delete'),
]

# Menu definition - URLs are resolved using only the pk parameter
Menu(
    name="post_actions",
    children=[
        MenuItem(name="edit", view_name="post_edit"),  # Becomes /posts/123/edit/
        MenuItem(name="delete", view_name="post_delete"),  # Becomes /posts/123/delete/
    ],
)
```

**How Parameter Filtering Works:**

1. Django-flex-menus inspects each URL pattern to determine required parameters
2. Only matching parameters from kwargs are passed to `reverse()`
3. All other parameters are still available to check functions
4. If a required parameter is missing, the URL resolution fails gracefully

**With callable URLs:**

Callable URLs receive all kwargs, allowing full flexibility:

```python
def comment_url(request, comment_id=None, **kwargs):
    """Generate URL for a specific comment."""
    # All kwargs are available here
    post_pk = kwargs.get('pk', request.resolver_match.kwargs.get('pk'))
    return f"/posts/{post_pk}/comments/{comment_id}/"

Menu(
    name="comment_actions",
    children=[
        MenuItem(name="edit_comment", url=comment_url),
    ],
)
```

**Practical Examples:**

```python
# Complex menu with different URL parameter requirements
Menu(
    name="admin_actions",
    children=[
        # Needs 'pk' parameter
        MenuItem(name="view_user", view_name="user_detail", check=user_is_staff),
        # Needs 'pk' parameter  
        MenuItem(name="edit_user", view_name="user_edit", check=user_is_superuser),
        # No parameters needed
        MenuItem(name="user_list", view_name="user_list", check=user_is_staff),
        # Custom check using multiple context vars
        MenuItem(
            name="delete_user", 
            view_name="user_delete",
            check=lambda request, user_obj=None, **kwargs: (
                request.user.is_superuser and 
                user_obj and 
                user_obj != request.user
            )
        ),
    ],
)
```

```django
{# Template: Pass all context - each URL gets only what it needs #}
{% render_menu 'admin_actions' renderer='bootstrap5' pk=user.pk user_obj=user current_user=request.user %}
```

In this example:
- `user_detail` and `user_edit` and `user_delete` get `pk=user.pk` for URL resolution
- `user_list` gets no parameters (doesn't need any)
- All check functions receive all kwargs: `pk`, `user_obj`, and `current_user`
- The delete check can use both `user_obj` and `current_user` for complex logic

```django
{% render_menu 'comment_actions' renderer='simple' comment_id=comment.id %}
```

**Combined visibility and URL resolution:**

```python
def can_edit_project(request, project=None, **kwargs):
    if not project:
        return False
    return project.owner == request.user

Menu(
    name="project_menu",
    children=[
        # Same 'project' param used for both check and URL resolution
        MenuItem(
            name="edit",
            view_name="project_edit",  # Resolves to /projects/{project.pk}/edit/
            check=can_edit_project,  # Receives project for visibility check
        ),
    ],
)
```

```django
{% render_menu 'project_menu' renderer='bootstrap5' project=project pk=project.pk %}
```

:::{important}
If you pass kwargs that aren't needed by a URL pattern, Django's `reverse()` will fail and that menu item will become **invisible** (not throw an error). This allows you to pass multiple context variables where different items use different subsets:
:::

```python
Menu(
    name="actions",
    children=[
        MenuItem(name="list", view_name="posts"),           # No kwargs needed
        MenuItem(name="detail", view_name="post_detail"),   # Uses 'pk'  
        MenuItem(name="edit", view_name="post_edit"),       # Uses 'pk'
    ],
)
```

```django
{# Pass pk - 'list' item stays visible (no view_name kwargs), 
   'detail' and 'edit' get pk for URL resolution #}
{% render_menu 'actions' renderer='simple' pk=post.pk %}
```

### Custom Rendering

For complete control, process the menu and render manually:

```django
{% process_menu 'main_nav' as menu %}

<ul class="custom-menu">
{% for item in menu.visible_children %}
    <li class="{% if item.selected %}active{% endif %}">
        {% if item.has_url %}
            <a href="{{ item.url }}">{{ item.name }}</a>
        {% else %}
            <span>{{ item.name }}</span>
        {% endif %}
        
        {% if item.visible_children %}
            <ul class="submenu">
            {% for child in item.visible_children %}
                <li><a href="{{ child.url }}">{{ child.name }}</a></li>
            {% endfor %}
            </ul>
        {% endif %}
    </li>
{% endfor %}
</ul>
```

## Processed Menu Properties

After `process_menu`, items have these properties:

**Navigation:**
- `visible_children` - List of visible child items
- `parent` - Parent MenuItem
- `depth` - Depth in tree (0, 1, 2, ...)

**State:**
- `visible` - Whether item passed visibility checks
- `selected` - Whether item matches selection path
- `url` - Resolved URL (or None)

**Type checks:**
- `has_url` - Has a resolvable URL
- `has_children` - Has child items
- `is_leaf` - No children
- `is_parent` - Has children
- `is_clickable` - Has resolvable URL

**Data:**
- `name` - Unique identifier
- `extra_context` - Dict of custom data

## Caching

Processed menus are cached per request to avoid redundant processing:

```django
{# First call: processes menu #}
{% render_menu 'main_nav' %}

{# Second call: uses cached result #}
{% render_menu 'main_nav' %}
```

Cache is request-scoped and thread-safe.

## Renderer Selection

Renderers must be specified in the template tag:

```django
{% render_menu 'nav' renderer='navbar' %}
```

If no renderer is specified, the tag will raise an error.

Configure available renderers in `settings.py`:

```python
FLEX_MENUS = {
    "renderers": {
        "bootstrap5": "flex_menu.renderers.Bootstrap5NavbarRenderer",
        "sidebar": "flex_menu.renderers.Bootstrap5SidebarRenderer",
        "simple": "flex_menu.renderers.SimpleHTMLRenderer",
    },
}
```

## Error Handling

If a menu doesn't exist, `render_menu` raises `TemplateSyntaxError`:

```django
{% render_menu 'nonexistent' %}
{# Raises: Menu 'nonexistent' does not exist #}
```

To handle gracefully:

```django
{% process_menu 'optional_menu' as menu %}
{% if menu %}
    {% render_item menu %}
{% endif %}
```

## Best Practices

1. **Load once** - Load `{% load flex_menu %}` at the top of your template
2. **Specify renderers** - Always include renderer names in `render_menu` tags
3. **Named renderers** - Configure renderers in settings, reference by name
4. **Process when needed** - Use `process_menu` only for custom rendering logic
