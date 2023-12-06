from dataclasses import dataclass
from pathlib import Path

from .protocols import ComposeFetcher, ComposeReference


@dataclass(frozen=True)
class ODCSResultReference(ComposeReference):
    """
    Reference to a locally-stored compose result
    """
    compose_path: Path


@dataclass(frozen=True)
class ODCSFetcher(ComposeFetcher):
    """
    Fetch ODCS compose based on a remote compose-reference and store it locally
    """
    def __call__(self, request_reference: ComposeReference) -> ODCSResultReference:
        raise NotImplementedError()
