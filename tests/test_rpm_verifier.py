"""Test rpm_verifier.py end-to-end"""

from pathlib import Path
from textwrap import dedent
from unittest.mock import MagicMock, call, create_autospec, sentinel

import pytest
from pytest import MonkeyPatch

from verify_rpms import rpm_verifier
from verify_rpms.rpm_verifier import (
    ImageProcessor,
    ProcessedImage,
    generate_output,
    get_rpmdb,
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
                image: i1 | unsigned RPMs: my-rpm
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
                image: i1 | unsigned RPMs: my-rpm, another-rpm
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
                image: i1 | unsigned RPMs: my-rpm, another-rpm
                image: i2 | unsigned RPMs: their-rpm
                """
            ).strip(),
            True,
            id="multiple images with unsigned rpms + fail if unsigned",
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


class TestImageProcessor:
    """Test ImageProcessor's callable"""

    @pytest.fixture()
    def mock_db_getter(self) -> MagicMock:
        "mocked db_getter function"
        return MagicMock()

    @pytest.fixture()
    def mock_rpms_getter(self) -> MagicMock:
        "mocked rpms_getter function"
        return MagicMock()

    @pytest.mark.parametrize(
        ("unsigned_rpms"),
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
        assert out == ProcessedImage(image=img, unsigned_rpms=unsigned_rpms)


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
