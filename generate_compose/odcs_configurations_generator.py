"""Configurations generator for ODCS compose"""
from dataclasses import dataclass

from .protocols import ComposeConfigurationsGenerator, ODCSComposesConfigs


@dataclass(frozen=True)
class ODCSConfigurationsGenerator(ComposeConfigurationsGenerator):
    """
    Generate odcs configurations based on container and content_sets YAMLs.

    :param compose_inputs: data loaded from compose inputs yaml
    """

    compose_inputs: dict

    def __call__(self) -> ODCSComposesConfigs:
        raise NotImplementedError()
