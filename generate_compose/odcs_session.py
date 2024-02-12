"""Authenticate with ODCS using OIDC"""

from typing import Callable

from authlib.integrations.requests_client import OAuth2Session  # type: ignore
from odcs.client.odcs import ODCS, AuthMech  # type: ignore


def get_odcs_session(
    client_id: str,
    client_secret: str,
    odcs_server: str = "https://odcs.engineering.redhat.com",
    oidc_token_url: str = (
        "https://auth.redhat.com/auth/realms/EmployeeIDP/protocol/openid-connect/token"
    ),
    session_fetcher: Callable[[str, str, str, str], OAuth2Session] = OAuth2Session,
) -> ODCS:
    """Authenticate using OIDC and return an authenticated ODCS client"""
    oidc_client = session_fetcher(
        client_id, client_secret, "client_secret_basic", "openid"
    )

    try:
        token = oidc_client.fetch_token(
            url=oidc_token_url, grant_type="client_credentials"
        )
    except Exception as ex:
        raise RuntimeError("Failed fetching OIDC token") from ex

    return ODCS(
        odcs_server, auth_mech=AuthMech.OpenIDC, openidc_token=token["access_token"]
    )
