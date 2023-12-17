#!/usr/bin/env python3

"""Verify RPMs are signed"""

import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from subprocess import run
from typing import Callable, Iterable

import click


@dataclass(frozen=True)
class ProcessedImage:
    """Unsigned RPMs for a single image"""

    image: str
    unsigned_rpms: list[str]

    def __str__(self) -> str:
        return f"image: {self. image} | unsigned RPMs: {', '.join(self.unsigned_rpms)}"


def get_rpmdb(container_image: str, target_dir: Path, runner: Callable = run) -> Path:
    """Extract RPM DB from a given container image reference"""
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


def get_unsigned_rpms(rpmdb: Path, runner: Callable = run) -> list[str]:
    """Get unsigned RPMs from RPM DB path"""
    raise NotImplementedError()


def generate_output(
    processed_images: Iterable[ProcessedImage], fail_unsigned: bool
) -> tuple[bool, str]:
    """
    Generate the output that should be printed to the user based on the processed images
    and decide whether the script should fail or not

    :param processed_images: each element contains a name and a list of unsigned images
    :param fail_unsigned: whether the script should fail in case unsigned rpms found
    """
    with_unsigned_rpms = [img for img in processed_images if img.unsigned_rpms]
    if not with_unsigned_rpms:
        output = "No unsigned RPMs found."
        fail = False
    else:
        output = "\n".join([str(img) for img in with_unsigned_rpms])
        output = f"Found unsigned RPMs:\n{output}"
        fail = fail_unsigned
    return fail, output


def parse_image_input(image_input: str) -> list[str]:
    """
    Input is either an image reference or snapshot data in json format.
    Try parsing as json and extract the images.
    If failing to parse as json, assume it's an image reference as one-element list.
    """
    # Currently assuming a single image. To be replaced by deciding whether this is an
    # image or a snapshot json, and parsing accordingly
    return [image_input]


@dataclass(frozen=True)
class ImageProcessor:
    """Find unsigned RPMs provided an image"""

    workdir: Path
    db_getter: Callable[[str, Path], Path] = get_rpmdb
    rpms_getter: Callable[[Path], list[str]] = get_unsigned_rpms

    def __call__(self, img: str) -> ProcessedImage:
        with tempfile.TemporaryDirectory(
            dir=str(self.workdir), prefix="rpmdb"
        ) as tmpdir:
            rpm_db = self.db_getter(img, Path(tmpdir))
            unsigned_rpms = self.rpms_getter(rpm_db)
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
    help="Exit with failure if unsigned RPMs found",
    type=bool,
    required=True,
)
@click.option(
    "--workdir",
    help="Path in which temporary directories will be created",
    type=click.Path(path_type=Path),
    required=True,
)
def main(img_input: str, fail_unsigned: bool, workdir: Path) -> None:
    """Verify RPMs are signed"""

    container_images = parse_image_input(img_input)

    processor = ImageProcessor(workdir=workdir)
    with ThreadPoolExecutor() as executor:
        processed_images: Iterable[ProcessedImage] = executor.map(
            processor, container_images
        )

    fail, output = generate_output(list(processed_images), fail_unsigned)
    if fail:
        sys.exit(output)
    print(output)


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
