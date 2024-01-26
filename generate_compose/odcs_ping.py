"""Check connectivity to ODCS"""

import sys

import click
import requests
from odcs.client.odcs import ODCS, AuthMech  # type: ignore


def check_about(odcs):
    """Check the ODCS "about" API call"""
    try:
        about = odcs.about()
    except requests.exceptions.SSLError as e:
        print(f"Failed to connect to ODCS:\n  {e}")
        sys.exit(1)

    sign_keys = about.get("sigkeys", [])
    allowed_users = "\n  ".join(about.get("allowed_clients", {}).get("users", []))
    allowed_groups = "\n  ".join(about.get("allowed_clients", {}).get("groups", []))

    print(f"Connected ODCS version {about['version']}")
    if sign_keys:
        print(f"Signing keys: {sign_keys}")
    if allowed_users:
        print(f"Allowed users:\n  {allowed_users}")
    if allowed_groups:
        print(f"Allowed groups:\n  {allowed_groups}")


def check_new_compose(odcs):
    """Check the ODCS "new_compose" API call"""
    print("Attempting to generate a compose")
    sources = "squid:4:8090020231130092412:a75119d5"
    source_type = "module"
    try:
        compose = odcs.new_compose(sources, source_type)
        compose = odcs.wait_for_compose(compose["id"], timeout=600)
    except requests.exceptions.HTTPError as e:
        print(f"Failed to generate compose:\n  {e}")
        sys.exit(2)
    if compose["state_name"] == "done":
        print("Compose done:")
        print(f"  repo file at: {compose['result_repofile']}")
        print(f"  owner: {compose['owner']}")
    else:
        print("Failed to generate compose (Not done after timeout)")
        sys.exit(3)


@click.command()
@click.option(
    "--server",
    help="ODCS server URL",
    type=click.STRING,
    default="https://odcs.engineering.redhat.com",
    metavar="URL",
)
def main(server):
    """Check connectivity to ODCS"""
    odcs = ODCS(server, auth_mech=AuthMech.Kerberos)

    check_about(odcs)
    print()
    check_new_compose(odcs)
