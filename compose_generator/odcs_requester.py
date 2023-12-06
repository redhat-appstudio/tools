from dataclasses import dataclass

from .protocols import ComposeConfigurations, ComposeReference, ComposeRequester


@dataclass(frozen=True)
class ODCSRequestReference(ComposeReference):
    """
    Reference to a remotely-stored compose data
    """
    compose_url: str


@dataclass(frozen=True)
class ODCSRequester(ComposeRequester):
    """
    Request a new ODCS compose based on compose configurations and return a reference
    to the remote compose location.
    """
    def __call__(self, configs: ComposeConfigurations) -> ODCSRequestReference:
        raise NotImplementedError()
