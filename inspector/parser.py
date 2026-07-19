"""Parser interface and registry.

All parsers inherit from BaseParser and register themselves
with the ParserRegistry for automatic discovery.
"""
from abc import ABC, abstractmethod
from .models import Artifact


class BaseParser(ABC):
    """Abstract base for all artifact parsers."""

    @abstractmethod
    def can_parse(self, path: str) -> bool:
        """Return True if this parser can handle the given file."""
        ...

    @abstractmethod
    def parse(self, path: str) -> Artifact:
        """Parse file and return an Artifact object."""
        ...

    @abstractmethod
    def name(self) -> str:
        """Human-readable parser name."""
        ...


class ParserRegistry:
    """Global parser registry with automatic discovery."""

    def __init__(self):
        self._parsers: list[BaseParser] = []

    def register(self, parser: BaseParser):
        self._parsers.append(parser)

    def find(self, path: str) -> BaseParser | None:
        for p in self._parsers:
            if p.can_parse(path):
                return p
        return None

    def parse(self, path: str) -> Artifact | None:
        parser = self.find(path)
        if parser:
            return parser.parse(path)
        return None

    def list_parsers(self) -> list[dict]:
        return [{"name": p.name(), "class": p.__class__.__name__}
                for p in self._parsers]


# Global registry instance
registry = ParserRegistry()


def register(parser_cls):
    """Decorator to auto-register a parser."""
    instance = parser_cls()
    registry.register(instance)
    return parser_cls
