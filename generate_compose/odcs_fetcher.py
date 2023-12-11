"""Fetch ready ODCS compose"""
from dataclasses import dataclass
from pathlib import Path

import requests

from .odcs_requester import ODCSRequestReference
from .protocols import ComposeFetcher, ComposeReference


@dataclass(frozen=True)
class ODCSResultReference(ComposeReference):
    """
    Reference to a locally-stored compose result
    """

    compose_file_path: Path


@dataclass(frozen=True)
class ODCSFetcher(ComposeFetcher):
    """
    Fetch ODCS compose based on a remote compose-reference and store it locally

    :param compose_file_path: The Desired path for the compose file.
                              must include the path to the file as
                              well as the file's name.
    """

    compose_file_path: Path

    def __call__(self, request_reference: ComposeReference) -> ODCSResultReference:
        """
        Fetch the 'ODCS compose' from a remote reference.

        :param request_reference: An object containing the url reference for the
                                  ODCS compose file.

        :raises HTTPError: If the request for the ODCS compose file failed.
        :return: The filesystem path to the downloaded ODCS compose file.
        """
        assert isinstance(request_reference, ODCSRequestReference)
        response = requests.get(request_reference.compose_url, timeout=10)
        response.raise_for_status()

        self.compose_file_path.parent.mkdir(parents=True, exist_ok=True)
        self.compose_file_path.write_text(response.text, encoding="utf-8")
        ocds_result_ref = ODCSResultReference(compose_file_path=self.compose_file_path)
        return ocds_result_ref
