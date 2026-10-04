"""
Download and prepare ISL datasets for training

This script downloads public ISL datasets and converts them to the format
needed by the training pipeline.

Supported datasets:
1. ISLTranslate - 31k video-sentence pairs
2. ISL-CSLTR - 700 videos, 100 sentences
3. Synthetic data generation for testing

Usage:
    python download_isl_dataset.py --dataset synthetic --signs A,B,C,HELLO,YES,NO
    python download_isl_dataset.py --dataset isltranslate --limit 1000
"""

import argparse
import sys
from pathlib import Path
import numpy as np
import cv2

# Add ml-service to path
ML_SERVICE_ROOT = Path(__file__).resolve().parents[2] / "apps" / "ml-service"
sys.path.insert(0, str(ML_SERVICE_ROOT))

from app.core.landmarks import LandmarkExtractor
from app.core.labels import ALL_SIGN_LABELS

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"
WINDOW_SIZE = 24


def generate_synthetic_samples(signs: list[str], samples_per_sign: int = 40):
    """
    Generate synthetic training data for testing purposes.
    
    This creates randomized but valid landmark sequences that can be used
    to test the training pipeline without needing real video data.
    
    WARNING: These are synthetic samples and will have LOW accuracy.
    They are only for testing the pipeline, not for real use.
    """
    print(f"Generating synthetic data for {len(signs)} signs...")
    print(f"WARNING: Synthetic data is for TESTING ONLY. Accuracy will be poor.")
    print()
    
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    extractor = LandmarkExtractor()
    
    for sign in signs:
        if sign not in ALL_SIGN_LABELS:
            print(f"⚠️  Skipping '{sign}' - not in known labels")
            continue
        
        output_path = DATA_DIR / f"{sign}.npy"
        
        # Check if data already exists
        if output_path.exists():
            existing = np.load(output_path)
            print(f"✓ {sign}: {existing.shape[0]} samples already exist, skipping")
            continue
        
        samples = []
        
        # Generate synthetic landmark sequences
        for i in range(samples_per_sign):
            # Create a synthetic sequence with some variation
            base_variation = np.random.randn(1, 126) * 0.05
            sequence = []
            
            for frame_idx in range(WINDOW_SIZE):
                # Add temporal variation
                temporal_noise = np.random.randn(126) * 0.02
                frame_variation = base_variation + temporal_noise
                
                # Create realistic-ish hand positions
                # Left hand (landmarks 0-62)
                left_hand = np.random.rand(63) * 0.5 + 0.25  # Center region
                # Right hand (landmarks 63-125)
                right_hand = np.random.rand(63) * 0.5 + 0.25
                
                frame_data = np.concatenate([left_hand, right_hand]).astype(np.float32)
                frame_data += frame_variation.flatten()
                frame_data = np.clip(frame_data, 0, 1)  # Keep in valid range
                
                sequence.append(frame_data)
            
            samples.append(np.stack(sequence, axis=0))
        
        # Save samples
        samples_array = np.stack(samples, axis=0)  # (samples, window_size, 126)
        np.save(output_path, samples_array)
        
        print(f"✓ {sign}: Generated {samples_per_sign} synthetic samples")
    
    extractor.close()
    print()
    print("✅ Synthetic data generation complete")
    print()
    print("⚠️  IMPORTANT: Synthetic data is for PIPELINE TESTING only!")
    print("   For real accuracy, record actual sign language data using:")
    print("   python collect.py --label <SIGN> --samples 40")


def download_isltranslate_dataset(limit: int = None):
    """
    Download ISLTranslate dataset and extract landmarks.
    
    NOTE: This requires manual download first due to dataset terms.
    """
    print("ISLTranslate Dataset Download")
    print("="*60)
    print()
    print("The ISLTranslate dataset requires manual download:")
    print()
    print("1. Visit: https://github.com/Exploration-Lab/ISLTranslate")
    print("2. Follow download instructions (requires Google Form)")
    print("3. Download ISL-videos.tar.gz or mediapipe_holistic_poses.tar.gz")
    print("4. Extract to ml/data/external/isltranslate/")
    print()
    print("Dataset Info:")
    print("- 31,000 ISL-English sentence pairs")
    print("- Continuous sign language (not isolated signs)")
    print("- Pre-extracted MediaPipe features available")
    print()
    print("License: CC-BY-NC (Non-commercial use only)")
    print()
    print("After downloading, run:")
    print("python process_isltranslate.py --data-dir ml/data/external/isltranslate/")


def download_islcsltr_dataset():
    """
    Download ISL-CSLTR dataset.
    """
    print("ISL-CSLTR Dataset Download")
    print("="*60)
    print()
    print("The ISL-CSLTR dataset requires manual download:")
    print()
    print("1. Visit: https://data.mendeley.com/datasets/kcmpdxky7p/1")
    print("2. Click 'Download' (may require Mendeley account)")
    print("3. Extract to ml/data/external/isl-csltr/")
    print()
    print("Dataset Info:")
    print("- 700 videos, 100 sentences")
    print("- 7 different signers")
    print("- Sentence-level and word-level annotations")
    print()
    print("License: Check Mendeley page for terms")


def main():
    parser = argparse.ArgumentParser(
        description="Download and prepare ISL datasets"
    )
    parser.add_argument(
        "--dataset",
        choices=["synthetic", "isltranslate", "islcsltr"],
        default="synthetic",
        help="Dataset to download/generate"
    )
    parser.add_argument(
        "--signs",
        type=str,
        default="A,B,C,D,E,HELLO,YES,NO,THANK_YOU,HELP,MY,NAME",
        help="Comma-separated list of signs for synthetic data"
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=40,
        help="Number of samples per sign (synthetic only)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of samples (for large datasets)"
    )
    
    args = parser.parse_args()
    
    if args.dataset == "synthetic":
        signs = [s.strip().upper() for s in args.signs.split(",")]
        generate_synthetic_samples(signs, args.samples)
    
    elif args.dataset == "isltranslate":
        download_isltranslate_dataset(args.limit)
    
    elif args.dataset == "islcsltr":
        download_islcsltr_dataset()


if __name__ == "__main__":
    main()
