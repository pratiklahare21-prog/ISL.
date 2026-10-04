"""
Prints how many samples you've recorded per label so far, and which
labels still need data.

    python check_progress.py
    python check_progress.py --min 40
"""

import argparse
import sys
from pathlib import Path

import numpy as np

ML_SERVICE_ROOT = Path(__file__).resolve().parents[2] / "apps" / "ml-service"
sys.path.insert(0, str(ML_SERVICE_ROOT))
from app.core.labels import ALL_SIGN_LABELS  # noqa: E402

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--min", type=int, default=30, help="Target samples per label")
    args = parser.parse_args()

    print(f"{'LABEL':<16}{'SAMPLES':<10}STATUS")
    print("-" * 40)
    missing = []
    below_target = []

    for label in ALL_SIGN_LABELS:
        path = DATA_DIR / f"{label}.npy"
        if not path.exists():
            print(f"{label:<16}{0:<10}❌ none")
            missing.append(label)
            continue
        arr = np.load(path)
        count = arr.shape[0]
        status = "✅ ok" if count >= args.min else f"⚠️  need {args.min - count} more"
        if count < args.min:
            below_target.append(label)
        print(f"{label:<16}{count:<10}{status}")

    print("\nSummary:")
    print(f"  {len(ALL_SIGN_LABELS) - len(missing)}/{len(ALL_SIGN_LABELS)} labels have at least some data")
    print(f"  {len(missing)} labels have NO data yet: {missing}")
    print(f"  {len(below_target)} labels are below the target of {args.min} samples")


if __name__ == "__main__":
    main()
