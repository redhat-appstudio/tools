#!/usr/bin/env python3

"""Initialize and use a compose generator using ODCS"""

from pathlib import Path

import click
import yaml

from .compose_generator import ComposeGenerator
from .odcs_configurations_generator import ODCSConfigurationsGenerator
from .odcs_fetcher import ODCSFetcher
from .odcs_requester import ODCSRequester


@click.command()
@click.option(
    "--compose-dir-path",
    help="Compose files target directory.",
    type=click.Path(path_type=Path),
    required=True,
)
@click.option(
    "--compose-input-yaml-path",
    help="Path in which inputs yaml is stored",
    type=click.Path(path_type=Path),
    required=True,
)
def main(
    compose_dir_path: Path,
    compose_input_yaml_path: Path,
):
    """
    Get inputs from container and content_sets YAMLs and relay them to an ODCS
    compose generator that will request a compose and store it in a TBD location.
    """
    compose_inputs: dict = yaml.safe_load(compose_input_yaml_path.read_text())

    compose_generator = ComposeGenerator(
        configurations_generator=ODCSConfigurationsGenerator(
            compose_inputs=compose_inputs,
        ),
        requester=ODCSRequester(),
        fetcher=ODCSFetcher(compose_dir_path=compose_dir_path),
    )
    compose_generator()


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
