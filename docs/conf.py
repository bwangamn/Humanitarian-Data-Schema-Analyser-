import os
import sys

# Insert the ``src`` directory so autodoc can locate the installed package layout.
sys.path.insert(0, os.path.abspath('../src'))

# -- Project information -----------------------------------------------------
project = 'Humanitarian Data Schema Analyser'
copyright = '2026, Humanitarian Data Schema Analyser Team'
author = 'Humanitarian Data Schema Analyser Team'
release = '0.2.1'

# -- General configuration ---------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.githubpages',
    'myst_parser',
]

templates_path = ['_templates']
exclude_patterns = [
    '_build',
    'Thumbs.db',
    '.DS_Store',
    'evaluation/evaluation_plan.md',
    'figures/README.md',
    'report/report_draft.md',
]

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
html_theme = 'sphinx_rtd_theme'

html_static_path = ['_static']
html_title = 'Humanitarian Data Schema Analyser Documentation'
