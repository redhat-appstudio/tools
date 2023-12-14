"""Fetch ready ODCS compose"""
import tempfile
from dataclasses import dataclass
from pathlib import Path

import requests

from .odcs_requester import ODCSRequestReferences
from .protocols import ComposeFetcher, ComposeReference


@dataclass(frozen=True)
class ODCSResultReference(ComposeReference):
    """
    Reference to locally-stored compose results
    """

    compose_dir_path: Path


@dataclass(frozen=True)
class ODCSFetcher(ComposeFetcher):
    """
    Fetch ODCS compose based on a remote compose-reference and store it locally

    :param compose_dir_path: The Desired path for where compose files should be stored
    """

    compose_dir_path: Path

    def __call__(self, request_reference: ComposeReference) -> ODCSResultReference:
        """
        Fetch the 'ODCS compose' from a remote reference.

        :param request_reference: An object containing the url references for the
                                  ODCS compose file.

        :raises HTTPError: If the request for the ODCS compose file failed.
        :return: The filesystem path to the downloaded ODCS compose file.
        """
        self.compose_dir_path.mkdir(parents=True, exist_ok=True)
        assert isinstance(request_reference, ODCSRequestReferences)
        urls = request_reference.compose_urls
        for url in urls:
            with tempfile.NamedTemporaryFile(
                delete=False, dir=self.compose_dir_path
            ) as compose_path:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                Path(compose_path.name).write_text(response.text, encoding="utf-8")

        return ODCSResultReference(compose_dir_path=self.compose_dir_path)
