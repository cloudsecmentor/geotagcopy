"""Entry point for `python -m geotagcopy`."""

import argparse
import sys

from geotagcopy.app import run_app


def main():
    parser = argparse.ArgumentParser(
        description="GeoTagCopy - Copy GPS tags from geotagged photos to untagged ones"
    )
    parser.add_argument(
        "-t", "--tagged",
        default="",
        help="Path to folder with geotagged (e.g. iPhone) photos",
    )
    parser.add_argument(
        "-u", "--untagged",
        default="",
        help="Path to folder with untagged (e.g. camera) photos",
    )
    args = parser.parse_args()
    run_app(tagged_folder=args.tagged, untagged_folder=args.untagged)


if __name__ == "__main__":
    main()
