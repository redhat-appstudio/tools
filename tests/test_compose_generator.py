"""Test ComposeGenerator class using mock dependencies"""

from unittest.mock import MagicMock, create_autospec

import pytest

from generate_compose.compose_generator import ComposeGenerator
from generate_compose.protocols import (
    ComposeConfigurationsGenerator,
    ComposeFetcher,
    ComposeRequester,
)


class TestComposeGenerator:
    """Test ComposeGenerator class using mock dependencies"""

    @pytest.fixture()
    def mock_config_generator(self) -> MagicMock:
        """Generic config generator"""
        return create_autospec(ComposeConfigurationsGenerator)

    @pytest.fixture()
    def mock_requester(self) -> MagicMock:
        """Generic ComposeRequester"""
        return create_autospec(ComposeRequester)

    @pytest.fixture()
    def mock_fetcher(self) -> MagicMock:
        """Monkey-patched ODCSFetcher"""
        return create_autospec(ComposeFetcher)

    def test_compose_generator(
        self,
        mock_config_generator: MagicMock,
        mock_requester: MagicMock,
        mock_fetcher: MagicMock,
    ) -> None:
        """Test ComposeGenerator call using mock dependencies"""
        compose_generator = ComposeGenerator(
            configurations_generator=mock_config_generator,
            requester=mock_requester,
            fetcher=mock_fetcher,
        )
        out = compose_generator()

        mock_config_generator.assert_called_once_with()
        mock_requester.assert_called_once_with(
            compose_configs=mock_config_generator.return_value
        )
        mock_fetcher.assert_called_once_with(
            request_reference=mock_requester.return_value
        )
        assert out == mock_fetcher.return_value
