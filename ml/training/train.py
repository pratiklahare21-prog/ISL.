"""
Trains the sign sequence classifier on collected landmark data and saves
a checkpoint that apps/ml-service loads for live inference.

Run from the ml/training/ directory (after activating your venv and
installing apps/ml-service/requirements.txt, since this reuses that
package's model + label code):

    python train.py --epochs 60 --batch-size 16

This is CPU-friendly by design (see architecture.py's docstring) — on an
Intel Core Ultra 5 laptop this should train in a few minutes for a
few-thousand-sample dataset. No CUDA/GPU required or used.
"""

import argparse
import sys
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, random_split

ML_SERVICE_ROOT = Path(__file__).resolve().parents[2] / "apps" / "ml-service"
sys.path.insert(0, str(ML_SERVICE_ROOT))
from app.core.labels import NUM_CLASSES  # noqa: E402
from app.core.landmarks import FEATURE_VECTOR_SIZE  # noqa: E402
from app.models.architecture import SignSequenceClassifier  # noqa: E402

from dataset import LandmarkSequenceDataset  # noqa: E402

OUTPUT_DIR = Path(__file__).resolve().parents[1] / "models_out"


def train(epochs: int, batch_size: int, lr: float, val_split: float):
    dataset = LandmarkSequenceDataset(min_samples_per_label=5)
    print(dataset.summary())
    print()

    val_size = max(1, int(len(dataset) * val_split))
    train_size = len(dataset) - val_size
    train_ds, val_ds = random_split(dataset, [train_size, val_size])

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False)

    device = torch.device("cpu")  # Intel Arc iGPU has no torch CUDA backend;
    # CPU is the correct, reliable target here (see architecture.py notes).
    model = SignSequenceClassifier(
        input_size=FEATURE_VECTOR_SIZE, num_classes=NUM_CLASSES
    ).to(device)

    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-5)
    label_tensor = torch.tensor(dataset.labels, dtype=torch.long)
    class_counts = torch.bincount(label_tensor, minlength=NUM_CLASSES).float()
    present = class_counts > 0
    class_weights = torch.zeros(NUM_CLASSES, dtype=torch.float32)
    class_weights[present] = (
        class_counts[present].sum() / (present.sum() * class_counts[present])
    ).sqrt()
    criterion = nn.CrossEntropyLoss(weight=class_weights.to(device))
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="min", factor=0.5, patience=5
    )

    best_val_acc = 0.0
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    checkpoint_path = OUTPUT_DIR / "isl_model.pt"

    for epoch in range(1, epochs + 1):
        model.train()
        total_loss = 0.0
        for x, y in train_loader:
            x, y = x.to(device), y.to(device)
            optimizer.zero_grad()
            logits = model(x)
            loss = criterion(logits, y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item() * x.size(0)
        train_loss = total_loss / len(train_ds)

        model.eval()
        correct, total, val_loss_sum = 0, 0, 0.0
        with torch.no_grad():
            for x, y in val_loader:
                x, y = x.to(device), y.to(device)
                logits = model(x)
                val_loss_sum += criterion(logits, y).item() * x.size(0)
                preds = torch.argmax(logits, dim=-1)
                correct += (preds == y).sum().item()
                total += y.size(0)
        val_loss = val_loss_sum / max(1, len(val_ds))
        val_acc = correct / max(1, total)
        scheduler.step(val_loss)

        print(
            f"Epoch {epoch:3d}/{epochs} | train_loss={train_loss:.4f} "
            f"| val_loss={val_loss:.4f} | val_acc={val_acc:.3f}"
        )

        if val_acc >= best_val_acc:
            best_val_acc = val_acc
            torch.save(model.state_dict(), checkpoint_path)

    print(f"\nBest val accuracy: {best_val_acc:.3f}")
    print(f"Checkpoint saved to: {checkpoint_path}")
    print("Restart apps/ml-service (or it'll pick it up on next request if")
    print("the process was started after this checkpoint existed) to use it.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=60)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--val-split", type=float, default=0.15)
    args = parser.parse_args()

    train(args.epochs, args.batch_size, args.lr, args.val_split)
