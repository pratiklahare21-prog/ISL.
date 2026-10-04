"""
The live-translation websocket endpoint.

Flow per connection:
  browser --(base64 JPEG frame, ~10-15fps is plenty)--> /ws/translate
  server: decode JPEG -> BGR frame -> MediaPipe landmarks -> feature vector
          -> InferenceSession sliding window -> prediction
  server --(json: {type: "prediction", label, confidence, stable, ...})--> browser

Each connection gets its own LandmarkExtractor + InferenceSession — both
hold per-connection state (MediaPipe trackers assume a continuous stream
from one source; the sliding window is inherently per-conversation).

OPEN-WEIGHT AI INTEGRATION:
  When stable signs accumulate, the SentenceGenerator converts them into
  natural English sentences using an open-weight LLM (Phi-3 or TinyLlama)
  or rule-based fallback.
"""

import base64
import json
import time

import cv2
import numpy as np
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.landmarks import LandmarkExtractor
from app.core.inference import InferenceSession
from app.core.sentence_generator import get_sentence_generator

router = APIRouter()

# Sentence generation parameters
SIGNS_PER_SENTENCE = 4  # Generate sentence every N stable signs


def decode_base64_jpeg(data: str) -> np.ndarray | None:
    try:
        # Strip a data URL prefix if the browser sent one, e.g.
        # "data:image/jpeg;base64,...."
        if "," in data[:64]:
            data = data.split(",", 1)[1]
        raw = base64.b64decode(data)
        arr = np.frombuffer(raw, dtype=np.uint8)
        frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        return frame
    except Exception:
        return None


@router.websocket("/ws/translate")
async def translate_ws(websocket: WebSocket):
    await websocket.accept()

    extractor = LandmarkExtractor()
    session = InferenceSession()
    sentence_generator = get_sentence_generator()
    session_id = "unknown"
    
    # Accumulate stable signs for sentence generation
    accumulated_signs = []

    await websocket.send_text(
        json.dumps(
            {
                "type": "status",
                "sessionId": session_id,
                "status": "connected",
                "message": "ml-service ready with open-weight AI",
            }
        )
    )

    try:
        while True:
            raw_message = await websocket.receive_text()
            try:
                message = json.loads(raw_message)
            except json.JSONDecodeError:
                continue

            msg_type = message.get("type")
            session_id = message.get("sessionId", session_id)

            if msg_type == "reset":
                session.reset()
                accumulated_signs.clear()
                continue

            if msg_type == "stop":
                break

            if msg_type != "frame":
                continue

            frame = decode_base64_jpeg(message.get("data", ""))
            if frame is None:
                continue

            # Match dataset collection: both paths use a mirrored webcam view
            # so handedness and landmark geometry remain consistent.
            frame = cv2.flip(frame, 1)
            landmarks = extractor.process(frame)
            result = session.push_frame(landmarks)

            # Always let the client know hand-detection state (useful for
            # UI feedback like "show your hand to the camera"), but only
            # send a label when there's something meaningful to show/speak.
            payload = {
                "type": "prediction",
                "sessionId": session_id,
                "label": result.label,
                "confidence": round(result.confidence, 4),
                "stable": result.stable,
                "handsDetected": result.hands_detected,
                "timestampMs": message.get("timestampMs", int(time.time() * 1000)),
            }
            await websocket.send_text(json.dumps(payload))
            
            # OPEN-WEIGHT AI INTEGRATION:
            # When a stable sign is detected, accumulate it and generate
            # natural sentences periodically
            if result.stable and result.label:
                accumulated_signs.append(result.label)
                
                # Generate sentence when we have enough signs
                if len(accumulated_signs) >= SIGNS_PER_SENTENCE:
                    sentence_result = sentence_generator.generate_sentence(accumulated_signs)
                    
                    # Send AI-generated sentence to client
                    sentence_payload = {
                        "type": "sentence",
                        "sessionId": session_id,
                        "rawSigns": sentence_result["raw_signs"],
                        "naturalSentence": sentence_result["natural_sentence"],
                        "method": sentence_result["method"],
                        "confidence": sentence_result["confidence"],
                        "timestampMs": int(time.time() * 1000),
                    }
                    await websocket.send_text(json.dumps(sentence_payload))
                    
                    # Clear accumulated signs
                    accumulated_signs.clear()

    except WebSocketDisconnect:
        pass
    finally:
        extractor.close()
