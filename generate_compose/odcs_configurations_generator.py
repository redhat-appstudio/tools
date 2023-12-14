"""Configurations generator for ODCS compose"""
from dataclasses import dataclass, field

from odcs.client.odcs import ComposeSourceGeneric  # type: ignore

from .protocols import ComposeConfigurations, ComposeConfigurationsGenerator


@dataclass(frozen=True)
class ODCSComposeConfig:
    """
    Configurations to be used for requesting an ODCS compose
    """

    spec: ComposeSourceGeneric
    additional_args: dict = field(default_factory=dict)


@dataclass
class ODCSComposesConfigs(ComposeConfigurations):
    """
    Configurations to be used for requesting multiple ODCS composes
    """

    configs: list[ODCSComposeConfig]


@dataclass(frozen=True)
class ODCSConfigurationsGenerator(ComposeConfigurationsGenerator):
    """
    Generate odcs configurations based on container and content_sets YAMLs.

    :param compose_inputs: data loaded from compose inputs yaml
    """

    compose_inputs: dict

    def __call__(self) -> ComposeConfigurations:
        raise NotImplementedError()
