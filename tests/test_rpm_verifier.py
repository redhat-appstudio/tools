"""Test rpm_verifier.py end-to-end"""

from pathlib import Path
from subprocess import CalledProcessError, run
from textwrap import dedent
from typing import Callable
from unittest.mock import MagicMock, create_autospec

import pytest
from pytest import MonkeyPatch

from verify_rpms import rpm_verifier
from verify_rpms.rpm_verifier import (
    ImageProcessor,
    ProcessedImage,
    generate_output,
    get_rpmdb,
    get_rpms_data,
    get_unsigned_rpms,
)


def test_get_rpmdb(tmp_path: Path) -> None:
    """Test get_rpmdb"""
    image = "my-image"
    mock_runner = create_autospec(run)
    out = get_rpmdb(
        container_image=image,
        target_dir=tmp_path,
        runner=mock_runner,
    )
    mock_runner.assert_called_once()
    assert mock_runner.call_args.args[0] == [
        "oc",
        "image",
        "extract",
        "my-image",
        "--path",
        f"/var/lib/rpm/:{tmp_path}",
    ]
    assert mock_runner.call_count == 1
    assert out == tmp_path


@pytest.mark.parametrize(
    ("test_input", "expected"),
    [
        pytest.param(
            dedent(
                """
                libssh-config-0.9.6-10.el8_8 RSA/SHA256, Tue 6 May , Key ID 1234567890
                python39-twisted-23.10.0-1.el8ap (none)
                libmodulemd-2.13.0-1.el8 RSA/SHA256, Wed 18 Aug , Key ID 1234567890
                gpg-pubkey-d4082792-5b32db75 (none)
                """
            ).strip(),
            [
                "libssh-config-0.9.6-10.el8_8 RSA/SHA256, Tue 6 May , Key ID 1234567890",
                "python39-twisted-23.10.0-1.el8ap (none)",
                "libmodulemd-2.13.0-1.el8 RSA/SHA256, Wed 18 Aug , Key ID 1234567890",
                "gpg-pubkey-d4082792-5b32db75 (none)",
            ],
            id="Mix of signed and unsigned",
        ),
        pytest.param("", [], id="Empty list"),
    ],
)
def test_get_rpms_data(test_input: list[str], expected: list[str]) -> None:
    """Test get_rpms_data"""
    mock_runner = create_autospec(run)
    mock_runner.return_value.stdout = test_input
    result = get_rpms_data(rpmdb=Path("rpmdb_folder"), runner=mock_runner)
    mock_runner.assert_called_once()
    assert mock_runner.call_args.args[0] == [
        "rpm",
        "-qa",
        "--qf",
        "%{NAME}-%{VERSION}-%{RELEASE} %{SIGPGP:pgpsig}\n",
        "--dbpath",
        "rpmdb_folder",
    ]
    assert result == expected


@pytest.mark.parametrize(
    ("test_input", "expected"),
    [
        pytest.param(
            [
                "libssh-config-0.9.6-10.el8_8 RSA/SHA256, Tue 6 May , Key ID 1234567890",
                "python39-twisted-23.10.0-1.el8ap (none)",
                "libmodulemd-2.13.0-1.el8 RSA/SHA256, Wed 18 Aug , Key ID 1234567890",
                "gpg-pubkey-d4082792-5b32db75 (none)",
            ],
            ["python39-twisted-23.10.0-1.el8ap"],
            id="Mix of signed and unsigned",
        ),
        pytest.param(
            [
                "libssh-config-0.9.6-10.el8_8 RSA/SHA256, Tue 6 May , Key ID 1234567890",
                "libmodulemd-2.13.0-1.el8 RSA/SHA256, Wed 18 Aug , Key ID 1234567890",
            ],
            [],
            id="All signed",
        ),
        pytest.param(
            [
                "libssh-config-0.9.6-10.el8_8 (none)",
                "python39-twisted-23.10.0-1.el8ap (none)",
                "libmodulemd-2.13.0-1.el8 (none)",
            ],
            [
                "libssh-config-0.9.6-10.el8_8",
                "python39-twisted-23.10.0-1.el8ap",
                "libmodulemd-2.13.0-1.el8",
            ],
            id="All unsigned",
        ),
        pytest.param([], [], id="Empty list"),
    ],
)
def test_get_unsigned_rpms(test_input: list[str], expected: list[str]) -> None:
    """Test get_unsigned_rpms"""
    result = get_unsigned_rpms(rpms=test_input)
    assert result == expected


