"""Request a new ODCS compose"""

from dataclasses import dataclass
from typing import Callable

from odcs.client.odcs import ODCS  # type: ignore

from .odcs_configurations_generator import ODCSComposesConfigs
from .odcs_session import get_odcs_session
from .protocols import ComposeRequester, ODCSRequestReferences


@dataclass(frozen=True)
class ODCSRequester(ComposeRequester):
    """
    Request new ODCS composes based on compose configurations and return a reference
    to the remote compose location.
    """

    client_id: str
    client_secret: str
    odcs_session_getter: Callable[[str, str, str], ODCS] = get_odcs_session

    def __call__(self, compose_configs: ODCSComposesConfigs) -> ODCSRequestReferences:
        odcs: ODCS = self.odcs_session_getter(
            self.client_id,
            self.client_secret,
            "https://odcs.engineering.redhat.com/",
        )
        composes = [
            odcs.request_compose(config.spec, **config.additional_args)
            for config in compose_configs.configs
        ]

        finished_composes = [
            odcs.wait_for_compose(compose["id"]) for compose in composes
        ]

        failed_composes = [
            compose for compose in finished_composes if compose["state_name"] != "done"
        ]

        if failed_composes:
            failures = [
                f"{compose['id']}: state={compose['state_name']} "
                f"reason={compose['state_reason']}"
                for compose in failed_composes
            ]
            sep = "\n"
            raise RuntimeError(
                f"Failed to generate some composes:\n{sep.join(failures)}"
            )

        compose_urls = [compose["result_repofile"] for compose in finished_composes]
        req_refrences = ODCSRequestReferences(compose_urls=compose_urls)
        return req_refrences
