#!/usr/bin/env python3

"""Initialize and use a compose generator using ODCS"""

from .compose_generator import ComposeGenerator
from .odcs_configurations_generator import ODCSConfigurationsGenerator
from .odcs_fetcher import ODCSFetcher
from .odcs_requester import ODCSRequester


def main():
    """
    Get inputs from container and content_sets yamls and relay them to an ODCS
    compose generator that will request a compose and store it in a TBD location.
    """
    # Get inputs from container and content_sets yamls
    container_data = {}
    content_sets_data = {}

    compose_generator = ComposeGenerator(
        configurations_generator=ODCSConfigurationsGenerator(
            container_data=container_data,
            content_sets_data=content_sets_data,
        ),
        requestor=ODCSRequester(),
        fetcher=ODCSFetcher(),
    )
    compose_generator()


if __name__ == "__main__":
    main()
