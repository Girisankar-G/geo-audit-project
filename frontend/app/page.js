"use client";
import { useState } from "react";

const API = "http://localhost:8000";

export default function Home() {
  const [url, setUrl] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function runAudit() {
    if (!url.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await fetch(`${API}/audit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Audit failed");
      setResult(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main style={{ minHeight: "100vh", background: "#0a0a0f", color: "#e2e2e2", padding: "48px 16px", fontFamily: "Segoe UI, system-ui, sans-serif" }}>
      <div style={{ maxWidth: 860, margin: "0 auto" }}>

        {/* Header */}
        <div style={{ marginBottom: 40 }}>
          <h1 style={{ fontSize: 28, fontWeight: 700, display: "flex", alignItems: "center", gap: 10 }}>
            ⚡ Villion GEO Audit
          </h1>
          <p style={{ color: "#666", fontSize: 14, marginTop: 6 }}>
            Analyze any webpage for AI citation readiness on ChatGPT, Perplexity & Google AI.
          </p>
        </div>

        {/* Input */}
        <div style={{ display: "flex", gap: 10, marginBottom: 32 }}>
          <input
            type="url"
            value={url}
            onChange={e => setUrl(e.target.value)}
            onKeyDown={e => e.key === "Enter" && runAudit()}
            placeholder="https://example.com/about"
            style={{ flex: 1, background: "#111118", border: "1px solid #2a2a3a", borderRadius: 10, padding: "12px 16px", fontSize: 14, color: "#e2e2e2", outline: "none" }}
          />
          <button
            onClick={runAudit}
            disabled={loading}
            style={{ background: loading ? "#3b1f6e" : "#7c3aed", color: "white", border: "none", borderRadius: 10, padding: "12px 24px", fontSize: 14, fontWeight: 600, cursor: loading ? "not-allowed" : "pointer" }}
          >
            {loading ? "Auditing…" : "Run Audit"}
          </button>
        </div>

        {/* Error */}
        {error && (
          <div style={{ background: "#1a0505", border: "1px solid #5a1010", color: "#f87171", borderRadius: 10, padding: "12px 16px", fontSize: 13, marginBottom: 20 }}>
            ⚠ {error}
          </div>
        )}

        {/* Loading */}
        {loading && [1,2,3].map(i => (
          <div key={i} style={{ background: "#111118", border: "1px solid #1e1e2e", borderRadius: 14, height: i === 2 ? 160 : 100, marginBottom: 16 }} />
        ))}

        {/* Results */}
        {result && !loading && (
          <div>
            {result.warning && (
              <div style={{ background: "#1a1500", border: "1px solid #5a4500", color: "#f5c542", borderRadius: 10, padding: "10px 14px", fontSize: 12, marginBottom: 16 }}>
                ℹ {result.warning}
              </div>
            )}

            {/* Page Data */}
            <Card title="Page Data" right={<Badge color="#1e1e2e" text={result.url} />}>
              <Row label="Title" value={result.page_data.title} />
              <Row label="Meta Description" value={result.page_data.meta_description} />
              <div style={{ marginBottom: 12 }}>
                <Label>Headings</Label>
                {result.page_data.headings.length > 0
                  ? result.page_data.headings.map((h, i) => <Tag key={i}>{h}</Tag>)
                  : <Missing />}
              </div>
              <div>
                <Label>Images Detected</Label>
                {result.page_data.image_urls.length > 0
                  ? result.page_data.image_urls.slice(0,3).map((img, i) => (
                    <a key={i} href={img} target="_blank" rel="noreferrer" style={{ display: "block", fontSize: 12, color: "#60a5fa", marginTop: 4, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{img}</a>
                  ))
                  : <Missing />}
              </div>
            </Card>

            {/* Schema */}
            <Card title="Schema Recommendation" right={
              <div style={{ display: "flex", gap: 6 }}>
                <Badge color="#2d1b69" textColor="#a78bfa" text={result.detected_schema_type} />
                <Badge
                  color={result.detection_method === "llm" ? "#052e16" : "#1e1e2e"}
                  textColor={result.detection_method === "llm" ? "#4ade80" : "#888"}
                  text={result.detection_method === "llm" ? "🤖 LLM-enriched" : "📐 Rule-based"}
                />
              </div>
            }>
              <pre style={{ background: "#070710", borderRadius: 10, padding: 16, fontSize: 12, color: "#4ade80", overflowX: "auto", lineHeight: 1.6, margin: 0 }}>
                {JSON.stringify(result.recommended_jsonld, null, 2)}
              </pre>
            </Card>

            {/* GEO Tips */}
            <Card title="GEO Improvement Tips">
              {result.geo_tips.map((tip, i) => (
                <div key={i} style={{ display: "flex", gap: 10, fontSize: 13, color: "#ccc", marginBottom: 10, lineHeight: 1.5 }}>
                  <span style={{ color: "#7c3aed", flexShrink: 0 }}>→</span>
                  <span>{tip}</span>
                </div>
              ))}
            </Card>
          </div>
        )}
      </div>
    </main>
  );
}

function Card({ title, right, children }) {
  return (
    <div style={{ background: "#111118", border: "1px solid #1e1e2e", borderRadius: 14, padding: 24, marginBottom: 20 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 18 }}>
        <span style={{ fontSize: 11, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: "#888" }}>{title}</span>
        {right}
      </div>
      {children}
    </div>
  );
}

function Badge({ color, textColor = "#aaa", text }) {
  return (
    <span style={{ fontSize: 11, fontWeight: 700, padding: "3px 10px", borderRadius: 20, background: color, color: textColor }}>
      {text}
    </span>
  );
}

function Row({ label, value }) {
  return (
    <div style={{ marginBottom: 14 }}>
      <Label>{label}</Label>
      {value
        ? <p style={{ fontSize: 13, color: "#ccc", margin: 0 }}>{value}</p>
        : <Missing />}
    </div>
  );
}

function Label({ children }) {
  return <div style={{ fontSize: 10, textTransform: "uppercase", letterSpacing: "0.08em", color: "#555", marginBottom: 4 }}>{children}</div>;
}

function Tag({ children }) {
  return <span style={{ display: "inline-block", background: "#1a1a2e", borderRadius: 6, padding: "3px 10px", fontSize: 12, color: "#bbb", margin: "3px 3px 3px 0" }}>{children}</span>;
}

function Missing() {
  return <span style={{ fontSize: 13, color: "#e55", fontStyle: "italic" }}>Not found</span>;
}