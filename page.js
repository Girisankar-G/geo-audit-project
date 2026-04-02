"use client";

import { useState } from "react";

const API_BASE = "http://localhost:8000";

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
      const res = await fetch(`${API_BASE}/audit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Audit failed");
      }

      const data = await res.json();
      setResult(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-gray-950 text-white px-4 py-12">
      <div className="max-w-4xl mx-auto">

        {/* Header */}
        <div className="mb-10">
          <div className="flex items-center gap-3 mb-2">
            <span className="text-2xl">⚡</span>
            <h1 className="text-3xl font-bold tracking-tight">Villion GEO Audit</h1>
          </div>
          <p className="text-gray-400 text-sm">
            Analyze any webpage for AI citation readiness on ChatGPT, Perplexity & Google AI.
          </p>
        </div>

        {/* Input */}
        <div className="flex gap-3 mb-8">
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && runAudit()}
            placeholder="https://example.com/about"
            className="flex-1 bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-sm focus:outline-none focus:border-violet-500 placeholder-gray-600"
          />
          <button
            onClick={runAudit}
            disabled={loading}
            className="bg-violet-600 hover:bg-violet-500 disabled:bg-violet-900 px-6 py-3 rounded-lg font-semibold text-sm transition-colors"
          >
            {loading ? "Auditing…" : "Run Audit"}
          </button>
        </div>

        {/* Error */}
        {error && (
          <div className="bg-red-950 border border-red-700 text-red-300 rounded-lg px-4 py-3 text-sm mb-6">
            ⚠ {error}
          </div>
        )}

        {/* Loading skeleton */}
        {loading && (
          <div className="space-y-4 animate-pulse">
            {[1, 2, 3].map((i) => (
              <div key={i} className="bg-gray-900 rounded-lg h-24 border border-gray-800" />
            ))}
          </div>
        )}

        {/* Results */}
        {result && !loading && (
          <div className="space-y-6">

            {/* Warning banner */}
            {result.warning && (
              <div className="bg-yellow-950 border border-yellow-700 text-yellow-300 rounded-lg px-4 py-2 text-xs">
                ℹ {result.warning}
              </div>
            )}

            {/* Page Data Card */}
            <section className="bg-gray-900 border border-gray-800 rounded-xl p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="font-semibold text-sm text-gray-300 uppercase tracking-widest">
                  Page Data
                </h2>
                <span className="text-xs bg-gray-800 px-2 py-1 rounded text-gray-400">
                  {result.url}
                </span>
              </div>

              <div className="space-y-3 text-sm">
                <Row label="Title" value={result.page_data.title} />
                <Row label="Meta Description" value={result.page_data.meta_description} />

                {result.page_data.headings.length > 0 && (
                  <div>
                    <span className="text-gray-500 text-xs uppercase tracking-wide">Headings</span>
                    <ul className="mt-1 space-y-1">
                      {result.page_data.headings.map((h, i) => (
                        <li key={i} className="text-gray-300 text-xs bg-gray-800 px-2 py-1 rounded">
                          {h}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {result.page_data.image_urls.length > 0 && (
                  <div>
                    <span className="text-gray-500 text-xs uppercase tracking-wide">Images Detected</span>
                    <ul className="mt-1 space-y-1">
                      {result.page_data.image_urls.slice(0, 3).map((img, i) => (
                        <li key={i} className="text-blue-400 text-xs truncate">{img}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </section>

            {/* Schema Recommendation Card */}
            <section className="bg-gray-900 border border-gray-800 rounded-xl p-6">
              <div className="flex items-center gap-3 mb-4">
                <h2 className="font-semibold text-sm text-gray-300 uppercase tracking-widest">
                  Schema Recommendation
                </h2>
                <span className="bg-violet-900 text-violet-300 text-xs font-bold px-2 py-1 rounded">
                  {result.detected_schema_type}
                </span>
                <span className={`text-xs px-2 py-1 rounded ${
                  result.detection_method === "llm"
                    ? "bg-green-900 text-green-300"
                    : "bg-gray-800 text-gray-400"
                }`}>
                  {result.detection_method === "llm" ? "🤖 LLM-enriched" : "📐 Rule-based"}
                </span>
              </div>

              <pre className="bg-gray-950 rounded-lg p-4 text-xs text-green-300 overflow-x-auto leading-relaxed">
                {JSON.stringify(result.recommended_jsonld, null, 2)}
              </pre>
            </section>

            {/* GEO Tips Card */}
            <section className="bg-gray-900 border border-gray-800 rounded-xl p-6">
              <h2 className="font-semibold text-sm text-gray-300 uppercase tracking-widest mb-4">
                GEO Improvement Tips
              </h2>
              <ul className="space-y-2">
                {result.geo_tips.map((tip, i) => (
                  <li key={i} className="flex gap-2 text-sm text-gray-300">
                    <span className="text-violet-400 mt-0.5">→</span>
                    <span>{tip}</span>
                  </li>
                ))}
              </ul>
            </section>

          </div>
        )}
      </div>
    </main>
  );
}

function Row({ label, value }) {
  return (
    <div>
      <span className="text-gray-500 text-xs uppercase tracking-wide">{label}</span>
      <p className="text-gray-200 text-sm mt-0.5">{value || <span className="text-red-400 italic">Not found</span>}</p>
    </div>
  );
}
