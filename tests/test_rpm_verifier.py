"""Test rpm_verifier.py end-to-end"""
from pathlib import Path
from subprocess import CalledProcessError
from textwrap import dedent
from unittest.mock import MagicMock, call, create_autospec, sentinel

import pytest
from pydantic import ValidationError
from pytest import MonkeyPatch

from verify_rpms import rpm_verifier
from verify_rpms.rpm_verifier import (
    ImageProcessor,
    ProcessedImage,
    generate_output,
    get_rpmdb,
    get_unsigned_rpms,
    parse_image_input,
)


@pytest.mark.parametrize(
    ("processed_images", "fail", "expected_print", "expected_fail"),
    [
        pytest.param(
            [ProcessedImage(image="i1", unsigned_rpms=[])],
            False,
            "No unsigned RPMs found.",
            False,
            id="No unsigned RPMs + do not fail if unsigned",
        ),
        pytest.param(
            [
                ProcessedImage(image="i1", unsigned_rpms=[]),
                ProcessedImage(image="i2", unsigned_rpms=[]),
            ],
            True,
            "No unsigned RPMs found.",
            False,
            id="No unsigned RPMs + fail if unsigned",
        ),
        pytest.param(
            [ProcessedImage(image="i1", unsigned_rpms=["my-rpm"])],
            False,
            dedent(
                """
                Found unsigned RPMs:
                i1: my-rpm
                """
            ).strip(),
            False,
            id="1 unsigned + do not fail if unsigned",
        ),
        pytest.param(
            [
                ProcessedImage(image="i1", unsigned_rpms=["my-rpm", "another-rpm"]),
                ProcessedImage(image="i2", unsigned_rpms=[]),
            ],
            True,
            dedent(
                """
                Found unsigned RPMs:
                i1: my-rpm, another-rpm
                """
            ).strip(),
            True,
            id="an image with multiple unsigned and another without + fail if unsigned",
        ),
        pytest.param(
            [
                ProcessedImage(image="i1", unsigned_rpms=["my-rpm", "another-rpm"]),
                ProcessedImage(image="i2", unsigned_rpms=["their-rpm"]),
            ],
            True,
            dedent(
                """
                Found unsigned RPMs:
                i1: my-rpm, another-rpm
                i2: their-rpm
                """
            ).strip(),
            True,
            id="multiple images with unsigned rpms + fail if unsigned",
        ),
        pytest.param(
            [
                ProcessedImage(
                    image="i1", unsigned_rpms=[], error="Failed to run command"
                ),
                ProcessedImage(image="i2", unsigned_rpms=["their-rpm"]),
            ],
            True,
            dedent(
                """
                Found unsigned RPMs:
                i2: their-rpm
                Encountered errors:
                i1: Failed to run command 
                """
            ).strip(),
            True,
            id="Error in running command + image with unsigned rpms + fail if unsigned",
        ),
        pytest.param(
            [
                ProcessedImage(
                    image="i1", unsigned_rpms=[], error="Failed to run first command"
                ),
                ProcessedImage(
                    image="i2", unsigned_rpms=[], error="Failed to run second command"
                ),
            ],
            True,
            dedent(
                """
                Encountered errors:
                i1: Failed to run first command
                i2: Failed to run second command
                """
            ).strip(),
            True,
            id="2 Errors in running command + fail if unsigned",
        ),
        pytest.param(
            [
                ProcessedImage(
                    image="i1", unsigned_rpms=[], error="Failed to run first command"
                ),
                ProcessedImage(
                    image="i2", unsigned_rpms=["my-rpm", "another-rpm"], error=""
                ),
            ],
            False,
            dedent(
                """
                Found unsigned RPMs:
                i2: my-rpm, another-rpm
                Encountered errors:
                i1: Failed to run first command
                """
            ).strip(),
            False,
            id="Errors in running command + image with unsigned rpms + do not fail if unsigned",
        ),
    ],
)
def test_generate_output(
    processed_images: list[ProcessedImage],
    fail: bool,
    expected_print: str,
    expected_fail: bool,
) -> None:
    """Test generate output"""
    fail_out, print_out = generate_output(processed_images, fail)
    assert fail_out == expected_fail
    assert print_out == expected_print


@pytest.mark.parametrize(
    "test_input,expected",
    [
        pytest.param(
            dedent(
                """
                libssh-config-0.9.6-10.el8_8 (none) RSA/SHA256, Tue 6 May , Key ID 1234567890
                python39-twisted-23.10.0-1.el8ap (none) (none)
                libmodulemd-2.13.0-1.el8 (none) RSA/SHA256, Wed 18 Aug , Key ID 1234567890
                gpg-pubkey-d4082792-5b32db75 (none) (none)
                """
            ).strip(),
            ["python39-twisted-23.10.0-1.el8ap"],
            id="Mix of signed and unsigned",
        ),
        pytest.param(
            dedent(
                """
                libssh-config-0.9.6-10.el8_8 (none) RSA/SHA256, Tue 6 May , Key ID 1234567890
                libmodulemd-2.13.0-1.el8 (none) RSA/SHA256, Wed 18 Aug , Key ID 1234567890
                """
            ).strip(),
            [],
            id="All signed",
        ),
        pytest.param("", [], id="Empty list"),
    ],
)
def test_get_unsigned_rpms(test_input: list[str], expected: list[str]) -> None:
    """Test get_unsigned_rpms"""
    mock_runner = MagicMock()
    mock_runner.return_value.stdout = test_input
    result = get_unsigned_rpms(rpmdb=Path("rpmdb_folder"), runner=mock_runner)
    assert result == expected


