import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve(strict=True).parent.parent

sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "docs"))

from fairdm_docs.conf import *

# The shared docs configuration ships autodoc2 without enabling it.
extensions = [*extensions, "autodoc2"]

autodoc2_packages = ["../flex_menu"]
autodoc2_render_plugin = "myst"
autodoc2_output_dir = "api"
html_logo = None
html_favicon = None
html_theme_options["path_to_docs"] = "docs"
html_theme_options["home_page_in_toc"] = False

autodoc2_parse_docstrings = True
autodoc2_docstring_parser_regexes = [(r".*", "google_docstrings")]

# adr/ and agents/ must be readable from a checkout, but neither is a page of the
# published site, which describes what is true now rather than decision history.
exclude_patterns = [*exclude_patterns, "adr/**", "agents/**"]
