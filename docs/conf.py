import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve(strict=True).parent.parent

sys.path.insert(0, str(BASE_DIR))

from fairdm_docs.conf import *

autodoc2_packages = ["../flex_menu"]
autodoc2_render_plugin = "myst"  # or "rst"
autodoc2_output_dir = "api"
html_logo = None
html_favicon = None
html_theme_options["path_to_docs"] = "docs"
html_theme_options["home_page_in_toc"] = False

autodoc2_parse_docstrings = True
autodoc2_docstring_parser_regexes = [("myst", r".*choices*")]
