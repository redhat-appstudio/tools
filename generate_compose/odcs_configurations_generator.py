"""Configurations generator for ODCS compose"""
from dataclasses import dataclass

from .protocols import ComposeConfigurations, ComposeConfigurationsGenerator


@dataclass(frozen=True)
class ODCSConfigurations(ComposeConfigurations):
    """
    Configurations to be used for requesting an ODCS compose
    """


@dataclass(frozen=True)
class ODCSConfigurationsGenerator(ComposeConfigurationsGenerator):
    """
    Generate odcs configurations based on container and content_sets YAMLs.

    :param compose_inputs: data loaded from compose inputs yaml
    """

    compose_inputs: dict

    def __call__(self) -> ODCSConfigurations:
        raise NotImplementedError()
