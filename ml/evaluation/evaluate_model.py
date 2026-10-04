"""
Model Evaluation Script

Evaluates the trained ISL model on test data and generates accuracy metrics.

Usage:
    python evaluate_model.py

Outputs:
    - Overall accuracy
    - Per-class accuracy
    - Precision, Recall, F1-score
    - Confusion matrix (saved to evaluation_results/)
    - Classification report
"""

import sys
import json
from pathlib import Path
from collections import defaultdict
import time

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Subset
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    confusion_matrix,
    classification_report
)

# Add ml-service to path
ML_SERVICE_ROOT = Path(__file__).resolve().parents[2] / "apps" / "ml-service"
sys.path.insert(0, str(ML_SERVICE_ROOT))

from app.core.labels import NUM_CLASSES, ALL_SIGN_LABELS, INDEX_TO_LABEL
from app.core.landmarks import FEATURE_VECTOR_SIZE
from app.models.architecture import SignSequenceClassifier

# Import training dataset
TRAINING_ROOT = Path(__file__).resolve().parent.parent / "training"
sys.path.insert(0, str(TRAINING_ROOT))
from dataset import LandmarkSequenceDataset

MODEL_PATH = Path(__file__).resolve().parents[1] / "models_out" / "isl_model.pt"
RESULTS_DIR = Path(__file__).resolve().parent / "evaluation_results"


def evaluate_model():
    """Main evaluation function"""
    
    print("="*60)
    print("ISL Model Evaluation")
    print("="*60)
    print()
    
    # Check if model exists
    if not MODEL_PATH.exists():
        print(f"❌ Model not found at: {MODEL_PATH}")
        print("Train a model first: cd ml/training && python train.py")
        return None
    
    print(f"✓ Loading model from: {MODEL_PATH}")
    
    # Load model
    device = torch.device("cpu")
    model = SignSequenceClassifier(
        input_size=FEATURE_VECTOR_SIZE,
        num_classes=NUM_CLASSES
    ).to(device)
    
    try:
        state = torch.load(MODEL_PATH, map_location=device)
        model.load_state_dict(state)
        model.eval()
        print("✓ Model loaded successfully")
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        return None
    
    # Load dataset
    print()
    print("Loading dataset...")
    try:
        dataset = LandmarkSequenceDataset(min_samples_per_label=1)
        print(dataset.summary())
    except RuntimeError as e:
        print(f"❌ {e}")
        return None
    
    if len(dataset) == 0:
        print("❌ No data available for evaluation")
        return None
    
    # Use 20% of data as test set (or min 1 sample per class)
    test_size = max(len(dataset) // 5, 1)
    # Use last samples as test (assuming chronological order)
    test_indices = list(range(len(dataset) - test_size, len(dataset)))
    test_dataset = Subset(dataset, test_indices)
    
    test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False)
    
    print(f"\n✓ Using {len(test_dataset)} samples for evaluation")
    print()
    
    # Evaluate
    print("Running inference...")
    all_preds = []
    all_labels = []
    all_confidences = []
    
    start_time = time.time()
    
    with torch.no_grad():
        for x, y in test_loader:
            x, y = x.to(device), y.to(device)
            logits = model(x)
            probs = torch.softmax(logits, dim=-1)
            preds = torch.argmax(logits, dim=-1)
            confidences = torch.max(probs, dim=-1)[0]
            
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(y.cpu().numpy())
            all_confidences.extend(confidences.cpu().numpy())
    
    inference_time = time.time() - start_time
    avg_latency = (inference_time / len(test_dataset)) * 1000  # ms per sample
    
    # Convert to numpy arrays
    all_preds = np.array(all_preds)
    all_labels = np.array(all_labels)
    all_confidences = np.array(all_confidences)
    
    # Calculate metrics
    print("="*60)
    print("EVALUATION RESULTS")
    print("="*60)
    print()
    
    # Overall accuracy
    overall_acc = accuracy_score(all_labels, all_preds)
    print(f"Overall Accuracy: {overall_acc:.4f} ({overall_acc*100:.2f}%)")
    print()
    
    # Precision, Recall, F1
    precision, recall, f1, support = precision_recall_fscore_support(
        all_labels, all_preds, average='weighted', zero_division=0
    )
    
    print(f"Weighted Precision: {precision:.4f}")
    print(f"Weighted Recall:    {recall:.4f}")
    print(f"Weighted F1-Score:  {f1:.4f}")
    print()
    
    # Average confidence
    avg_confidence = np.mean(all_confidences)
    print(f"Average Confidence: {avg_confidence:.4f}")
    print()
    
    # Performance metrics
    print(f"Average Inference Latency: {avg_latency:.2f} ms per sample")
    print(f"Throughput: {1000/avg_latency:.1f} samples/second")
    print()
    
    # Per-class accuracy
    print("Per-Class Accuracy:")
    print("-"*60)
    
    # Get unique classes in test set
    unique_labels = np.unique(all_labels)
    class_accuracies = {}
    
    for label_idx in unique_labels:
        mask = all_labels == label_idx
        if mask.sum() > 0:
            class_acc = accuracy_score(all_labels[mask], all_preds[mask])
            label_name = INDEX_TO_LABEL.get(label_idx, f"Unknown_{label_idx}")
            class_accuracies[label_name] = class_acc
            correct = (all_preds[mask] == all_labels[mask]).sum()
            total = mask.sum()
            print(f"  {label_name:15} {class_acc:.4f} ({correct}/{total})")
    
    print()
    
    # Confusion Matrix
    print("Generating confusion matrix...")
    cm = confusion_matrix(all_labels, all_preds)
    
    # Save results
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save detailed results
    results = {
        "overall_accuracy": float(overall_acc),
        "weighted_precision": float(precision),
        "weighted_recall": float(recall),
        "weighted_f1": float(f1),
        "average_confidence": float(avg_confidence),
        "avg_latency_ms": float(avg_latency),
        "throughput_samples_per_sec": float(1000/avg_latency),
        "test_samples": len(test_dataset),
        "per_class_accuracy": {k: float(v) for k, v in class_accuracies.items()},
        "model_path": str(MODEL_PATH),
        "evaluation_date": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    results_file = RESULTS_DIR / "evaluation_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"✓ Saved detailed results to: {results_file}")
    
    # Save confusion matrix
    cm_file = RESULTS_DIR / "confusion_matrix.npy"
    np.save(cm_file, cm)
    print(f"✓ Saved confusion matrix to: {cm_file}")
    
    # Generate classification report
    label_names = [INDEX_TO_LABEL.get(i, f"Class_{i}") for i in unique_labels]
    report = classification_report(
        all_labels,
        all_preds,
        target_names=label_names,
        zero_division=0
    )
    
    report_file = RESULTS_DIR / "classification_report.txt"
    with open(report_file, 'w') as f:
        f.write("ISL Model - Classification Report\n")
        f.write("="*60 + "\n\n")
        f.write(report)
        f.write("\n\nPer-Class Accuracy:\n")
        f.write("-"*60 + "\n")
        for label_name, acc in sorted(class_accuracies.items()):
            f.write(f"{label_name:15} {acc:.4f}\n")
    
    print(f"✓ Saved classification report to: {report_file}")
    print()
    
    # Print summary
    print("="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Overall Accuracy: {overall_acc*100:.2f}%")
    print(f"F1-Score: {f1:.4f}")
    print(f"Average Latency: {avg_latency:.2f} ms")
    print(f"Classes Evaluated: {len(unique_labels)}")
    print()
    
    return results


if __name__ == "__main__":
    try:
        results = evaluate_model()
        if results is None:
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Evaluation failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
