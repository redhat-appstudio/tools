#!/usr/bin/env python3

"""Verify RPMs are signed"""
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from subprocess import CalledProcessError, run
from typing import Callable

import click


@dataclass(frozen=True)
class ProcessedImage:
    """
    A class to hold data about rpms for single image:
    Image name,
    Unsigned RPMs,
    Errors
    """

    image: str
    unsigned_rpms: list[str]
    error: str = ""

    def __str__(self) -> str:
        return f"{self.image}: {', '.join(self.unsigned_rpms)}"


def get_rpmdb(container_image: str, target_dir: Path, runner: Callable = run) -> Path:
    """
    Extract RPM DB from a given container image reference
    :param container_image: the image to extract
    :param target_dir: the directory to extract the DB to
    :param runner: subprocess.run to run CLI commands
    :return: Path of the directory the DB extracted to
    """
    runner(
        [
            "oc",
            "image",
            "extract",
            container_image,
            "--path",
            f"/var/lib/rpm/:{target_dir}",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return target_dir


def get_rpms_data(rpmdb: Path, runner: Callable = run) -> list[str]:
    """
    Get RPMs data from RPM DB
    :param rpmdb: path to RPM DB folder
    :param runner: subprocess.run to run CLI commands
    :return: list of RPMs with their signature information
    """
    rpm_strs = runner(
        [  # pylint: disable=duplicate-code
            "rpm",
            "-qa",
            "--qf",
            "%{NAME}-%{VERSION}-%{RELEASE} %{SIGPGP:pgpsig}\n",
            "--dbpath",
            str(rpmdb),
        ],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()
    return rpm_strs


def get_unsigned_rpms(rpms: list[str]) -> list[str]:
    """
    Get all unsigned RPMs from the list of RPMs
    Filters out the `gpg-pubkey` and return the unsigned RPMs
    :param rpms: list of RPMs
    :return: list of unsigned RPMs
    """
    unsigned_rpms: list[str] = [
        rpm.split()[0]
        for rpm in rpms
        if "Key ID" not in rpm and not rpm.startswith("gpg-pubkey")
    ]

    return unsigned_rpms


def generate_output(processed_image: ProcessedImage) -> tuple[bool, str]:
    """
    Generate the output that should be printed to the user based on the processed images
    results.
    :param processed_image: ProcessedImage that contains all the rpms information
    :returns: The status and summary of the image processing.
    """
    failure = True

    if not processed_image.unsigned_rpms and not processed_image.error:
        output = f"No unsigned RPMs in {processed_image.image}"
        failure = False
    else:
        output = (
            f"Found unsigned RPMs in {processed_image.image}:\n{processed_image.unsigned_rpms}"
            if processed_image.unsigned_rpms
            else f"Encountered errors in {processed_image.image}:\n{processed_image.error}"
        )
    return failure, output.lstrip()


@dataclass(frozen=True)
class ImageProcessor:
    """
    Populate RPMs data for all images
    """

    workdir: Path
    db_getter: Callable[[str, Path], Path] = get_rpmdb
    rpms_getter: Callable[[Path], list[str]] = get_rpms_data
    unsigned_rpms_getter: Callable[[list[str]], list[str]] = get_unsigned_rpms

    def __call__(self, img: str) -> ProcessedImage:
        with tempfile.TemporaryDirectory(
            dir=str(self.workdir), prefix="rpmdb"
        ) as tmpdir:
            try:
                rpms_db = self.db_getter(img, Path(tmpdir))
                rpms_data = self.rpms_getter(rpms_db)
                unsigned_rpms = self.unsigned_rpms_getter(rpms_data)
            except CalledProcessError as err:
                return ProcessedImage(
                    image=img,
                    unsigned_rpms=[],
                    error=err.stderr,
                )
            return ProcessedImage(
                image=img,
                unsigned_rpms=unsigned_rpms,
            )


@click.command()
@click.option(
    "--input",
    "img_input",
    help="Reference to container image",
    type=str,
    required=True,
)
@click.option(
    "--fail-unsigned",
    help="Exit with failure if unsigned RPMs or other errors were found",
    type=bool,
    required=True,
)
@click.option(
    "--workdir",
    help="Path in which temporary directories will be created",
    type=click.Path(path_type=Path),
    required=True,
)
def main(
    img_input: str,
    fail_unsigned: bool,
    workdir: Path,
) -> None:
    """Verify RPMs are signed"""
    status_path: Path = workdir / "status"
    processor = ImageProcessor(workdir=workdir)
    processed_image = processor(img=img_input)

    failures_occurred, output = generate_output(processed_image=processed_image)
    if failures_occurred:
        status_path.write_text("ERROR")
    else:
        status_path.write_text("SUCCESS")
    if failures_occurred and fail_unsigned:
        sys.exit(output)
    print(output)


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
