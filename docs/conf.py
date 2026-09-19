import os
import sys

# Insert project root directory into Python path so autodoc can locate packages
sys.path.insert(0, os.path.abspath('..'))

# -- Project information -----------------------------------------------------
project = 'Humanitarian Data Schema Analyser'
copyright = '2026, Humanitarian Data Schema Analyser Team'
author = 'Humanitarian Data Schema Analyser Team'
release = '1.0.0'

# -- General configuration ---------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.githubpages',
]

try:
    import myst_parser
    extensions.append('myst_parser')
except ImportError:
    pass

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# Docstring configuration
napoleon_google_docstring = True
napoleon_numpy_docstring = True
autodoc_member_order = 'bysource'
autodoc_default_options = {
    'members': True,
    'undoc-members': True,
    'show-inheritance': True,
}

# Source suffix
source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}

# -- Options for HTML output -------------------------------------------------
try:
    import sphinx_rtd_theme
    html_theme = 'sphinx_rtd_theme'
except ImportError:
    html_theme = 'alabaster'

html_static_path = ['_static']
html_title = 'Humanitarian Data Schema Analyser Documentation'

