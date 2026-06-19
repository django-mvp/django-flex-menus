# django-flex-menus

Domain model for the django-flex-menus library — a tree-based menu management system for Django.

## Core Concepts

**Menu**:
A complete, named menu tree. Defined once in code (e.g., `menus.py`) and later referenced by name in templates via `{% render_menu "main_nav" renderer="bootstrap5" %}`. A Menu is a convenience class that automatically attaches itself to the global root node, making it discoverable by name.
_Avoid_: menu tree, navigation, navbar

**Item**:
A leaf node in a Menu tree. An Item is one of three kinds: Link, Action, or Decoration. An Item cannot have children — if it has children, it is a Group, not an Item.
_Avoid_: MenuItem (implementation term), nav item, link, button

**Link**:
An Item with a URL that produces an `<a>` tag with an `href` attribute. Can be **static** (URL string defined at startup) or **dynamic** (Route resolved at processing time using Django's URL resolver). Use when the item navigates somewhere.
_Avoid_: anchor, href, clickable, button

**Group**:
Any parent node in a Menu tree. Implicit — not a class users instantiate directly. Any Item with children is conceptually a Group. Never produces an `<a>` tag itself — only its descendants do.
_Avoid_: container, parent, folder, section

**Action**:
An Item with no URL and no children that performs an action without navigating (e.g., opens a modal). The Renderer decides what HTML to produce.
_Avoid_: button, command, event

**Decoration**:
An Item with no URL and no children used for visual structure (e.g., dividers, headers). Has no interactive behavior.
_Avoid_: separator, spacer, element, component

**URL**:
A fixed destination string attached to a Link. Resolved at definition time. Can point to an internal path or an external resource. Use when the link never changes.
_Avoid_: static link, hardcoded URL

**Route**:
A Django named URL pattern attached to a Link via `view_name`. Resolved at render time using kwargs passed through the template tag. Enables parameterized links (e.g., resolving `/projects/42/` from `view_name="project-detail"` and `pk=42`). Use when the link depends on request context.
_Avoid_: view name, reverse URL, dynamic URL

**Renderer**:
A component that transforms processed Items into HTML. Renderers define which templates to use at each depth level, what context data to pass, and what CSS/JS media to include. Renderers are configured by name in settings and referenced by name in templates.
_Avoid_: template, view, serializer, formatter

**Check**:
A visibility predicate attached to an Item or Group. It can be a boolean or a callable that receives `(request, **kwargs)` and returns True/False. Intentionally neutral — it can express authorization, subscription tier, time of day, A/B test bucket, or any other condition.
_Avoid_: permission, filter, rule, policy

**Per-Item Context**:
Static data attached to an Item that flows into the Renderer's template. The meaning of each key is determined by the Renderer — it could be badge styling, icon names, labels, or anything else. Defined once in menus.py and never changes at runtime.
_Avoid_: extra_context, metadata, payload, attributes

**Renderer Context**:
Dynamic data passed to `{% render_menu %}` via template tag kwargs. Flows through two paths: Check functions (for visibility decisions) and Route resolution (for URL parameters). Also unpacked into the Renderer's template context.
_Avoid_: kwargs, template variables, arguments

## Renderer Concepts

**Depth**:
The nesting level of an Item in a Menu tree. Depth 0 = top-level Items, depth 1 = first nesting level, etc. Used by Renderers to select appropriate templates per nesting level.
_Avoid_: level, tier, hierarchy, indentation

## Lifecycle States

**Visible**:
An Item or Group is visible when its Check returns True AND its URL resolves successfully (if it has one). Items whose URLs fail to resolve are hidden rather than raising errors.
_Avoid_: invisible, shown, displayed

**Active**:
An Item is active when its resolved URL matches the current request path, or any of its descendants' resolved URLs match. Only Items with a resolvable URL can be active.
_Avoid_: selected, highlighted, current, focused

## Supporting Concepts

**root**:
The global singleton tree root provided by anytree. All Menu instances attach to it automatically. It is an implementation detail — users never reference it directly.
