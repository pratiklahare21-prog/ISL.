"""
Per-session inference state machine.

This is the piece that makes live translation feel stable instead of
flickering a different letter every frame. Each websocket session owns
one InferenceSession, which:

  1. Buffers incoming per-frame landmark feature vectors into a fixed-
     size sliding window (WINDOW_SIZE frames).
  2. Runs the model once the window is full (and then on every new
     frame, dropping the oldest — a rolling window).
  3. Requires the SAME predicted label to win across STABILITY_FRAMES
     consecutive windows, above CONFIDENCE_THRESHOLD, before it is
     reported as "stable" (i.e. worth speaking / appending to the
     transcript). This is a simple temporal-smoothing / debounce filter
     — it trades a little latency (a few hundred ms) for much lower
     false-trigger and flicker rates, which is the right trade-off for
     "speak it out loud" use cases.
  4. Tracks a cooldown so the same stable sign isn't re-spoken every
     window while the user holds the same hand shape.
"""

from collections import deque, Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np
import torch

from app.core.labels import ALL_SIGN_LABELS, NUM_CLASSES
from app.core.landmarks import FrameLandmarks, FEATURE_VECTOR_SIZE
from app.models.architecture import SignSequenceClassifier

WINDOW_SIZE = 24  # ~0.8s at 30fps; long enough to capture short word signs
STABILITY_FRAMES = 2  # consecutive windows that must agree
CONFIDENCE_THRESHOLD = 0.65
CONFIDENCE_MARGIN = 0.05
REPEAT_COOLDOWN_WINDOWS = 10  # prevent repeated speech while a sign is held
MIN_HAND_FRAMES = 18  # require a hand in most of the rolling window

DEFAULT_CHECKPOINT = (
    Path(__file__).resolve().parents[4] / "ml" / "models_out" / "isl_model.pt"
)


@dataclass
class PredictionResult:
    label: str
    confidence: float
    stable: bool
    hands_detected: dict


class ModelRegistry:
    """Loads the checkpoint once per process; sessions share the model
    (read-only inference), but each session keeps its own buffer state."""

    _model: Optional[SignSequenceClassifier] = None
    _device: torch.device = torch.device("cpu")
    _allowed_indices: Optional[set[int]] = None

    @classmethod
    def allowed_indices(cls) -> set[int]:
        if cls._allowed_indices is None:
            raw_dir = Path(__file__).resolve().parents[4] / "ml" / "data" / "raw"
            trained = {
                path.stem
                for path in raw_dir.glob("*.npy")
                if path.is_file()
            }
            indices = {
                index
                for label, index in (
                    (label, ALL_SIGN_LABELS.index(label))
                    for label in trained
                    if label in ALL_SIGN_LABELS
                )
            }
            cls._allowed_indices = indices or set(range(NUM_CLASSES))
        return cls._allowed_indices

    @classmethod
    def get_model(cls) -> Optional[SignSequenceClassifier]:
        if cls._model is None:
            if not DEFAULT_CHECKPOINT.exists():
                return None
            model = SignSequenceClassifier(
                input_size=FEATURE_VECTOR_SIZE, num_classes=NUM_CLASSES
            )
            state = torch.load(DEFAULT_CHECKPOINT, map_location=cls._device)
            model.load_state_dict(state)
            model.eval()
            cls._model = model
        return cls._model


class InferenceSession:
    def __init__(self):
        self.buffer: deque[np.ndarray] = deque(maxlen=WINDOW_SIZE)
        self.hand_presence: deque[bool] = deque(maxlen=WINDOW_SIZE)
        self.recent_predictions: deque[str] = deque(maxlen=STABILITY_FRAMES)
        self.last_stable_label: Optional[str] = None
        self.cooldown_remaining: int = 0

    def push_frame(self, landmarks: FrameLandmarks) -> PredictionResult:
        feature = landmarks.to_feature_vector()
        self.buffer.append(feature)
        has_hand = landmarks.has_any_hand()
        self.hand_presence.append(has_hand)

        hands_detected = {
            "left": landmarks.left_hand is not None,
            "right": landmarks.right_hand is not None,
        }

        if not has_hand:
            # No hands on screen: don't guess, and let the stability
            # buffer decay so a re-appearing hand starts a fresh vote.
            self.buffer.clear()
            self.hand_presence.clear()
            self.recent_predictions.clear()
            self.last_stable_label = None
            return PredictionResult("", 0.0, False, hands_detected)

        model = ModelRegistry.get_model()
        if (
            model is None
            or len(self.buffer) < WINDOW_SIZE
            or sum(self.hand_presence) < MIN_HAND_FRAMES
        ):
            return PredictionResult("", 0.0, False, hands_detected)

        window = np.stack(self.buffer, axis=0)  # (WINDOW_SIZE, 126)
        tensor = torch.from_numpy(window).unsqueeze(0).float()  # (1, T, 126)

        with torch.no_grad():
            logits = model(tensor)
            allowed = ModelRegistry.allowed_indices()
            masked_logits = logits.squeeze(0).clone()
            disallowed = [
                index for index in range(NUM_CLASSES) if index not in allowed
            ]
            masked_logits[disallowed] = -torch.inf
            probs = torch.softmax(masked_logits, dim=-1)
            top_idx = int(torch.argmax(probs).item())
            top_conf = float(probs[top_idx].item())
            top_two = torch.topk(probs, k=min(2, len(probs))).values
            confidence_margin = (
                float(top_two[0] - top_two[1]) if len(top_two) > 1 else 1.0
            )

        label = (
            ALL_SIGN_LABELS[top_idx]
            if top_conf >= CONFIDENCE_THRESHOLD
            and confidence_margin >= CONFIDENCE_MARGIN
            else ""
        )

        if self.cooldown_remaining > 0:
            self.cooldown_remaining -= 1

        if label:
            self.recent_predictions.append(label)
        else:
            self.recent_predictions.clear()

        stable = False
        if len(self.recent_predictions) == STABILITY_FRAMES and self.cooldown_remaining == 0:
            most_common_label, count = Counter(self.recent_predictions).most_common(1)[0]
            # Accept a short majority instead of requiring every rolling
            # window to agree; one noisy webcam frame should not cancel a
            # genuine sign.
            if count >= 2 and most_common_label != self.last_stable_label:
                stable = True
                self.last_stable_label = most_common_label
                self.cooldown_remaining = REPEAT_COOLDOWN_WINDOWS
                label = most_common_label

        return PredictionResult(label, top_conf, stable, hands_detected)

    def reset(self):
        self.buffer.clear()
        self.hand_presence.clear()
        self.recent_predictions.clear()
        self.last_stable_label = None
        self.cooldown_remaining = 0
