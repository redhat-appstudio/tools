#!/usr/bin/env python3

"""Verify RPMs are signed"""
import json
import sys
import tempfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from subprocess import CalledProcessError, run
from typing import Any, Callable

import click


@dataclass(frozen=True)
class ProcessedImage:
    """
    A class to hold data about rpms for single image:
    Image name,
    Unsigned RPMs,
    Keys used to sign RPMs,
    Errors
    """

    image: str
    unsigned_rpms: list[str]
    signed_rpms_keys: list[str]
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


def get_signed_rpms_keys(rpms: list[str]) -> list[str]:
    """
    Get the keys used to sign RPMs
    :param rpms: list of RPMs
    :return: list of keys used to sign RPMs
    """
    signed_rpms_keys: list[str] = [
        rpm.split(", Key ID ")[-1] for rpm in rpms if "Key ID" in rpm
    ]
    return signed_rpms_keys


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


def generate_results(
    processed_image: ProcessedImage,
) -> dict[str, Any]:
    """
    Generate the results that should be added to the results of the task
    :param processed_image: ProcessedImage that contains all the rpms information
    :returns: dictionary with results for the image
    """
    results: dict[str, Any] = {}
    if processed_image.error != "":
        results["error"] = processed_image.error
    else:
        results["keys"] = dict(Counter(processed_image.signed_rpms_keys).most_common())
        results["keys"]["unsigned"] = len(processed_image.unsigned_rpms)
    return results


@dataclass(frozen=True)
class ImageProcessor:
    """
    Populate RPMs data for an image
    """

    workdir: Path
    db_getter: Callable[[str, Path], Path] = get_rpmdb
    rpms_getter: Callable[[Path], list[str]] = get_rpms_data
    unsigned_rpms_getter: Callable[[list[str]], list[str]] = get_unsigned_rpms
    signed_rpms_keys_getter: Callable[[list[str]], list[str]] = get_signed_rpms_keys

    def __call__(self, img: str) -> ProcessedImage:
        with tempfile.TemporaryDirectory(
            dir=str(self.workdir), prefix="rpmdb"
        ) as tmpdir:
            try:
                rpms_db = self.db_getter(img, Path(tmpdir))
                rpms_data = self.rpms_getter(rpms_db)
                unsigned_rpms = self.unsigned_rpms_getter(rpms_data)
                signed_rpms_keys = self.signed_rpms_keys_getter(rpms_data)
            except CalledProcessError as err:
                return ProcessedImage(
                    image=img,
                    unsigned_rpms=[],
                    signed_rpms_keys=[],
                    error=err.stderr,
                )
            return ProcessedImage(
                image=img,
                unsigned_rpms=unsigned_rpms,
                signed_rpms_keys=signed_rpms_keys,
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
    results_path: Path = workdir / "results"

    processor = ImageProcessor(workdir=workdir)
    processed_image = processor(img=img_input)

    failures_occurred, output = generate_output(processed_image=processed_image)
    results = generate_results(processed_image=processed_image)
    results_path.write_text(json.dumps(results))
    if failures_occurred:
        status_path.write_text("ERROR")
    else:
        status_path.write_text("SUCCESS")
    if failures_occurred and fail_unsigned:
        sys.exit(output + "\n" + json.dumps(results))
    print(output)
    print(json.dumps(results))


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
