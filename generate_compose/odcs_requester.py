"""Request a new ODCS compose"""
from dataclasses import dataclass

from odcs.client.odcs import ODCS, AuthMech  # type: ignore

from .odcs_configurations_generator import ODCSComposesConfigs
from .protocols import ComposeRequester, ODCSRequestReferences


@dataclass(frozen=True)
class ODCSRequester(ComposeRequester):
    """
    Request new ODCS composes based on compose configurations and return a reference
    to the remote compose location.
    """

    odcs: ODCS = ODCS(
        "https://odcs.engineering.redhat.com/", auth_mech=AuthMech.Kerberos
    )

    def __call__(self, compose_configs: ODCSComposesConfigs) -> ODCSRequestReferences:
        composes = [
            self.odcs.request_compose(config.spec, **config.additional_args)
            for config in compose_configs.configs
        ]

        finished_composes = [
            self.odcs.wait_for_compose(compose["id"]) for compose in composes
        ]

        compose_urls = [compose["result_repofile"] for compose in finished_composes]
        req_refrences = ODCSRequestReferences(compose_urls=compose_urls)
        return req_refrences
