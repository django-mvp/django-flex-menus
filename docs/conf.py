import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve(strict=True).parent.parent

sys.path.insert(0, str(BASE_DIR))

from fairdm_docs.conf import *

# autodoc2 ships with the docs toolchain but is not one of the extensions it
# enables, so every autodoc2_* setting below was inert and docs/api/ was never
# written — which is what left index.md's toctree pointing at a page that did
# not exist.
extensions = [*extensions, "autodoc2"]

autodoc2_packages = ["../flex_menu"]
autodoc2_render_plugin = "myst"  # or "rst"
autodoc2_output_dir = "api"
html_logo = None
html_favicon = None
html_theme_options["path_to_docs"] = "docs"
html_theme_options["home_page_in_toc"] = False

autodoc2_parse_docstrings = True
autodoc2_docstring_parser_regexes = [("myst", r".*choices*")]

# adr/ and agents/ live under docs/ for portability — a decision record and the
# repo's own conventions have to be readable from a checkout without fetching
# anything. Neither is a page of the published site: the site says what is true
# now, while a decision record is an append-only history that is superseded but
# never rewritten. Left in, Sphinx builds them and then warns that nothing links
# to them.
exclude_patterns = [*exclude_patterns, "adr/**", "agents/**"]
