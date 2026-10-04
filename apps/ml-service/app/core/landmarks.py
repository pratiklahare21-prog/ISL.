"""
Wraps MediaPipe Holistic-style hand (+ optional pose) detection into a
single call: raw BGR frame -> normalized landmark arrays.

We use MediaPipe's `Hands` solution (21 points per hand, x/y/z normalized
to [0,1] relative to image size, z is relative depth) rather than full
Holistic, since ISL fingerspelling and most common-word signs are
hand-dominant; this keeps inference fast enough for real-time video on a
CPU/iGPU laptop. Pose landmarks are wired in as optional, for future signs
that need shoulder/torso reference (e.g. signs performed near the chest).
"""

from dataclasses import dataclass
from typing import Optional

import cv2
import mediapipe as mp
import numpy as np

mp_hands = mp.solutions.hands

NUM_HAND_LANDMARKS = 21
# x, y, z per landmark
POINT_DIM = 3


def normalize_feature_vector(feature: np.ndarray) -> np.ndarray:
    """Normalize each hand around its wrist for position-invariant shapes."""
    normalized = feature.reshape(2, NUM_HAND_LANDMARKS, POINT_DIM).copy()
    for hand in normalized:
        if not np.any(hand):
            continue
        hand -= hand[0]
        scale = float(np.max(np.linalg.norm(hand, axis=1)))
        if scale > 1e-6:
            hand /= scale
    return normalized.reshape(NUM_HAND_LANDMARKS * POINT_DIM * 2).astype(np.float32)


@dataclass
class FrameLandmarks:
    left_hand: Optional[np.ndarray]  # shape (21, 3) or None
    right_hand: Optional[np.ndarray]  # shape (21, 3) or None

    def has_any_hand(self) -> bool:
        return self.left_hand is not None or self.right_hand is not None

    def to_feature_vector(self) -> np.ndarray:
        """
        Flattens to a fixed-size (126,) vector: 21*3 for left + 21*3 for
        right, zero-filled when a hand isn't visible. Fixed size and
        order is required so the model always sees a consistent input
        shape regardless of which hand(s) are on screen.
        """
        left = (
            self.left_hand.flatten()
            if self.left_hand is not None
            else np.zeros(NUM_HAND_LANDMARKS * POINT_DIM, dtype=np.float32)
        )
        right = (
            self.right_hand.flatten()
            if self.right_hand is not None
            else np.zeros(NUM_HAND_LANDMARKS * POINT_DIM, dtype=np.float32)
        )
        return normalize_feature_vector(np.concatenate([left, right]))


FEATURE_VECTOR_SIZE = NUM_HAND_LANDMARKS * POINT_DIM * 2  # 126


class LandmarkExtractor:
    """
    Not thread-safe by MediaPipe's own contract — each websocket
    connection/session must own its own instance (see app/routes/ws.py).
    """

    def __init__(
        self,
        static_image_mode: bool = False,
        max_num_hands: int = 2,
        min_detection_confidence: float = 0.6,
        min_tracking_confidence: float = 0.5,
    ):
        self._hands = mp_hands.Hands(
            static_image_mode=static_image_mode,
            max_num_hands=max_num_hands,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )

    def process(self, frame_bgr: np.ndarray) -> FrameLandmarks:
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        frame_rgb.flags.writeable = False
        results = self._hands.process(frame_rgb)

        left_hand = None
        right_hand = None

        if results.multi_hand_landmarks and results.multi_handedness:
            for hand_landmarks, handedness in zip(
                results.multi_hand_landmarks, results.multi_handedness
            ):
                points = np.array(
                    [[lm.x, lm.y, lm.z] for lm in hand_landmarks.landmark],
                    dtype=np.float32,
                )
                # MediaPipe reports handedness from the camera's mirrored
                # perspective; "Left"/"Right" here refers to the label
                # in the source video, which is what we consistently use
                # both at training-data collection time and inference time.
                label = handedness.classification[0].label
                if label == "Left":
                    left_hand = points
                else:
                    right_hand = points

        return FrameLandmarks(left_hand=left_hand, right_hand=right_hand)

    def close(self):
        self._hands.close()
