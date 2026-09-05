import { useState } from "react";
import { analyzeRepo } from "../api";

interface AnalyzeFormProps {
  onAnalyze: (snapshot: any) => void;
}

export function AnalyzeForm({ onAnalyze }: AnalyzeFormProps) {
  const [url, setUrl] = useState("https://github.com/Fairuza050894/technical-documentation-platform.git");
  const [branch, setBranch] = useState("main");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const snapshot = await analyzeRepo(url, branch);
      onAnalyze(snapshot);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} style={{ marginBottom: "24px", padding: "16px", border: "1px solid #e0e0e0", borderRadius: "8px" }}>
      <h3 style={{ marginTop: 0, marginBottom: "12px" }}>Analyze Repository</h3>
      <div style={{ display: "flex", gap: "12px", flexWrap: "wrap", alignItems: "flex-end" }}>
        <div style={{ flex: "1 1 300px" }}>
          <label style={{ display: "block", fontSize: "12px", fontWeight: 600, marginBottom: "4px", color: "#555" }}>Repository URL</label>
          <input
            type="text"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            style={{ width: "100%", padding: "8px 12px", border: "1px solid #ccc", borderRadius: "4px", fontSize: "14px" }}
          />
        </div>
        <div style={{ flex: "0 0 150px" }}>
          <label style={{ display: "block", fontSize: "12px", fontWeight: 600, marginBottom: "4px", color: "#555" }}>Branch</label>
          <input
            type="text"
            value={branch}
            onChange={(e) => setBranch(e.target.value)}
            style={{ width: "100%", padding: "8px 12px", border: "1px solid #ccc", borderRadius: "4px", fontSize: "14px" }}
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          style={{
            padding: "8px 20px",
            backgroundColor: loading ? "#999" : "#0066cc",
            color: "white",
            border: "none",
            borderRadius: "4px",
            cursor: loading ? "not-allowed" : "pointer",
            fontSize: "14px",
            fontWeight: 600,
          }}
        >
          {loading ? "Analyzing..." : "Analyze"}
        </button>
      </div>
      {error && <p style={{ color: "#d32f2f", marginTop: "8px", fontSize: "13px" }}>{error}</p>}
    </form>
  );
}
