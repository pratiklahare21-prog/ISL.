import { useEffect, useState } from "react";
import { api } from "../lib/api";

interface SessionSummary {
  id: string;
  title: string | null;
  signCount: number;
  avgConfidence: number | null;
  createdAt: string;
  transcript: { label: string; confidence: number; spokenAt: string }[];
}

export function HistoryPage() {
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get("/sessions")
      .then((res) => setSessions(res.data.data))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div style={{ maxWidth: 800, margin: "40px auto", fontFamily: "Inter, sans-serif", padding: "0 20px" }}>
      <h1>Session history</h1>
      {loading && <p>Loading…</p>}
      {!loading && sessions.length === 0 && <p>No sessions saved yet.</p>}
      <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
        {sessions.map((s) => (
          <div
            key={s.id}
            style={{
              border: "1px solid #e5e7eb",
              borderRadius: 12,
              padding: 16,
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <strong>{s.title || "Untitled session"}</strong>
              <span style={{ color: "#6b7280", fontSize: 13 }}>
                {new Date(s.createdAt).toLocaleString()}
              </span>
            </div>
            <p style={{ color: "#6b7280", fontSize: 13 }}>
              {s.signCount} signs ·{" "}
              {s.avgConfidence ? `${Math.round(s.avgConfidence * 100)}% avg confidence` : "—"}
            </p>
            <p>
              {s.transcript
                .map((t) => (t.label.length === 1 ? t.label : t.label.replace(/_/g, " ").toLowerCase()))
                .join(" ")}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
