"""compose generator protocols"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from odcs.client.odcs import ComposeSourceGeneric  # type: ignore

# pylint: disable=too-few-public-methods


@dataclass(frozen=True)
class ODCSComposeConfig:
    """
    Configurations to be used for requesting an ODCS compose
    """

    spec: ComposeSourceGeneric
    additional_args: dict = field(default_factory=dict)


@dataclass
class ODCSComposesConfigs:
    """
    Configurations to be used for requesting multiple ODCS composes
    """

    configs: list[ODCSComposeConfig]


class ComposeConfigurationsGenerator(Protocol):
    """
    Generate compose configurations
    """

    def __call__(self) -> ODCSComposesConfigs:
        pass


@dataclass(frozen=True)
class ODCSRequestReferences:
    """
    Reference to remotely-stored compose requests
    """

    compose_urls: list[str]


@dataclass(frozen=True)
class ODCSResultReference:
    """
    Reference to locally-stored compose results
    """

    compose_dir_path: Path


class ComposeRequester(Protocol):
    """
    Given compose configurations, return a remote compose reference
    """

    def __call__(self, configs: ODCSComposesConfigs) -> ODCSRequestReferences:
        pass


class ComposeFetcher(Protocol):
    """
    Given remote compose reference, return a local compose reference
    """

    def __call__(self, request_reference: ODCSRequestReferences) -> ODCSResultReference:
        pass
