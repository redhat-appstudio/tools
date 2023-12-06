from typing import Protocol


class ComposeConfigurations(Protocol):
    """
    Data class for storing compose configurations
    """


class ComposeConfigurationsGenerator(Protocol):
    """
    Generate compose configurations
    """
    def __call__(self) -> ComposeConfigurations:
        pass


class ComposeReference(Protocol):
    """
    Data class for storing compose reference
    """


class ComposeRequester(Protocol):
    """
    Given compose configurations, return a remote compose reference
    """
    def __call__(self, configs: ComposeConfigurations) -> ComposeReference:
        pass


class ComposeFetcher(Protocol):
    """
    Given remote compose reference, return a local compose reference
    """

    def __call__(self, request_reference: ComposeReference) -> ComposeReference:
        pass
