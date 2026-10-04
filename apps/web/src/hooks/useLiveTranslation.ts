import { useCallback, useEffect, useRef, useState } from "react";
import type { WsServerMessage, TranscriptEntry } from "@isl/shared";
import { speak } from "../lib/speech";

const ML_WS_URL =
  import.meta.env.VITE_ML_WS_URL || "ws://localhost:8000/ws/translate";

const CAPTURE_INTERVAL_MS = 40; // ~25 fps so the 24-frame window fills quickly.
const JPEG_QUALITY = 0.6;

export type ConnectionStatus =
  | "idle"
  | "connecting"
  | "connected"
  | "error"
  | "closed";

interface UseLiveTranslationOptions {
  sessionId: string;
  autoSpeak?: boolean;
  onStableLabel?: (label: string) => void;
  onSentence?: (sentence: string, method: string) => void;
}

export function useLiveTranslation({
  sessionId,
  autoSpeak = true,
  onStableLabel,
  onSentence,
}: UseLiveTranslationOptions) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const captureTimerRef = useRef<number | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const captureBusyRef = useRef(false);
  const captureTimeoutRef = useRef<number | null>(null);

  const [status, setStatus] = useState<ConnectionStatus>("idle");
  const [currentLabel, setCurrentLabel] = useState<string>("");
  const [currentConfidence, setCurrentConfidence] = useState(0);
  const [handsDetected, setHandsDetected] = useState({ left: false, right: false });
  const [transcript, setTranscript] = useState<TranscriptEntry[]>([]);
  const [error, setError] = useState<string | null>(null);

  const stopCapturing = useCallback(() => {
    if (captureTimerRef.current) {
      window.clearInterval(captureTimerRef.current);
      captureTimerRef.current = null;
    }
    if (captureTimeoutRef.current) {
      window.clearTimeout(captureTimeoutRef.current);
      captureTimeoutRef.current = null;
    }
    captureBusyRef.current = false;
  }, []);

  const stop = useCallback(() => {
    stopCapturing();
    wsRef.current?.close();
    wsRef.current = null;
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    if (videoRef.current) videoRef.current.srcObject = null;
    setStatus("closed");
  }, [stopCapturing]);

  const start = useCallback(async () => {
    setError(null);
    setStatus("connecting");

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480, facingMode: "user" },
        audio: false,
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
    } catch (err) {
      setError(
        "Could not access the webcam. Please grant camera permission and try again."
      );
      setStatus("error");
      return;
    }

    const ws = new WebSocket(ML_WS_URL);
    wsRef.current = ws;

    ws.onopen = () => {
      setStatus("connected");
      ws.send(JSON.stringify({ type: "start", sessionId }));
      startCapturing();
    };

    ws.onmessage = (event) => {
      try {
        const message: WsServerMessage = JSON.parse(event.data);
        if (message.type === "prediction") {
          captureBusyRef.current = false;
          if (captureTimeoutRef.current) {
            window.clearTimeout(captureTimeoutRef.current);
            captureTimeoutRef.current = null;
          }
          setCurrentLabel(message.label);
          setCurrentConfidence(message.confidence);
          setHandsDetected(message.handsDetected);

          if (message.stable && message.label) {
            onStableLabel?.(message.label);
            const entry: TranscriptEntry = {
              label: message.label,
              confidence: message.confidence,
              spokenAt: new Date().toISOString(),
            };
            setTranscript((prev) => [...prev, entry]);
            if (autoSpeak) speak(message.label);
          }
        } else if (message.type === "sentence") {
          // NEW: Handle AI-generated sentences
          if (message.naturalSentence && onSentence) {
            onSentence(message.naturalSentence, message.method || "unknown");
            if (autoSpeak) {
              // Speak the natural sentence instead of individual signs
              speak(message.naturalSentence);
            }
          }
        } else if (message.type === "status" && message.status === "error") {
          setError(message.message ?? "ml-service reported an error");
        }
      } catch {
        // ignore malformed message
      }
    };

    ws.onerror = () => {
      setError(
        "Could not connect to the translation service. Is apps/ml-service running on port 8000?"
      );
      setStatus("error");
    };

    ws.onclose = () => {
      stopCapturing();
      setStatus((prev) => (prev === "error" ? prev : "closed"));
    };

    function startCapturing() {
      captureTimerRef.current = window.setInterval(() => {
        if (captureBusyRef.current) return;
        captureBusyRef.current = true;
        captureFrame();
      }, CAPTURE_INTERVAL_MS);
    }

    function captureFrame() {
      const video = videoRef.current;
      const canvas = canvasRef.current;
      if (!video || !canvas || ws.readyState !== WebSocket.OPEN) {
        captureBusyRef.current = false;
        return;
      }
      if (video.videoWidth === 0) {
        captureBusyRef.current = false;
        return;
      }

      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      const ctx = canvas.getContext("2d");
      if (!ctx) {
        captureBusyRef.current = false;
        return;
      }
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      const dataUrl = canvas.toDataURL("image/jpeg", JPEG_QUALITY);

      ws.send(
        JSON.stringify({
          type: "frame",
          sessionId,
          data: dataUrl,
          timestampMs: Date.now(),
        })
      );
      captureTimeoutRef.current = window.setTimeout(() => {
        captureBusyRef.current = false;
        captureTimeoutRef.current = null;
      }, 500);
    }
  }, [sessionId, autoSpeak, onStableLabel, onSentence, stopCapturing]);

  const resetTranscript = useCallback(() => {
    setTranscript([]);
    wsRef.current?.send(JSON.stringify({ type: "reset", sessionId }));
  }, [sessionId]);

  useEffect(() => {
    return () => stop();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return {
    videoRef,
    canvasRef,
    status,
    error,
    currentLabel,
    currentConfidence,
    handsDetected,
    transcript,
    start,
    stop,
    resetTranscript,
  };
}