@pytest.mark.parametrize(
    ("processed_image", "expected_print", "expected_failures_exist"),
    [
        pytest.param(
            ProcessedImage(
                image="i1",
                unsigned_rpms=[],
            ),
            "No unsigned RPMs in i1",
            False,
            id="No unsigned RPMs + no errors. Do not report failures",
        ),
        pytest.param(
            ProcessedImage(
                image="i1",
                unsigned_rpms=["my-rpm"],
            ),
            dedent(
                """
                Found unsigned RPMs in i1:
                ['my-rpm']
                """
            ).strip(),
            True,
            id="Unsigned RPM + no errors. Report failures",
        ),
        pytest.param(
            ProcessedImage(
                image="i1",
                unsigned_rpms=["my-rpm", "another-rpm"],
            ),
            dedent(
                """
                    Found unsigned RPMs in i1:
                    ['my-rpm', 'another-rpm']
                    """
            ).strip(),
            True,
            id="An image with multiple unsigned RPMs Report failure",
        ),
        pytest.param(
            ProcessedImage(
                image="i1",
                unsigned_rpms=[],
                error="Failed to run command",
            ),
            dedent(
                """
                Encountered errors in i1:
                Failed to run command
                """
            ).strip(),
            True,
            id="Error when running command, Report failure",
        ),
    ],
)
def test_generate_output(
    processed_image: ProcessedImage,
    expected_print: str,
    expected_failures_exist: bool,
) -> None:
    """Test generate_output"""
    fail_out, print_out = generate_output(processed_image)
    assert fail_out == expected_failures_exist
    assert print_out == expected_print


