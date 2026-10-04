import { useCallback, useState } from "react";
import { useLiveTranslation } from "../hooks/useLiveTranslation";
import { WebcamView } from "../components/WebcamView";
import { TranscriptPanel } from "../components/TranscriptPanel";
import { speak, stopSpeaking } from "../lib/speech";

function randomSessionId() {
  return `sess_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
}

const DEMO_STEPS = [
  "A", "B", "C", "D", "E",
  "MY", "NAME", "O", "M",
  "MY", "NAME", "P", "R", "A", "T", "I", "K",
];

export function TranslatorPage() {
  const [sessionId] = useState(randomSessionId);
  const [autoSpeak, setAutoSpeak] = useState(true);
  const [demoIndex, setDemoIndex] = useState(0);
  const [demoOutput, setDemoOutput] = useState("");
  const [assisted, setAssisted] = useState(false);
  const [aiSentences, setAiSentences] = useState<Array<{sentence: string, method: string, timestamp: number}>>([]);

  const handleStableLabel = useCallback((label: string) => {
    setDemoIndex((index) => {
      if (label !== DEMO_STEPS[index]) return index;
      const next = index + 1;
      if (next === 9) {
        setDemoOutput("Name recognized: OM");
        speak("Om");
      }
      if (next === DEMO_STEPS.length) {
        setDemoOutput("Name recognized: PRATIK");
        speak("Pratik");
      }
      return next;
    });
  }, []);

  const handleSentence = useCallback((sentence: string, method: string) => {
    setAiSentences(prev => [...prev, { sentence, method, timestamp: Date.now() }]);
  }, []);

  function advanceExpectedStep() {
    setAssisted(true);
    setDemoIndex((index) => {
      const next = index + 1;
      if (next === 9) {
        setDemoOutput("Name recognized: OM");
        speak("Om");
      }
      if (next === DEMO_STEPS.length) {
        setDemoOutput("Name recognized: PRATIK");
        speak("Pratik");
      }
      return Math.min(next, DEMO_STEPS.length);
    });
  }

  function resetDemo() {
    setDemoIndex(0);
    setDemoOutput("");
    setAssisted(false);
    setAiSentences([]);
    resetTranscript();
    stopSpeaking();
  }

  const {
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
  } = useLiveTranslation({
    sessionId,
    autoSpeak,
    onStableLabel: handleStableLabel,
    onSentence: handleSentence,
  });

  const isLive = status === "connected";

  async function handleStop() {
    stop();
    stopSpeaking();
    resetTranscript();
  }

  return (
    <div style={styles.page}>
      <header style={styles.header}>
        <h1 style={styles.title}>ISL Live Translator</h1>
        <p style={styles.subtitle}>
          Sign in front of the camera — recognized signs are shown and spoken aloud.
        </p>
      </header>

      <div style={styles.controls}>
        {!isLive ? (
          <button style={styles.primaryBtn} onClick={start}>
            Start camera
          </button>
        ) : (
          <button style={styles.dangerBtn} onClick={handleStop}>
            Stop
          </button>
        )}

        <label style={styles.checkboxLabel}>
          <input
            type="checkbox"
            checked={autoSpeak}
            onChange={(e) => setAutoSpeak(e.target.checked)}
          />
          Speak aloud
        </label>

        <span style={statusBadgeStyle(status)}>{status}</span>
        <button
          style={styles.assistBtn}
          onClick={advanceExpectedStep}
          disabled={demoIndex >= DEMO_STEPS.length}
        >
          Demo: next step
        </button>
        <button style={styles.resetBtn} onClick={resetDemo}>
          Reset demo
        </button>
      </div>

      <div style={styles.demoBox}>
        <strong>Presentation mode</strong> · Step {Math.min(demoIndex + 1, DEMO_STEPS.length)} of {DEMO_STEPS.length}
        <br />
        <strong>Demo order:</strong> {DEMO_STEPS.join(" → ")}
        <br />
        <strong>Next sign:</strong>{" "}
        {demoIndex < DEMO_STEPS.length ? DEMO_STEPS[demoIndex] : "Demo complete"}
        {demoOutput && <><br /><strong>Sentence:</strong> {demoOutput}</>}
        {assisted && (
          <>
            <br />
            <strong>Presentation assist used:</strong> this step was expected,
            not recognized by the model.
          </>
        )}
      </div>

      {error && <div style={styles.errorBox}>{error}</div>}

      {aiSentences.length > 0 && (
        <div style={styles.aiSentenceBox}>
          <strong>🤖 AI-Generated Sentences (Open-Weight LLM):</strong>
          {aiSentences.slice(-3).map((item, idx) => (
            <div key={item.timestamp} style={styles.sentenceItem}>
              <span style={styles.sentenceBadge}>{item.method}</span>
              {item.sentence}
            </div>
          ))}
        </div>
      )}

      <div style={styles.grid}>
        <WebcamView
          videoRef={videoRef}
          canvasRef={canvasRef}
          handsDetected={handsDetected}
          currentLabel={currentLabel}
          currentConfidence={currentConfidence}
        />
        <TranscriptPanel transcript={transcript} onClear={resetTranscript} />
      </div>

      <footer style={styles.footer}>
        <p>
          Recognizing the alphabet, digits, and a set of common daily-conversation
          words. Accuracy depends on the amount of training data collected for
          each sign — see the project README for how to add more.
        </p>
      </footer>
    </div>
  );
}

function statusBadgeStyle(status: string): React.CSSProperties {
  const colors: Record<string, string> = {
    idle: "#6b7280",
    connecting: "#f59e0b",
    connected: "#22c55e",
    error: "#ef4444",
    closed: "#6b7280",
  };
  return {
    padding: "4px 12px",
    borderRadius: 999,
    fontSize: 12,
    fontWeight: 600,
    background: colors[status] ?? "#6b7280",
    color: "#0b0f14",
    textTransform: "capitalize",
  };
}

const styles: Record<string, React.CSSProperties> = {
  page: {
    maxWidth: 1100,
    margin: "0 auto",
    padding: "32px 20px 60px",
    fontFamily:
      "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    color: "#111827",
  },
  header: { marginBottom: 24 },
  title: { fontSize: 28, fontWeight: 800, margin: 0 },
  subtitle: { color: "#6b7280", marginTop: 6 },
  controls: {
    display: "flex",
    alignItems: "center",
    gap: 16,
    marginBottom: 20,
    flexWrap: "wrap",
  },
  primaryBtn: {
    background: "#111827",
    color: "#fff",
    border: "none",
    borderRadius: 10,
    padding: "10px 20px",
    fontWeight: 600,
    cursor: "pointer",
  },
  dangerBtn: {
    background: "#dc2626",
    color: "#fff",
    border: "none",
    borderRadius: 10,
    padding: "10px 20px",
    fontWeight: 600,
    cursor: "pointer",
  },
  checkboxLabel: {
    display: "flex",
    alignItems: "center",
    gap: 6,
    fontSize: 14,
    color: "#374151",
  },
  hint: { fontSize: 13, color: "#6b7280" },
  assistBtn: {
    background: "#fef3c7",
    color: "#92400e",
    border: "1px solid #fcd34d",
    borderRadius: 8,
    padding: "8px 12px",
    fontSize: 12,
    cursor: "pointer",
  },
  resetBtn: {
    background: "#fff",
    color: "#374151",
    border: "1px solid #d1d5db",
    borderRadius: 8,
    padding: "8px 12px",
    fontSize: 12,
    cursor: "pointer",
  },
  errorBox: {
    background: "#fef2f2",
    border: "1px solid #fecaca",
    color: "#991b1b",
    padding: "12px 16px",
    borderRadius: 10,
    marginBottom: 20,
  },
  aiSentenceBox: {
    background: "#f0fdf4",
    border: "2px solid #86efac",
    color: "#166534",
    padding: "16px",
    borderRadius: 10,
    marginBottom: 20,
    lineHeight: 1.8,
  },
  sentenceItem: {
    marginTop: 8,
    padding: "8px 12px",
    background: "#dcfce7",
    borderRadius: 8,
    fontSize: 16,
  },
  sentenceBadge: {
    background: "#22c55e",
    color: "white",
    padding: "2px 8px",
    borderRadius: 4,
    fontSize: 11,
    fontWeight: 600,
    marginRight: 8,
    textTransform: "uppercase",
  },
  demoBox: {
    background: "#eff6ff",
    border: "1px solid #bfdbfe",
    color: "#1e3a8a",
    padding: "12px 16px",
    borderRadius: 10,
    marginBottom: 20,
    lineHeight: 1.6,
  },
  grid: {
    display: "grid",
    gridTemplateColumns: "1.4fr 1fr",
    gap: 24,
    alignItems: "start",
  },
  footer: { marginTop: 32, color: "#9ca3af", fontSize: 13 },
};
