# File to build the SML parser using tree-sitter

# build_sml.py
from tree_sitter import Language

# Build the parser for Windows
Language.build_library(
    # Output path for the DLL
    'build/sml.dll',

    # List of paths to your language grammar repos
    [
        'tree-sitter-sml'
    ]
)