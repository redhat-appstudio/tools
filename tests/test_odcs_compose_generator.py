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
    def container_data(self) -> dict:
        """container.yaml content"""
        return {
            "compose": {"pulp_repos": True, "signing_intent": "release"},
            "image_build_method": "imagebuilder",
            "remote_source": {
                "pkg_managers": [],
                "ref": "f6ceb2ff45a71938f6949abcd15aa0a1b0f79842",
                "repo": "https://github.com/kubevirt/must-gather",
            },
        }

    @pytest.fixture()
    def container_yaml(self, container_data: dict, tmp_path: Path) -> Path:
        """path to container.yaml with content"""
        path = tmp_path / "container.yaml"
        with path.open("w") as file:
            yaml.dump(container_data, file)
        return path

    @pytest.fixture()
    def content_sets_data(self) -> dict:
        """content_sets.yaml content"""
        return {
            "x86_64": [
                "rhel-8-for-x86_64-baseos-eus-rpms__8_DOT_6",
                "rhel-8-for-x86_64-appstream-eus-rpms__8_DOT_6",
            ],
            "aarch64": [
                "rhel-8-for-aarch64-baseos-eus-rpms__8_DOT_6",
                "rhel-8-for-aarch64-appstream-eus-rpms__8_DOT_6",
            ],
        }

    @pytest.fixture()
    def content_sets_yaml(self, content_sets_data: dict, tmp_path: Path) -> Path:
        """path to content_sets.yaml with content"""
        path = tmp_path / "content_sets.yml"
        with path.open("w") as file:
            yaml.dump(content_sets_data, file)
        return path

    @pytest.fixture()
    def compose_file_path(self, tmp_path: Path) -> Path:
        """Path to where the compose should be stored"""
        return tmp_path / "repofile.repo"

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
        compose_file_path: Path,
        container_data: dict,
        container_yaml: Path,
        content_sets_data: dict,
        content_sets_yaml: Path,
        mock_compose_generator: MagicMock,
        mock_config_generator: MagicMock,
        mock_requester: MagicMock,
        mock_fetcher: MagicMock,
    ) -> None:
        """Test call to odcs_compose_generator.py main function"""
        odcs_compose_generator.main(  # pylint: disable=no-value-for-parameter
            args=[
                "--compose-file-path",
                str(compose_file_path),
                "--container-yaml-path",
                str(container_yaml),
                "--content-sets-yaml-path",
                str(content_sets_yaml),
            ],
            obj={},
            standalone_mode=False,
        )

        mock_config_generator.assert_called_once_with(
            container_data=container_data, content_sets_data=content_sets_data
        )
        mock_fetcher.assert_called_once_with(compose_file_path=compose_file_path)
        mock_compose_generator.assert_called_once_with(
            configurations_generator=mock_config_generator.return_value,
            requestor=mock_requester.return_value,
            fetcher=mock_fetcher.return_value,
        )
        mock_compose_generator.return_value.assert_called_once_with()
