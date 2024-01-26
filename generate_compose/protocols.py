"""compose generator protocols"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar, Mapping, Protocol

from odcs.client.odcs import ComposeSourceGeneric  # type: ignore
from odcs.client.odcs import (
    ComposeSourceBuild,
    ComposeSourceModule,
    ComposeSourcePulp,
    ComposeSourceRawConfig,
    ComposeSourceTag,
)

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

    kinds: ClassVar[Mapping] = {
        "ComposeSourceBuild": ComposeSourceBuild,
        "ComposeSourceModule": ComposeSourceModule,
        "ComposeSourcePulp": ComposeSourcePulp,
        "ComposeSourceRawConfig": ComposeSourceRawConfig,
        "ComposeSourceTag": ComposeSourceTag,
    }

    @classmethod
    def from_list(cls, input_configs: list) -> "ODCSComposesConfigs":
        """
        Return an instance of the class given a configuration list extracted from
        input config yaml.

        yaml structure:
        composes:
          - kind: ComposeSourceTag
            spec:
              tag: some-tag
              some-source-kw-arg: some-source-kw-value
            additional_args:
              some-additional-arg: some-additional-value

        :param input_configs: configs extracted from yaml.
        """
        configs = [
            ODCSComposeConfig(
                spec=cls.make_compose_config(entry["spec"], entry["kind"]),
                additional_args=entry["additional_args"],
            )
            for entry in input_configs
        ]

        return cls(configs)

    @classmethod
    def make_compose_config(cls, spec: dict, kind: str) -> ComposeSourceGeneric:
        """
        Create an instance of ComposeSourceGeneric implementation given the class name
        and the required inputs.
        """
        return cls.kinds[kind](**spec)


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

    def __call__(self, compose_configs: ODCSComposesConfigs) -> ODCSRequestReferences:
        pass


class ComposeFetcher(Protocol):
    """
    Given remote compose reference, return a local compose reference
    """

    def __call__(self, request_reference: ODCSRequestReferences) -> ODCSResultReference:
        pass
