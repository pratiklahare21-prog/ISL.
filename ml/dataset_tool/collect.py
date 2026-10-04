"""
Interactive webcam tool to record training samples for the ISL model.

WHY THIS EXISTS: there is no reliable public ISL landmark dataset covering
this label set. You must record your own samples. This tool makes that
fast and consistent with how the ml-service extracts features at
inference time (same LandmarkExtractor code is reused, so training and
serving are guaranteed to match).

HOW TO USE
----------
    python collect.py --label A --samples 40
    python collect.py --label HELLO --samples 40 --dynamic

For STATIC signs (alphabet, digits): each sample is a short window
(WINDOW_SIZE frames) recorded while you hold the hand shape steady.
For DYNAMIC signs (words): each sample is a window recorded while you
perform the full motion once, start to finish.

CONTROLS (while webcam window is focused):
    SPACE  - start recording one sample (records exactly WINDOW_SIZE frames)
    Q      - quit early

Samples are appended to ml/data/raw/<label>.npy as an array of shape
(num_samples, WINDOW_SIZE, 126). Re-running the tool for a label that
already has data appends more samples rather than overwriting.

TIPS FOR GOOD DATA (this directly determines model accuracy):
  - Vary hand position slightly across samples (a bit left/right/closer/
    further from camera) so the model generalizes instead of memorizing
    one exact position.
  - Keep consistent lighting; avoid strong backlight.
  - For dynamic/word signs, vary your speed slightly across samples.
  - Aim for at least 30-50 samples per label; more (80-100) for word
    signs, since those have more motion variability.
"""

import argparse
import sys
import time
from pathlib import Path

import cv2
import numpy as np

# Make the ml-service's landmark extractor importable from here so
# training-time feature extraction is byte-for-byte identical to
# inference-time feature extraction.
ML_SERVICE_ROOT = Path(__file__).resolve().parents[2] / "apps" / "ml-service"
sys.path.insert(0, str(ML_SERVICE_ROOT))

# The app package is added to sys.path at runtime, which the editor's
# static resolver does not reliably infer. Suppress the missing-import
# warning without changing the runtime behavior.
from app.core.landmarks import LandmarkExtractor  # type: ignore[import-not-found]  # noqa: E402
from app.core.labels import ALL_SIGN_LABELS  # type: ignore[import-not-found]  # noqa: E402

WINDOW_SIZE = 24  # must match apps/ml-service/app/core/inference.py WINDOW_SIZE
DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"


def record_one_sample(cap, extractor) -> np.ndarray | None:
    """Records exactly WINDOW_SIZE frames starting now. Returns None if
    the user quits mid-recording."""
    frames = []
    while len(frames) < WINDOW_SIZE:
        ok, frame = cap.read()
        if not ok:
            continue
        frame = cv2.flip(frame, 1)  # mirror, feels natural to the signer
        landmarks = extractor.process(frame)
        feature = landmarks.to_feature_vector()
        frames.append(feature)

        display = frame.copy()
        progress = len(frames) / WINDOW_SIZE
        cv2.rectangle(display, (0, 0), (int(display.shape[1] * progress), 10), (0, 200, 0), -1)
        cv2.putText(
            display, "RECORDING...", (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2,
        )
        cv2.imshow("ISL Dataset Collector", display)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            return None

    return np.stack(frames, axis=0)  # (WINDOW_SIZE, 126)


def main():
    parser = argparse.ArgumentParser(description="Record ISL sign samples.")
    parser.add_argument("--label", required=True, help=f"One of: {', '.join(ALL_SIGN_LABELS)}")
    parser.add_argument("--samples", type=int, default=40, help="Number of samples to record")
    parser.add_argument("--camera", type=int, default=0, help="Camera index")
    args = parser.parse_args()

    label = args.label.upper()
    if label not in ALL_SIGN_LABELS:
        print(f"⚠️  '{label}' is not in the known label list.")
        print(f"   Known labels: {ALL_SIGN_LABELS}")
        print("   (Edit packages/shared/src/constants/signs.ts AND")
        print("    apps/ml-service/app/core/labels.py to add a new label,")
        print("    keeping both files in sync, before collecting for it.)")
        return

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out_path = DATA_DIR / f"{label}.npy"

    existing = np.load(out_path) if out_path.exists() else None
    existing_count = existing.shape[0] if existing is not None else 0
    print(f"Label: {label} | existing samples: {existing_count} | recording {args.samples} more")

    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        print("❌ Could not open webcam. Try a different --camera index.")
        return

    extractor = LandmarkExtractor()
    collected = []

    print("\nControls: SPACE = record one sample | Q = quit\n")

    try:
        while len(collected) < args.samples:
            ok, frame = cap.read()
            if not ok:
                continue
            frame = cv2.flip(frame, 1)
            display = frame.copy()
            cv2.putText(
                display,
                f"{label}: {len(collected)}/{args.samples} | SPACE=record Q=quit",
                (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2,
            )
            cv2.imshow("ISL Dataset Collector", display)
            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                break
            if key == ord(" "):
                print(f"Recording sample {len(collected) + 1}...")
                # Give the signer time to form the posture after pressing Space.
                for countdown in (3, 2, 1):
                    ok, countdown_frame = cap.read()
                    if not ok:
                        continue
                    countdown_frame = cv2.flip(countdown_frame, 1)
                    cv2.putText(
                        countdown_frame,
                        f"GET READY: {countdown}",
                        (20, 80),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1.2,
                        (0, 165, 255),
                        3,
                    )
                    cv2.imshow("ISL Dataset Collector", countdown_frame)
                    if cv2.waitKey(1000) & 0xFF == ord("q"):
                        return
                sample = record_one_sample(cap, extractor)
                if sample is None:
                    break
                collected.append(sample)
                print(f"  ✓ captured ({len(collected)}/{args.samples})")

    finally:
        cap.release()
        cv2.destroyAllWindows()
        extractor.close()

    if not collected:
        print("No samples recorded.")
        return

    new_data = np.stack(collected, axis=0)  # (N, WINDOW_SIZE, 126)
    if existing is not None:
        combined = np.concatenate([existing, new_data], axis=0)
    else:
        combined = new_data

    np.save(out_path, combined)
    print(f"\n✅ Saved {new_data.shape[0]} new samples ({combined.shape[0]} total) to {out_path}")


if __name__ == "__main__":
    main()
