"""Test cmd_runner.py"""
from subprocess import CalledProcessError
from unittest.mock import MagicMock, create_autospec

import pytest
from pytest import MonkeyPatch

from verify_rpms import cmd_runner
from verify_rpms.cmd_runner import CmdRunner, run
from verify_rpms.exceptions import CmdError


class TestCmdRunner:
    """Test cmd_runner.py"""

    @pytest.fixture
    def args(self) -> list[str]:
        """arguments fixture to pass to command line"""
        return ["command", "to", "run"]

    @pytest.fixture
    def mock_run(self) -> MagicMock:
        """Mock subprocess.run"""
        mock: MagicMock = create_autospec(run)
        return mock

    def test_cmd_runner_valid(
        self, mock_run: MagicMock, args: list[str], monkeypatch: MonkeyPatch
    ) -> None:
        """Test valid command line"""
        mock_run.return_value = "Success"
        monkeypatch.setattr(cmd_runner, run.__name__, mock_run)
        result = CmdRunner.run_cmd(args=args)
        assert result == "Success"

    @pytest.mark.parametrize("error", ["CalledProcessError", "FileNotFoundError"])
    def test_cmd_runner_exception(
        self, mock_run: MagicMock, args: list[str], monkeypatch: MonkeyPatch, error: str
    ) -> None:
        """Test exceptions thrown by subprocess.run"""
        if error == "CalledProcessError":
            mock_run.side_effect = CalledProcessError(
                returncode=1, cmd=args, stderr="Error Message"
            )
        if error == "FileNotFoundError":
            mock_run.side_effect = FileNotFoundError("Error Message")
        monkeypatch.setattr(cmd_runner, run.__name__, mock_run)
        with pytest.raises(CmdError) as exec_info:
            CmdRunner.run_cmd(args=args)
        assert f"Running {args} failed\nError Message" in str(exec_info.value)
