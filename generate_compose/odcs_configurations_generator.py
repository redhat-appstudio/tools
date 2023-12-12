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

    :param container_data: data loaded from container.yaml
    :param content_sets_data: data loaded from content_sets.yaml
    """

    container_data: dict
    content_sets_data: dict

    def __call__(self) -> ODCSConfigurations:
        raise NotImplementedError()
