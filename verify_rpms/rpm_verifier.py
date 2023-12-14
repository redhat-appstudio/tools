#!/usr/bin/env python3

"""Verify RPMs are signed"""

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


def get_rpmdb(container_image: str, target_dir: Path, runner: Callable = run) -> Path:
    """Extract RPM DB from a given container image reference"""
    raise NotImplementedError()


def get_unsigned_rpms(rpmdb: Path, runner: Callable = run) -> list[str]:
    """Get unsigned RPMs from RPM DB path"""
    raise NotImplementedError()


def generate_output(
    unsigned_rpms: Iterable[ProcessedImage], fail_unsigned: bool
) -> None:
    """
    Given a mapping between images and unsigned RPMs, print out the images
    having unsigned RPMs, together with their unsigned RPMs.
    Exit with error in case unsigned RPMs found and the relevant flag provided.
    """
    raise NotImplementedError()


@dataclass(frozen=True)
class ImageProcessor:
    """Find unsigned RPMs provided an image"""

    db_getter: Callable[[str, Path], Path] = get_rpmdb
    rpms_getter: Callable[[Path], list[str]] = get_unsigned_rpms

    def __call__(self, img: str) -> ProcessedImage:
        with tempfile.TemporaryDirectory(prefix="tmprpmdb") as tmpdir:
            rpm_db = self.db_getter(img, Path(tmpdir))
            unsigned_rpms = self.rpms_getter(rpm_db)
            return ProcessedImage(
                image=img,
                unsigned_rpms=unsigned_rpms,
            )


@click.command()
@click.option(
    "--container-image",
    help="Reference to container image",
    type=str,
    multiple=True,
)
@click.option(
    "--fail-unsigned",
    help="Exit with failure if unsigned RPMs found",
    type=bool,
    is_flag=True,
)
def main(container_image: list[str], fail_unsigned: bool) -> None:
    """Verify RPMs are signed"""
    processor = ImageProcessor()
    with ThreadPoolExecutor() as executor:
        processed_images: Iterable[ProcessedImage] = executor.map(
            processor, container_image
        )

    generate_output(list(processed_images), fail_unsigned)


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
