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
    "--compose-file-path",
    help="Compose file target path (including filename).",
    type=click.Path(path_type=Path),
    required=True,
)
@click.option(
    "--container-yaml-path",
    help="Path in which container yaml file is stored",
    type=click.Path(path_type=Path),
    required=True,
)
@click.option(
    "--content-sets-yaml-path",
    help="Path in which content_sets yaml file is stored",
    type=click.Path(path_type=Path),
    required=True,
)
def main(
    compose_file_path: Path,
    container_yaml_path: Path,
    content_sets_yaml_path: Path,
):
    """
    Get inputs from container and content_sets yamls and relay them to an ODCS
    compose generator that will request a compose and store it in a TBD location.
    """
    container_data: dict = yaml.safe_load(container_yaml_path.read_text())
    content_sets_data: dict = yaml.safe_load(content_sets_yaml_path.read_text())

    compose_generator = ComposeGenerator(
        configurations_generator=ODCSConfigurationsGenerator(
            container_data=container_data,
            content_sets_data=content_sets_data,
        ),
        requestor=ODCSRequester(),
        fetcher=ODCSFetcher(compose_file_path=compose_file_path),
    )
    compose_generator()


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
