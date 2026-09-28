"""Docutils parser that renders Google-style docstrings for sphinx-autodoc2."""

from docutils.parsers.rst import Parser as RstParser
from sphinx.ext.napoleon import Config, GoogleDocstring

_CONFIG = Config(
    napoleon_use_param=True, napoleon_use_rtype=False, napoleon_use_ivar=True
)


class Parser(RstParser):
    """Convert Google sections to reStructuredText, then parse the result.

    autodoc2 has no Napoleon support of its own and loads a docstring parser by
    module name, which is why this module exposes a class called ``Parser``.
    """

    def parse(self, inputstring, document):
        """Parse the docstring after Napoleon has rewritten its sections."""
        super().parse(str(GoogleDocstring(inputstring, _CONFIG)), document)
