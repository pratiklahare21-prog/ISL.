import { RefObject } from "react";

interface Props {
  videoRef: RefObject<HTMLVideoElement>;
  canvasRef: RefObject<HTMLCanvasElement>;
  handsDetected: { left: boolean; right: boolean };
  currentLabel: string;
  currentConfidence: number;
}

export function WebcamView({
  videoRef,
  canvasRef,
  handsDetected,
  currentLabel,
  currentConfidence,
}: Props) {
  return (
    <div style={styles.wrapper}>
      <video ref={videoRef} style={styles.video} muted playsInline />
      <canvas ref={canvasRef} style={{ display: "none" }} />

      <div style={styles.overlayTop}>
        <span style={handBadgeStyle(handsDetected.left)}>Left hand</span>
        <span style={handBadgeStyle(handsDetected.right)}>Right hand</span>
      </div>

      {currentLabel && (
        <div style={styles.overlayBottom}>
          <span style={styles.liveLabel}>{formatLabel(currentLabel)}</span>
          <span style={styles.confidence}>
            {Math.round(currentConfidence * 100)}%
          </span>
        </div>
      )}
    </div>
  );
}

function formatLabel(label: string) {
  return label.length === 1 ? label : label.replace(/_/g, " ");
}

function handBadgeStyle(active: boolean): React.CSSProperties {
  return {
    padding: "4px 10px",
    borderRadius: 999,
    fontSize: 12,
    fontWeight: 600,
    background: active ? "#22c55e" : "rgba(255,255,255,0.15)",
    color: active ? "#08210f" : "#e5e7eb",
    transition: "background 150ms ease",
  };
}

const styles: Record<string, React.CSSProperties> = {
  wrapper: {
    position: "relative",
    width: "100%",
    maxWidth: 640,
    aspectRatio: "4 / 3",
    borderRadius: 16,
    overflow: "hidden",
    background: "#0b0f14",
    boxShadow: "0 8px 30px rgba(0,0,0,0.25)",
  },
  video: {
    width: "100%",
    height: "100%",
    objectFit: "cover",
    transform: "scaleX(-1)",
  },
  overlayTop: {
    position: "absolute",
    top: 12,
    left: 12,
    display: "flex",
    gap: 8,
  },
  overlayBottom: {
    position: "absolute",
    bottom: 0,
    left: 0,
    right: 0,
    padding: "16px 20px",
    background:
      "linear-gradient(to top, rgba(0,0,0,0.75), rgba(0,0,0,0))",
    display: "flex",
    alignItems: "baseline",
    gap: 10,
  },
  liveLabel: {
    color: "#fff",
    fontSize: 32,
    fontWeight: 700,
    letterSpacing: 0.5,
  },
  confidence: {
    color: "#a3e635",
    fontSize: 14,
    fontWeight: 600,
  },
};
