import type { TranscriptEntry } from "@isl/shared";

interface Props {
  transcript: TranscriptEntry[];
  onClear: () => void;
}

export function TranscriptPanel({ transcript, onClear }: Props) {
  const sentence = transcript
    .map((t) => (t.label.length === 1 ? t.label : t.label.replace(/_/g, " ").toLowerCase()))
    .join(" ");

  return (
    <div style={styles.panel}>
      <div style={styles.header}>
        <h3 style={styles.heading}>Live transcript</h3>
        <button style={styles.clearBtn} onClick={onClear}>
          Clear
        </button>
      </div>

      <p style={styles.sentence}>
        {sentence || <span style={styles.placeholder}>Signs you make will appear here…</span>}
      </p>

      <ul style={styles.list}>
        {transcript
          .slice()
          .reverse()
          .map((entry, i) => (
            <li key={i} style={styles.listItem}>
              <span style={styles.itemLabel}>
                {entry.label.length === 1 ? entry.label : entry.label.replace(/_/g, " ")}
              </span>
              <span style={styles.itemMeta}>
                {Math.round(entry.confidence * 100)}% ·{" "}
                {new Date(entry.spokenAt).toLocaleTimeString()}
              </span>
            </li>
          ))}
      </ul>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  panel: {
    background: "#111827",
    borderRadius: 16,
    padding: 20,
    color: "#e5e7eb",
    display: "flex",
    flexDirection: "column",
    minHeight: 300,
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 12,
  },
  heading: { margin: 0, fontSize: 16, fontWeight: 600 },
  clearBtn: {
    background: "transparent",
    border: "1px solid #374151",
    color: "#9ca3af",
    borderRadius: 8,
    padding: "4px 10px",
    fontSize: 12,
    cursor: "pointer",
  },
  sentence: {
    fontSize: 20,
    lineHeight: 1.5,
    marginBottom: 20,
    minHeight: 60,
  },
  placeholder: { color: "#6b7280" },
  list: {
    listStyle: "none",
    padding: 0,
    margin: 0,
    display: "flex",
    flexDirection: "column",
    gap: 8,
    overflowY: "auto",
    flex: 1,
  },
  listItem: {
    display: "flex",
    justifyContent: "space-between",
    borderBottom: "1px solid #1f2937",
    paddingBottom: 6,
  },
  itemLabel: { fontWeight: 600 },
  itemMeta: { fontSize: 12, color: "#6b7280" },
};
