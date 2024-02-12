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
@click.option(
    "--client-id",
    help="Client ID used for authenticating with ODCS",
    type=click.STRING,
    envvar="CLIENT_ID",
)
@click.option(
    "--client-secret",
    help="Client secret used for generating OIDC token",
    type=click.STRING,
    envvar="CLIENT_SECRET",
)
def main(
    compose_dir_path: Path,
    compose_input_yaml_path: Path,
    client_id: str,
    client_secret: str,
):
    """
    Get inputs from container and content_sets YAMLs and relay them to an ODCS
    compose generator that will request a compose and store it in a TBD location.
    """
    try:
        compose_inputs: dict = yaml.safe_load(compose_input_yaml_path.read_text())
    except FileNotFoundError as ex:
        raise FileNotFoundError(
            f"Could not find compose input file at {compose_input_yaml_path.resolve()}"
        ) from ex

    compose_generator = ComposeGenerator(
        configurations_generator=ODCSConfigurationsGenerator(
            compose_inputs=compose_inputs,
        ),
        requester=ODCSRequester(client_id=client_id, client_secret=client_secret),
        fetcher=ODCSFetcher(compose_dir_path=compose_dir_path),
    )
    compose_generator()


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
