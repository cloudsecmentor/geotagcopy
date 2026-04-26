"""Add GPS recommendations to a legacy metadata CSV."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from geotagcopy.legacy_analysis import main


if __name__ == "__main__":
    raise SystemExit(main())