@pytest.mark.parametrize(
    "test_input,expected",
    [
        pytest.param(
            dedent(
                """
                {
                    "application": "test",
                    "components": [
                        {
                            "containerImage": "quay.io/container-image@sha256:123"
                        },
                        {
                            "containerImage": "quay.io/container-image@sha256:456"
                        },
                        {
                            "containerImage": "quay.io/container-image@sha256:789"
                        }
                    ]
                }
                """
            ).strip(),
            [
                "quay.io/container-image@sha256:123",
                "quay.io/container-image@sha256:456",
                "quay.io/container-image@sha256:789",
            ],
            id="snapshot test",
        ),
        pytest.param(
            "quay.io/container-image@sha256:123",
            ["quay.io/container-image@sha256:123"],
            id="single container",
        ),
    ],
)
def test_parse_image_input(test_input: str, expected: list[str]) -> None:
    """Test parse_image_input"""
    result = parse_image_input(image_input=test_input)
    assert result == expected


def test_parse_image_input_exception() -> None:
    """Test parse_image_input throws exception"""
    test_input = '{"apiVersion": "appstudio.redhat.com/v1alpha1"}'
    with pytest.raises(ValidationError) as ve:
        parse_image_input(image_input=test_input)
    assert [err["type"] for err in ve.value.errors()] == ["missing"]


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

    @pytest.mark.parametrize(
        ("unsigned_rpms",),
        [
            pytest.param([], id="all signed"),
            pytest.param(["my-unsigned-rpm"], id="one unsigned"),
            pytest.param(
                ["my-unsigned-rpm", "their-unsigned-rpm"], id="multiple unsigned"
            ),
        ],
    )
    def test_call(
        self,
        mock_db_getter: MagicMock,
        mock_rpms_getter: MagicMock,
        tmp_path: Path,
        unsigned_rpms: list[str],
    ) -> None:
        """Test ImageProcessor's callable"""
        mock_rpms_getter.return_value = unsigned_rpms
        instance = ImageProcessor(
            workdir=tmp_path,
            db_getter=mock_db_getter,
            rpms_getter=mock_rpms_getter,
        )
        img = "my-img"
        out = instance(img)
        assert out == ProcessedImage(image=img, unsigned_rpms=unsigned_rpms, error="")

    def test_call_db_getter_exception(
        self,
        mock_db_getter: MagicMock,
        mock_rpms_getter: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test ImageProcessor's callable"""
        stderr = "Failed to run command"
        mock_db_getter.side_effect = CalledProcessError(
            stderr=stderr, returncode=1, cmd=""
        )
        instance = ImageProcessor(
            workdir=tmp_path,
            db_getter=mock_db_getter,
            rpms_getter=mock_rpms_getter,
        )
        img = "my-img"
        out = instance(img)
        mock_db_getter.assert_called_once()
        mock_rpms_getter.assert_not_called()
        assert out == ProcessedImage(image=img, unsigned_rpms=[], error=stderr)

    def test_call_rpm_getter_exception(
        self,
        mock_db_getter: MagicMock,
        mock_rpms_getter: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test ImageProcessor's callable"""
        stderr = "Failed to run command"
        mock_rpms_getter.side_effect = CalledProcessError(
            stderr=stderr, returncode=1, cmd=""
        )
        instance = ImageProcessor(
            workdir=tmp_path,
            db_getter=mock_db_getter,
            rpms_getter=mock_rpms_getter,
        )
        img = "my-img"
        out = instance(img)
        mock_db_getter.assert_called_once()
        mock_rpms_getter.assert_called_once()
        assert out == ProcessedImage(image=img, unsigned_rpms=[], error=stderr)


def test_get_rpmdb(tmp_path: Path) -> None:
    """Test get_rpmdb"""
    image = "my-image"
    mock_runner = MagicMock()
    out = get_rpmdb(
        container_image=image,
        target_dir=tmp_path,
        runner=mock_runner,
    )
    assert mock_runner.call_count == 1
    assert out == tmp_path


class TestMain:
    """Test call to rpm_verifier.py main function"""

    @pytest.fixture()
    def mock_image_processor(self, monkeypatch: MonkeyPatch) -> MagicMock:
        """Monkey-patched ImageProcessor"""
        mock: MagicMock = create_autospec(
            ImageProcessor,
            return_value=MagicMock(return_value=sentinel.output),
        )
        monkeypatch.setattr(rpm_verifier, ImageProcessor.__name__, mock)
        return mock

    @pytest.fixture()
    def mock_generate_output(self, monkeypatch: MonkeyPatch) -> MagicMock:
        """Monkey-patched generate_output"""
        mock = create_autospec(generate_output, return_value=(False, ""))
        monkeypatch.setattr(rpm_verifier, generate_output.__name__, mock)
        return mock

    def test_main(
        self,
        mock_generate_output: MagicMock,
        mock_image_processor: MagicMock,
    ) -> None:
        """Test call to rpm_verifier.py main function"""
        rpm_verifier.main(  # pylint: disable=no-value-for-parameter
            args=[
                "--input",
                "img1",
                "--fail-unsigned",
                "true",
                "--workdir",
                "some/path",
            ],
            obj={},
            standalone_mode=False,
        )

        assert mock_image_processor.return_value.call_count == 1
        mock_image_processor.return_value.assert_has_calls([call("img1")])
        mock_generate_output.assert_called_once_with([sentinel.output], True)
