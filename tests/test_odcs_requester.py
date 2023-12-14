"""test_odcs_requester.py - test odcs_requester"""
from typing import Callable
from unittest.mock import MagicMock, call, create_autospec

import pytest
from odcs.client.odcs import ODCS, ComposeSourceGeneric  # type: ignore
from requests.exceptions import HTTPError

from generate_compose.odcs_configurations_generator import (
    ODCSComposeConfig,
    ODCSComposesConfigs,
)
from generate_compose.odcs_requester import ODCSRequester, ODCSRequestReferences


class TestODCSRequester:
    """Test odcs_compose_generator.py"""

    @pytest.fixture()
    def compose_url(self) -> str:
        """Example compose-url, as close to the one expected"""
        return "http://download.eng.bos.redhat.com/odcs/prod/odcs-222222"

    @pytest.fixture()
    def create_odcs_mock(self, compose_url: str) -> Callable[[int, bool], MagicMock]:
        """Create an ODCS mock with specific results for the compose method"""

        def _mock_odcs_compose(
            num_of_composes: int = 1, exception: bool = False
        ) -> MagicMock:
            """Mock for ODCS.compose"""
            mock: MagicMock = create_autospec(ODCS)
            if exception:
                mock.request_compose.side_effect = HTTPError
            else:
                mock.request_compose.side_effect = [
                    {"result_repofile": f"{compose_url}", "id": i}
                    for i in range(1, num_of_composes + 1)
                ]
            return mock

        return _mock_odcs_compose

    @pytest.fixture()
    def compose_source(self) -> MagicMock:
        """Creates a ComposeSource with dynamic typing"""
        mock: MagicMock = create_autospec(ComposeSourceGeneric)
        return mock

    @pytest.mark.parametrize(
        "composes_configs",
        [
            pytest.param(
                ODCSComposesConfigs([ODCSComposeConfig(spec=compose_source)]),
                id="single compose, tag source, no additional arguments",
            ),
            pytest.param(
                ODCSComposesConfigs(
                    [
                        ODCSComposeConfig(spec=compose_source),
                        ODCSComposeConfig(spec=compose_source),
                    ]
                ),
                id="multiple composes, , tag source, no additional arguments",
            ),
        ],
    )
    def test_odcs_requester(
        self,
        create_odcs_mock: Callable,
        compose_url: str,
        composes_configs: ODCSComposesConfigs,
    ) -> None:
        """test ODCSRequester.__call__"""
        num_of_composes: int = len(composes_configs.configs)
        mock_odcs = create_odcs_mock(num_of_composes)
        odcs_requester = ODCSRequester(odcs=mock_odcs)
        req_ref = odcs_requester(compose_configs=composes_configs)

        expected_calls = [
            call(composes_configs.configs[0].spec) for _ in range(num_of_composes)
        ]
        assert mock_odcs.request_compose.call_args_list == expected_calls

        assert mock_odcs.request_compose.call_count == num_of_composes
        expected_calls = [
            call(compose_id) for compose_id in range(1, num_of_composes + 1)
        ]
        mock_odcs.wait_for_compose.assert_has_calls(expected_calls, any_order=False)
        assert mock_odcs.wait_for_compose.call_count == num_of_composes

        expected_req_ref = ODCSRequestReferences(
            compose_urls=[compose_url] * num_of_composes
        )
        assert req_ref == expected_req_ref

    def test_odcs_requester_compose_failure_should_raise(
        self, create_odcs_mock: Callable, compose_source: ComposeSourceGeneric
    ) -> None:
        """test ODCSRequester.__call__ raise an exception when the compose fails"""
        mock_odcs = create_odcs_mock(exception=True)
        odcs_requester = ODCSRequester(odcs=mock_odcs)
        composes_config = ODCSComposesConfigs([ODCSComposeConfig(spec=compose_source)])
        with pytest.raises(HTTPError):
            odcs_requester(compose_configs=composes_config)
        assert mock_odcs.wait_for_compose.call_count == 0

    def test_odcs_requester_compose_timeout_failure_should_raise(
        self, create_odcs_mock: Callable, compose_source: ComposeSourceGeneric
    ) -> None:
        """test ODCSRequester.__call__ raise an exception when
        waiting for compose throws an exception due to a timeout"""

        mock_odcs = create_odcs_mock(exception=False)
        mock_odcs.wait_for_compose.side_effect = RuntimeError

        odcs_requester = ODCSRequester(odcs=mock_odcs)
        composes_config = ODCSComposesConfigs([ODCSComposeConfig(spec=compose_source)])

        with pytest.raises(RuntimeError):
            odcs_requester(compose_configs=composes_config)
        assert mock_odcs.request_compose.call_count == 1
        assert mock_odcs.wait_for_compose.call_count == 1
