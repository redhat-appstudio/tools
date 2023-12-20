"""Test odcs_compose_generator.py end-to-end"""
from pathlib import Path
from unittest.mock import MagicMock, create_autospec

import pytest
import yaml
from pytest import MonkeyPatch

from generate_compose import odcs_compose_generator
from generate_compose.compose_generator import ComposeGenerator
from generate_compose.odcs_configurations_generator import ODCSConfigurationsGenerator
from generate_compose.odcs_fetcher import ODCSFetcher
from generate_compose.odcs_requester import ODCSRequester


class TestODCSComposeGenerator:
    """Test odcs_compose_generator.py end-to-end"""

    @pytest.fixture()
    def input_data(self) -> list:
        """inputs yaml content"""
        return [{"spec": {}, "additional_args": {}}]

    @pytest.fixture()
    def input_yaml(self, input_data: list, tmp_path: Path) -> Path:
        """path to inputs.yaml with content"""
        path = tmp_path / "inputs.yaml"
        with path.open("w") as file:
            yaml.dump(input_data, file)
        return path

    @pytest.fixture()
    def compose_dir_path(self, tmp_path: Path) -> Path:
        """Path to where the compose should be stored"""
        return tmp_path

    @pytest.fixture()
    def mock_config_generator(self, monkeypatch: MonkeyPatch) -> MagicMock:
        """Monkey-patched ODCSConfigurationsGenerator"""
        mock: MagicMock = create_autospec(
            ODCSConfigurationsGenerator,
            return_value=create_autospec(ODCSConfigurationsGenerator, instance=True),
        )
        monkeypatch.setattr(
            odcs_compose_generator, ODCSConfigurationsGenerator.__name__, mock
        )
        return mock

    @pytest.fixture()
    def mock_compose_generator(self, monkeypatch: MonkeyPatch) -> MagicMock:
        """Monkey-patched ComposeGenerator"""
        mock: MagicMock = create_autospec(ComposeGenerator)
        monkeypatch.setattr(odcs_compose_generator, ComposeGenerator.__name__, mock)
        return mock

    @pytest.fixture()
    def mock_requester(self, monkeypatch: MonkeyPatch) -> MagicMock:
        """Monkey-patched ODCSRequester"""
        mock: MagicMock = create_autospec(ODCSRequester)
        monkeypatch.setattr(odcs_compose_generator, ODCSRequester.__name__, mock)
        return mock

    @pytest.fixture()
    def mock_fetcher(self, monkeypatch: MonkeyPatch) -> MagicMock:
        """Monkey-patched ODCSFetcher"""
        mock: MagicMock = create_autospec(ODCSFetcher)
        monkeypatch.setattr(odcs_compose_generator, ODCSFetcher.__name__, mock)
        return mock

    def test_main(  # pylint: disable=too-many-arguments
        self,
        compose_dir_path: Path,
        input_data: dict,
        input_yaml: Path,
        mock_compose_generator: MagicMock,
        mock_config_generator: MagicMock,
        mock_requester: MagicMock,
        mock_fetcher: MagicMock,
    ) -> None:
        """Test call to odcs_compose_generator.py main function"""
        odcs_compose_generator.main(  # pylint: disable=no-value-for-parameter
            args=[
                "--compose-dir-path",
                str(compose_dir_path),
                "--compose-input-yaml-path",
                str(input_yaml),
            ],
            obj={},
            standalone_mode=False,
        )

        mock_config_generator.assert_called_once_with(compose_inputs=input_data)
        mock_fetcher.assert_called_once_with(compose_dir_path=compose_dir_path)
        mock_compose_generator.assert_called_once_with(
            configurations_generator=mock_config_generator.return_value,
            requester=mock_requester.return_value,
            fetcher=mock_fetcher.return_value,
        )
        mock_compose_generator.return_value.assert_called_once_with()
