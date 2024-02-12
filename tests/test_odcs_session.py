"""Test odcs_session"""

from unittest.mock import create_autospec, sentinel

import pytest
from authlib.integrations.requests_client import OAuth2Session  # type: ignore

from generate_compose.odcs_session import get_odcs_session


class TestODCSSession:
    """Test odcs_session.py"""

    def test_get_odcs_session(self) -> None:
        """test get_odcs_session"""
        mock = create_autospec(OAuth2Session)
        mock.return_value.fetch_token.return_value = {"access_token": sentinel.token}
        odcs = get_odcs_session(
            client_id="some-client",
            client_secret="some-secret",
            odcs_server=sentinel.url,
            session_fetcher=mock,
        )
        assert odcs.server_url == sentinel.url
        assert odcs._openidc_token == sentinel.token  # pylint: disable=protected-access

    def test_get_odcs_session_fail_fetching_token(self) -> None:
        """test get_odcs_session fails with proper message"""
        mock = create_autospec(OAuth2Session)
        mock.return_value.fetch_token.side_effect = Exception
        with pytest.raises(RuntimeError) as ex:
            get_odcs_session(
                client_id="some-client",
                client_secret="some-secret",
                odcs_server=sentinel.url,
                session_fetcher=mock,
            )
        assert str(ex.value) == "Failed fetching OIDC token"
