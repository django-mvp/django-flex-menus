# Menu Serialization

Menu serialization allows you to convert processed menu objects into JSON format for use with JavaScript frameworks like Alpine.js, Vue.js, React, or for building REST APIs.

## Overview

Django Flex Menus now supports serializing menu structures to JSON, enabling you to:

- Create responsive menus that adapt to different screen sizes using JavaScript
- Build Single Page Applications (SPAs) with menu data from Django
- Expose menu structures via REST APIs
- Use frontend frameworks like Alpine.js, Vue, or React
- Implement client-side filtering and manipulation of menus

## Quick Start

### In Templates (Alpine.js Example)

```django
{% load flex_menu %}

<div x-data='{% menu_json "main_navigation" %}' class="menu">
  <template x-for="item in children" :key="item.name">
    <a :href="item.url" 
       x-show="item.visible"
       :class="{ 'active': item.selected }"
       x-text="item.extra_context.label">
    </a>
  </template>
</div>
```

### In Python Views (API Example)

```python
from flex_menu import root, serialize_menu
from django.http import JsonResponse
import json

def menu_api_view(request):
    # Get and process the menu
    menu = root.get('main_navigation')
    processed = menu.process(request)
    
    # Serialize to JSON string
    json_data = serialize_menu(processed, indent=2)
    
    # Return as API response
    return JsonResponse(json.loads(json_data), safe=False)
```

## API Reference

### MenuItem.to_dict()

Converts a processed menu item into a dictionary.

**Signature:**
```python
def to_dict(self, include_children: bool = True) -> dict
```

**Parameters:**
- `include_children` (bool): Whether to recursively include children. Default is `True`.

**Returns:**
A dictionary with the following structure:
```python
{
    "name": str,                    # Unique identifier
    "url": str | None,              # Resolved URL
    "visible": bool,                # Visibility after checks
    "selected": bool,               # True if URL matches current page
    "depth": int,                   # Depth in menu tree (0 = root)
    "has_children": bool,           # Has child menu items
    "has_visible_children": bool,   # Has visible children after processing
    "is_clickable": bool,           # Has a URL (clickable link)
    "extra_context": dict,          # Custom data from menu definition
    "children": list[dict]          # Child menu items (if include_children=True)
}
```

**Example:**
```python
menu = root.get('main_nav').process(request)
data = menu.to_dict()

# Access properties
print(data['name'])                      # 'main_nav'
print(data['children'][0]['url'])        # '/home/'
print(data['extra_context']['label'])    # 'Main Navigation'
```

### serialize_menu()

Converts a processed menu item to a JSON string.

**Signature:**
```python
def serialize_menu(menu_item, **options) -> str
```

**Parameters:**
- `menu_item`: A processed MenuItem instance (after calling `.process(request)`)
- `include_children` (bool): Whether to include children. Default is `True`.
- `indent` (int | None): JSON indentation for pretty printing. Default is `None`.

**Returns:**
JSON string representation of the menu.

**Example:**
```python
from flex_menu import root, serialize_menu

menu = root.get('main_nav').process(request)

# Compact JSON
json_str = serialize_menu(menu)

# Pretty-printed JSON
json_str = serialize_menu(menu, indent=2)

# Without children
json_str = serialize_menu(menu, include_children=False)
```

### menu_json Template Tag

Template tag for injecting serialized menu data into templates.

**Signature:**
```django
{% menu_json menu_name [include_children=True] [indent=None] [**kwargs] %}
```

**Parameters:**
- `menu_name` (str): Name of the menu to serialize
- `include_children` (bool): Whether to include children. Default is `True`.
- `indent` (int): JSON indentation for pretty printing. Default is `None`.
- `**kwargs`: Context variables passed to check functions and URL resolution

**Returns:**
JSON-safe string for use in templates.

**Examples:**

Basic usage:
```django
{% load flex_menu %}
{% menu_json "main_navigation" %}
```

With indentation for debugging:
```django
<pre>{% menu_json "main_navigation" indent=2 %}</pre>
```

Without children:
```django
{% menu_json "main_navigation" include_children=False %}
```

Passing context variables:
```django
{% menu_json "project_menu" project=project slug=project.slug %}
```

## Use Cases

### 1. Alpine.js Responsive Menu

Create a menu that collapses on mobile:

```django
{% load flex_menu %}

<div x-data='{
  menuData: {% menu_json "main_navigation" %},
  mobileOpen: false
}'>
  <!-- Mobile toggle button -->
  <button @click="mobileOpen = !mobileOpen" class="md:hidden">
    Menu
  </button>
  
  <!-- Menu -->
  <nav :class="{ 'hidden': !mobileOpen }" class="md:block">
    <template x-for="item in menuData.children" :key="item.name">
      <a :href="item.url" 
         x-show="item.visible"
         :class="{ 'active': item.selected }"
         x-text="item.extra_context.label">
      </a>
    </template>
  </nav>
</div>
```

### 2. Vue.js Menu Component

```django
{% load flex_menu %}

<div id="app">
  <navigation-menu :menu-data='{% menu_json "main_navigation" %}'></navigation-menu>
</div>

<script>
const app = Vue.createApp({
  components: {
    'navigation-menu': {
      props: ['menuData'],
      template: `
        <nav>
          <a v-for="item in menuData.children"
             :key="item.name"
             :href="item.url"
             v-show="item.visible"
             :class="{ active: item.selected }">
            {{ item.extra_context.label }}
          </a>
        </nav>
      `
    }
  }
});
app.mount('#app');
</script>
```

### 3. REST API Endpoint

Create an API endpoint that returns menu structure:

```python
from django.http import JsonResponse
from flex_menu import root, serialize_menu
import json

def menu_api(request):
    """API endpoint for menu data."""
    menu_name = request.GET.get('menu', 'main_navigation')
    
    # Get menu
    menu = root.get(menu_name)
    if not menu:
        return JsonResponse({'error': 'Menu not found'}, status=404)
    
    # Process for current request
    processed = menu.process(request)
    
    # Serialize
    json_str = serialize_menu(processed)
    
    return JsonResponse(json.loads(json_str), safe=False)
```

### 4. Search/Filter Menus

Enable client-side menu searching:

```django
{% load flex_menu %}

<div x-data='{
  menuData: {% menu_json "main_navigation" %},
  search: "",
  get filteredItems() {
    if (!this.search) return this.menuData.children;
    return this.menuData.children.filter(item =>
      item.extra_context.label.toLowerCase().includes(this.search.toLowerCase())
    );
  }
}'>
  <input type="search" 
         x-model="search" 
         placeholder="Search menu...">
  
  <nav>
    <template x-for="item in filteredItems" :key="item.name">
      <a :href="item.url" x-text="item.extra_context.label"></a>
    </template>
  </nav>
</div>
```

## Properties Reference

Each serialized menu item contains these properties:

| Property | Type | Description |
|----------|------|-------------|
| `name` | `str` | Unique identifier for the menu item |
| `url` | `str \| None` | Resolved URL, or `None` if not a link |
| `visible` | `bool` | Whether the item passed visibility checks |
| `selected` | `bool` | Whether the item's URL matches current page |
| `depth` | `int` | Depth in the tree (0 = root, 1 = top-level, etc.) |
| `has_children` | `bool` | Whether the item has child menu items |
| `has_visible_children` | `bool` | Whether the item has visible children |
| `is_clickable` | `bool` | Whether the item has a URL (is a link) |
| `extra_context` | `dict` | Custom data from menu definition |
| `children` | `list[dict]` | Array of child menu items |

### Extra Context

The `extra_context` dictionary contains all custom data you provide when creating menu items:

```python
MenuItem(
    name="home",
    url="/",
    extra_context={
        "label": "Home",
        "icon": "fas fa-home",
        "badge": "New",
        "description": "Go to homepage",
        # ... any custom data
    }
)
```

All of this data is preserved in the serialized output:

```json
{
  "name": "home",
  "url": "/",
  "extra_context": {
    "label": "Home",
    "icon": "fas fa-home",
    "badge": "New",
    "description": "Go to homepage"
  }
}
```

## Best Practices

### 1. Process Before Serializing

Always process the menu with a request before serializing:

```python
# ✅ Correct
menu = root.get('main_nav')
processed = menu.process(request)
data = serialize_menu(processed)

# ❌ Wrong - unprocessed menu
menu = root.get('main_nav')
data = serialize_menu(menu)  # Missing visibility/URL resolution
```

### 2. Deep Copy Protection

The serialization uses `copy.deepcopy()` on `extra_context` to prevent mutations:

```python
processed = menu.process(request)
data = processed.to_dict()

# Safe - modifications won't affect the original
data['extra_context']['label'] = 'Modified'
# Original menu item is unchanged
```

### 3. Context Variables

Pass context variables for dynamic menus:

```django
{# Good - passes context for conditional visibility #}
{% menu_json "project_menu" project=project %}

{# Bad - menu won't have context for checks #}
{% menu_json "project_menu" %}
```

### 4. Use Indent for Debugging

Use the `indent` parameter when debugging:

```django
{# Development - pretty print for readability #}
<pre>{% menu_json "main_nav" indent=2 %}</pre>

{# Production - compact for efficiency #}
<div x-data='{% menu_json "main_nav" %}'></div>
```

## Backward Compatibility

Serialization is fully backward compatible:

- All existing rendering methods continue to work unchanged
- You can use both serialization and traditional rendering in the same project
- No changes required to existing code
- New functionality is purely additive

## Performance Considerations

- Menu processing is cached per request (via `process_menu`)
- Serialization is lightweight (no additional database queries)
- Deep copy of `extra_context` has minimal overhead for typical data
- Consider caching serialized JSON for frequently-used, static menus

## Complete Example

Here's a complete example showing a responsive menu with Alpine.js:

```django
{% load flex_menu %}
<!DOCTYPE html>
<html>
<head>
  <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
  <style>
    .menu-item { padding: 10px; }
    .menu-item.selected { background: #007bff; color: white; }
    .nested { margin-left: 20px; }
  </style>
</head>
<body>
  <div x-data='{% menu_json "main_navigation" %}'>
    <!-- Top-level items -->
    <template x-for="item in children" :key="item.name">
      <div x-show="item.visible">
        <a :href="item.url" 
           class="menu-item"
           :class="{ selected: item.selected }">
          <span x-show="item.extra_context.icon" 
                :class="item.extra_context.icon"></span>
          <span x-text="item.extra_context.label"></span>
          <span x-show="item.has_visible_children"
                x-text="'(' + item.children.length + ')'"></span>
        </a>
        
        <!-- Nested children -->
        <template x-if="item.has_visible_children">
          <div class="nested">
            <template x-for="child in item.children" :key="child.name">
              <a :href="child.url" 
                 x-show="child.visible"
                 class="menu-item"
                 :class="{ selected: child.selected }"
                 x-text="child.extra_context.label">
              </a>
            </template>
          </div>
        </template>
      </div>
    </template>
  </div>
</body>
</html>
```

## See Also

- [Building Menus](building-menus.md) - Creating menu structures
- [Template Usage](template-usage.md) - Traditional rendering
- [Visibility Checks](visibility-checks.md) - Controlling menu visibility
- [Custom Renderers](custom-renderers.md) - Server-side rendering