class TestImageProcessor:
    """Test ImageProcessor's callable"""

    @pytest.fixture()
    def mock_db_getter(self) -> MagicMock:
        """mocked db_getter function"""
        return MagicMock()

    @pytest.fixture()
    def mock_rpms_getter(self) -> MagicMock:
        """mocked rpms_getter function"""
        return MagicMock()

    @pytest.fixture()
    def mock_unsigned_rpms_getter(self) -> MagicMock:
        """mocked unsigned_rpms_getter function"""
        return MagicMock()

    @pytest.mark.parametrize(
        ("rpms_data", "expected_unsigned"),
        [
            pytest.param([], [], id="No RPMs"),
            pytest.param(
                [
                    "libssh-config-0.9.6-10.el8_8 RSA/SHA256, Tue 6 May , Key ID 1234567890",
                    "python39-twisted-23.10.0-1.el8ap (none)",
                    "libmodulemd-2.13.0-1.el8 RSA/SHA256, Wed 18 Aug , Key ID 1234567890",
                    "gpg-pubkey-d4082792-5b32db75 (none)",
                ],
                ["python39-twisted-23.10.0-1.el8ap"],
                id="one unsigned, two signed",
            ),
        ],
    )
    def test_call(  # pylint: disable=too-many-arguments
        self,
        mock_db_getter: MagicMock,
        expected_unsigned: list[str],
        mock_rpms_getter: MagicMock,
        tmp_path: Path,
        rpms_data: list[str],
    ) -> None:
        """Test ImageProcessor's callable"""
        mock_rpms_getter.return_value = rpms_data
        instance = ImageProcessor(
            workdir=tmp_path,
            db_getter=mock_db_getter,
            rpms_getter=mock_rpms_getter,
        )
        img = "my-img"
        out = instance(img)
        assert out == ProcessedImage(
            image=img,
            unsigned_rpms=expected_unsigned,
            error="",
        )

    def test_call_db_getter_exception(  # pylint: disable=too-many-arguments
        self,
        mock_db_getter: MagicMock,
        mock_rpms_getter: MagicMock,
        mock_unsigned_rpms_getter: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test ImageProcessor exception in db_getter"""
        stderr = "Failed to run command"
        mock_db_getter.side_effect = CalledProcessError(
            stderr=stderr, returncode=1, cmd=""
        )
        instance = ImageProcessor(
            workdir=tmp_path,
            db_getter=mock_db_getter,
            rpms_getter=mock_rpms_getter,
            unsigned_rpms_getter=mock_unsigned_rpms_getter,
        )
        img = "my-img"
        out = instance(img)
        mock_db_getter.assert_called_once()
        mock_rpms_getter.assert_not_called()
        mock_unsigned_rpms_getter.assert_not_called()
        assert out == ProcessedImage(image=img, unsigned_rpms=[], error=stderr)

    def test_call_rpm_getter_exception(  # pylint: disable=too-many-arguments
        self,
        mock_db_getter: MagicMock,
        mock_rpms_getter: MagicMock,
        mock_unsigned_rpms_getter: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test ImageProcessor exception in rpms_getter"""
        stderr = "Failed to run command"
        mock_rpms_getter.side_effect = CalledProcessError(
            stderr=stderr, returncode=1, cmd=""
        )
        instance = ImageProcessor(
            workdir=tmp_path,
            db_getter=mock_db_getter,
            rpms_getter=mock_rpms_getter,
            unsigned_rpms_getter=mock_unsigned_rpms_getter,
        )
        img = "my-img"
        out = instance(img)
        mock_db_getter.assert_called_once()
        mock_rpms_getter.assert_called_once()
        mock_unsigned_rpms_getter.assert_not_called()
        assert out == ProcessedImage(image=img, unsigned_rpms=[], error=stderr)

    def test_call_unsigned_rpms_getter_exception(  # pylint: disable=too-many-arguments
        self,
        mock_db_getter: MagicMock,
        mock_rpms_getter: MagicMock,
        mock_unsigned_rpms_getter: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test ImageProcessor exception in unsigned_rpms_getter"""
        stderr = "Failed to run command"
        mock_unsigned_rpms_getter.side_effect = CalledProcessError(
            stderr=stderr, returncode=1, cmd=""
        )
        instance = ImageProcessor(
            workdir=tmp_path,
            db_getter=mock_db_getter,
            rpms_getter=mock_rpms_getter,
            unsigned_rpms_getter=mock_unsigned_rpms_getter,
        )
        img = "my-img"
        out = instance(img)
        mock_db_getter.assert_called_once()
        mock_rpms_getter.assert_called_once()
        mock_unsigned_rpms_getter.assert_called_once()
        assert out == ProcessedImage(image=img, unsigned_rpms=[], error=stderr)


class TestMain:
    """Test call to rpm_verifier.py main function"""

    @pytest.fixture()
    def mock_image_processor(self, monkeypatch: MonkeyPatch) -> MagicMock:
        """Monkey-patched ImageProcessor"""
        mock: MagicMock = create_autospec(
            ImageProcessor,
            return_value=MagicMock(return_value="some output"),
        )
        monkeypatch.setattr(rpm_verifier, ImageProcessor.__name__, mock)
        return mock

    @pytest.fixture()
    def create_generate_output_mock(
        self, monkeypatch: MonkeyPatch
    ) -> Callable[[bool], MagicMock]:
        """Create a generate_output mock with different results according to
        the `fail_unsigned` flag"""

        def _mock_generate_output(with_failures: bool = False) -> MagicMock:
            """Monkey-patched generate_output"""
            mock = create_autospec(
                generate_output, return_value=(with_failures, "some output")
            )
            monkeypatch.setattr(rpm_verifier, generate_output.__name__, mock)
            return mock

        return _mock_generate_output

    @pytest.mark.parametrize(
        ("fail_unsigned", "has_errors"),
        [
            pytest.param(
                False,
                False,
                id="Should pass if there are errors, and there are errors.",
            ),
            pytest.param(
                False, True, id="Should pass if there are errors, and there are none."
            ),
            pytest.param(
                True, False, id="Should fail if there are errors, and there are none."
            ),
        ],
    )
    def test_main(  # pylint: disable=too-many-arguments
        self,
        create_generate_output_mock: MagicMock,
        mock_image_processor: MagicMock,
        fail_unsigned: bool,
        has_errors: bool,
        tmp_path: Path,
    ) -> None:
        """Test call to rpm_verifier.py main function"""
        status_path = tmp_path / "status"
        generate_output_mock = create_generate_output_mock(with_failures=has_errors)
        rpm_verifier.main(  # pylint: disable=no-value-for-parameter
            args=[
                "--input",
                "img1",
                "--fail-unsigned",
                fail_unsigned,
                "--workdir",
                tmp_path,
            ],
            obj={},
            standalone_mode=False,
        )
        if has_errors:
            assert status_path.read_text() == "ERROR"
        else:
            assert status_path.read_text() == "SUCCESS"
        assert mock_image_processor.return_value.call_count == 1
        generate_output_mock.assert_called_once_with(
            processed_image=mock_image_processor.return_value.return_value
        )
        mock_image_processor.return_value.assert_called_once_with(img="img1")

    def test_main_fail_on_unsigned_rpm_or_errors(
        self,
        create_generate_output_mock: MagicMock,
        mock_image_processor: MagicMock,  # pylint: disable=unused-argument
        tmp_path: Path,
    ) -> None:
        """Test call to rpm_verifier.py main function fails
        when whe 'fail-unsigned' flag is used and there are unsigned RPMs
        """
        status_path = tmp_path / "status"
        fail_unsigned: bool = True
        generate_output_mock = create_generate_output_mock(with_failures=True)
        with pytest.raises(SystemExit) as err:
            rpm_verifier.main(  # pylint: disable=no-value-for-parameter
                args=[
                    "--input",
                    "img1",
                    "--fail-unsigned",
                    fail_unsigned,
                    "--workdir",
                    tmp_path,
                ],
                obj={},
                standalone_mode=False,
            )
        assert status_path.read_text() == "ERROR"
        generate_output_mock.assert_called_once()
        assert err.value.code == generate_output_mock.return_value[1]
