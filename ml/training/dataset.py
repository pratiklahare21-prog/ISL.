"""
Loads all recorded .npy sample files from ml/data/raw/ into a single
PyTorch Dataset, ready for train/val split and DataLoader use.
"""

import sys
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import Dataset

ML_SERVICE_ROOT = Path(__file__).resolve().parents[2] / "apps" / "ml-service"
sys.path.insert(0, str(ML_SERVICE_ROOT))
from app.core.labels import ALL_SIGN_LABELS, LABEL_TO_INDEX  # noqa: E402
from app.core.landmarks import normalize_feature_vector  # noqa: E402

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"


class LandmarkSequenceDataset(Dataset):
    def __init__(self, min_samples_per_label: int = 1):
        self.samples: list[np.ndarray] = []
        self.labels: list[int] = []
        self.label_counts: dict[str, int] = {}

        for label in ALL_SIGN_LABELS:
            path = DATA_DIR / f"{label}.npy"
            if not path.exists():
                continue
            arr = np.load(path)  # (N, WINDOW_SIZE, 126)
            if arr.shape[0] < min_samples_per_label:
                continue
            self.label_counts[label] = arr.shape[0]
            for i in range(arr.shape[0]):
                sample = arr[i]
                if not np.any(sample):
                    continue
                normalized = np.stack(
                    [normalize_feature_vector(frame) for frame in sample],
                    axis=0,
                )
                self.samples.append(normalized)
                self.labels.append(LABEL_TO_INDEX[label])

        if not self.samples:
            raise RuntimeError(
                "No training data found. Run ml/dataset_tool/collect.py first "
                "to record samples into ml/data/raw/."
            )

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        x = torch.from_numpy(self.samples[idx]).float()
        y = torch.tensor(self.labels[idx], dtype=torch.long)
        return x, y

    def summary(self) -> str:
        lines = [f"Loaded {len(self.samples)} samples across {len(self.label_counts)} labels:"]
        for label, count in sorted(self.label_counts.items()):
            lines.append(f"  {label}: {count}")
        missing = [l for l in ALL_SIGN_LABELS if l not in self.label_counts]
        if missing:
            lines.append(f"Labels with NO data (will be untrainable): {missing}")
        return "\n".join(lines)
