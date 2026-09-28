# Custom Renderers

Build custom renderers to control menu HTML output.

## Renderer Basics

Renderers transform processed menu items into HTML. They define:

- **Templates** - Which template to use for each item
- **Context** - What data to pass to templates
- **Media** - CSS/JS files to include

## Creating a Renderer

Extend `BaseRenderer`:

```python
from flex_menu.renderers import BaseRenderer

class MyRenderer(BaseRenderer):
    """Custom renderer for my app."""
    
    templates = {
        0: {"default": "menus/container.html"},
        1: {
            "parent": "menus/dropdown.html",
            "leaf": "menus/link.html",
        },
        "default": {
            "parent": "menus/nested_dropdown.html",
            "leaf": "menus/nested_link.html",
        },
    }
```

**Template structure:**

- Keys are depth levels (0, 1, 2, ...) or `"default"`
- Values are dicts with `"parent"`, `"leaf"`, or `"default"` keys
- `"parent"` = items with children
- `"leaf"` = items without children
- `"default"` = fallback for both types

## Depth-based Templates

Different templates for different nesting levels:

```python
templates = {
    # Container (top-level menu)
    0: {"default": "menus/nav.html"},
    
    # First level items
    1: {
        "parent": "menus/dropdown.html",      # Has children
        "leaf": "menus/nav_link.html",        # No children
    },
    
    # Second level items
    2: {
        "parent": "menus/submenu.html",
        "leaf": "menus/submenu_link.html",
    },
    
    # Deeper levels (fallback)
    "default": {
        "parent": "menus/deep_parent.html",
        "leaf": "menus/deep_link.html",
    },
}
```

## Adding Media

Include CSS and JavaScript:

```python
class MyRenderer(BaseRenderer):
    templates = {
        # ... templates ...
    }
    
    class Media:
        css = {
            'all': ('menus/styles.css',)
        }
        js = ('menus/scripts.js',)
```

## Custom Context Data

Override `get_context_data()` to add custom template variables:

```python
class MyRenderer(BaseRenderer):
    templates = {
        # ... templates ...
    }
    
    def get_context_data(self, item, **kwargs):
        """Add custom context for templates."""
        context = super().get_context_data(item, **kwargs)
        
        # Add custom data
        context['custom_class'] = self.get_item_class(item)
        context['icon'] = item.extra_context.get('icon')
        
        return context
    
    def get_item_class(self, item):
        """Generate CSS class for item."""
        classes = ['menu-item']
        if item.selected:
            classes.append('active')
        if item.has_children:
            classes.append('has-dropdown')
        return ' '.join(classes)
```

## Handling Special Cases

Override `get_template()` for special item types:

```python
class MyRenderer(BaseRenderer):
    templates = {
        # ... templates ...
    }
    
    def get_template(self, item):
        """Select template based on item properties."""
        # Check for divider
        if item.extra_context.get('divider'):
            return "menus/divider.html"
        
        # Check for special items
        if item.extra_context.get('heading'):
            return "menus/heading.html"
        
        # Default behavior
        return super().get_template(item)
```

## Complete Example

Tailwind CSS renderer:

```python
from flex_menu.renderers import BaseRenderer

class TailwindRenderer(BaseRenderer):
    """Tailwind CSS menu renderer."""
    
    templates = {
        0: {"default": "menus/tailwind/container.html"},
        1: {
            "parent": "menus/tailwind/dropdown.html",
            "leaf": "menus/tailwind/nav_link.html",
        },
        "default": {
            "parent": "menus/tailwind/nested_dropdown.html",
            "leaf": "menus/tailwind/nested_link.html",
        },
    }
    
    class Media:
        css = {
            'all': ('https://cdn.tailwindcss.com',)
        }
    
    def get_context_data(self, item, **kwargs):
        """Add Tailwind-specific context."""
        context = super().get_context_data(item, **kwargs)
        
        # Add CSS classes
        context['item_classes'] = self.get_item_classes(item)
        context['link_classes'] = self.get_link_classes(item)
        
        return context
    
    def get_item_classes(self, item):
        """Generate Tailwind classes for list item."""
        classes = ['relative']
        
        if item.has_children:
            classes.append('group')
        
        return ' '.join(classes)
    
    def get_link_classes(self, item):
        """Generate Tailwind classes for link."""
        classes = [
            'block', 'px-4', 'py-2',
            'text-gray-700', 'hover:bg-gray-100',
        ]
        
        if item.selected:
            classes.extend(['bg-blue-50', 'text-blue-600'])
        
        return ' '.join(classes)
```

