"""Top level generic entity for creating a compose"""
from dataclasses import dataclass

from .protocols import (
    ComposeConfigurations,
    ComposeConfigurationsGenerator,
    ComposeFetcher,
    ComposeReference,
    ComposeRequester,
)


@dataclass(frozen=True)
class ComposeGenerator:
    """
    Given implementations to all building blocks of a compose generator, generate a
    compose and return its reference.

    :param configurations_generator: an object to generate the configurations used for
        requesting a new compose
    :param requestor: an object to request a new composed
    :param fetcher: an object to fetch a compose once it's ready
    """

    configurations_generator: ComposeConfigurationsGenerator
    requestor: ComposeRequester
    fetcher: ComposeFetcher

    def __call__(self) -> ComposeReference:
        configs: ComposeConfigurations = self.configurations_generator()
        request_reference: ComposeReference = self.requestor(configs=configs)
        result_reference: ComposeReference = self.fetcher(
            request_reference=request_reference
        )
        return result_reference
