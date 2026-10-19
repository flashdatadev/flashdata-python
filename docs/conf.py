"""Build the SDK documentation locally without credentials or network calls."""

from flashdata import __version__

project = "FlashData Python"
author = "FlashData"
copyright = "2026, FlashData"
release = __version__
extensions = ["myst_parser", "sphinx.ext.autodoc"]
source_suffix = {".md": "markdown", ".rst": "restructuredtext"}
root_doc = "index"
exclude_patterns = ["_build"]
myst_enable_extensions = ["colon_fence"]
myst_heading_anchors = 3
autodoc_typehints = "none"
autodoc_member_order = "bysource"
html_theme = "sphinx_rtd_theme"
html_title = "FlashData Python SDK"
html_static_path = ["_static"]
html_css_files = ["custom.css"]
html_theme_options = {"collapse_navigation": False, "navigation_depth": 3, "style_nav_header_background": "#142622"}