## Template Examples

**Container template** (`menus/tailwind/container.html`):

```django
<nav class="bg-white shadow">
    <ul class="flex space-x-4">
        {% for child in item.visible_children %}
            {% render_item child renderer=renderer %}
        {% endfor %}
    </ul>
</nav>
```

**Link template** (`menus/tailwind/nav_link.html`):

```django
<li class="{{ item_classes }}">
    <a href="{{ item.url }}" class="{{ link_classes }}">
        {{ item.name }}
    </a>
</li>
```

**Dropdown template** (`menus/tailwind/dropdown.html`):

```django
<li class="{{ item_classes }}">
    <button class="{{ link_classes }} flex items-center">
        {{ item.name }}
        <svg class="w-4 h-4 ml-1"><!-- dropdown icon --></svg>
    </button>
    
    <ul class="absolute hidden group-hover:block bg-white shadow-lg">
        {% for child in item.visible_children %}
            {% render_item child renderer=renderer %}
        {% endfor %}
    </ul>
</li>
```

## Registering Your Renderer

Add to `settings.py`:

```python
FLEX_MENUS = {
    "renderers": {
        "tailwind": "myapp.renderers.TailwindRenderer",
        "bootstrap5": "myproject.renderers.Bootstrap5NavbarRenderer",
    },
}
```

Use in templates:

```django
{% render_menu 'main_nav' renderer='tailwind' %}
{% render_menu 'main_nav' renderer='tailwind' %}
```

## Error Handling

Raise errors for unsupported depths:

```python
class SimpleRenderer(BaseRenderer):
    """Renderer that only supports 2 levels."""
    
    templates = {
        0: {"default": "menus/container.html"},
        1: {"parent": "menus/dropdown.html", "leaf": "menus/link.html"},
    }
    
    def get_template(self, item):
        """Only allow up to depth 1."""
        if item.depth > 1:
            raise ValueError(
                f"SimpleRenderer only supports up to 2 nesting levels. "
                f"Item '{item.name}' is at depth {item.depth}."
            )
        return super().get_template(item)
```

## Advanced: Renderer Instance

Access the renderer instance in templates via `{{ renderer }}`:

```python
class MyRenderer(BaseRenderer):
    templates = {
        # ... templates ...
    }
    
    def get_dropdown_id(self, item):
        """Generate unique ID for dropdown."""
        return f"dropdown-{item.name}"
    
    def get_context_data(self, item, **kwargs):
        context = super().get_context_data(item, **kwargs)
        context['renderer'] = self  # Make renderer available
        return context
```

In template:

```django
<li>
    <button data-target="#{{ renderer.get_dropdown_id(item) }}">
        {{ item.name }}
    </button>
    <ul id="{{ renderer.get_dropdown_id(item) }}">
        <!-- children -->
    </ul>
</li>
```

## Best Practices

1. **Inherit from BaseRenderer** - Don't start from scratch
2. **Use depth-based templates** - Define clear structure for each level
3. **Provide Media** - Include necessary CSS/JS
4. **Override minimally** - Only override what you need to customize
5. **Document depth limits** - Make clear how many levels are supported
6. **Test thoroughly** - Test with different menu structures
7. **Use extra_context** - Support custom item attributes
8. **Keep templates simple** - Move logic to renderer methods
