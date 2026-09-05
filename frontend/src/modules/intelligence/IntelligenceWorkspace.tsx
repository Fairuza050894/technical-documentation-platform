import { useState, useCallback } from "react";
import type { Snapshot, TechRadarEntry, Dashboard } from "./api";
import { getTechRadar, getDashboard } from "./api";
import { AnalyzeForm } from "./components/AnalyzeForm";
import { TechRadar } from "./components/TechRadar";
import { DependencyGraphView } from "./components/DependencyGraph";
import { VulnerabilityAlerts } from "./components/VulnerabilityAlerts";

type Tab = "overview" | "radar" | "dependencies" | "vulnerabilities" | "changes";

export function IntelligenceWorkspace() {
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null);
  const [radar, setRadar] = useState<TechRadarEntry[]>([]);
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>("overview");
  const [loading, setLoading] = useState(false);

  const handleAnalyze = useCallback(async (s: Snapshot) => {
    setSnapshot(s);
    setLoading(true);
    try {
      const [radarData, dashData] = await Promise.all([
        getTechRadar(s.repo_id),
        getDashboard(s.repo_id),
      ]);
      setRadar(radarData);
      setDashboard(dashData);
    } catch (err) {
      console.error("Failed to load intelligence data:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  const tabs: { key: Tab; label: string }[] = [
    { key: "overview", label: "Overview" },
    { key: "radar", label: `Tech Radar (${radar.length})` },
    { key: "dependencies", label: `Dependencies (${snapshot?.dependency_graphs.reduce((a, g) => a + g.direct_count, 0) ?? 0})` },
    { key: "vulnerabilities", label: `Vulnerabilities (${snapshot?.vulnerability_alerts.length ?? 0})` },
    { key: "changes", label: `Changes (${snapshot?.change_events.length ?? 0})` },
  ];

  return (
    <div style={{ padding: "24px", maxWidth: "1200px", margin: "0 auto" }}>
      <h2 style={{ marginTop: 0, marginBottom: "8px" }}>Repository Intelligence</h2>
      <p style={{ color: "#666", marginBottom: "24px", fontSize: "14px" }}>
        Analyze repositories to detect tech stack, dependencies, vulnerabilities, and changes.
      </p>

      <AnalyzeForm onAnalyze={handleAnalyze} />

      {snapshot && (
        <>
          {/* Dashboard Cards */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))", gap: "16px", marginBottom: "24px" }}>
            <DashboardCard label="Tech Stack" value={snapshot.tech_stack.length.toString()} color="#1565c0" />
            <DashboardCard label="Packages" value={snapshot.total_packages.toString()} color="#2e7d32" />
            <DashboardCard label="Vulnerabilities" value={snapshot.vulnerability_alerts.length.toString()} color="#c62828" />
            <DashboardCard label="Critical" value={snapshot.critical_vulnerabilities.toString()} color="#d32f2f" />
            <DashboardCard label="Changes" value={snapshot.change_events.length.toString()} color="#f9a825" />
          </div>

          {/* Repo Info */}
          <div style={{ marginBottom: "20px", padding: "12px 16px", backgroundColor: "#f8f9fa", borderRadius: "6px", fontSize: "13px" }}>
            <strong>Repo:</strong> {snapshot.repo_url} | <strong>Branch:</strong> {snapshot.branch} | <strong>ID:</strong> <code style={{ fontSize: "12px" }}>{snapshot.id}</code>
          </div>

          {/* Tabs */}
          <div style={{ display: "flex", gap: "4px", borderBottom: "2px solid #e0e0e0", marginBottom: "20px" }}>
            {tabs.map((t) => (
              <button
                key={t.key}
                onClick={() => setActiveTab(t.key)}
                style={{
                  padding: "10px 16px",
                  border: "none",
                  backgroundColor: activeTab === t.key ? "#fff" : "transparent",
                  borderBottom: activeTab === t.key ? "2px solid #0066cc" : "2px solid transparent",
                  color: activeTab === t.key ? "#0066cc" : "#555",
                  fontWeight: activeTab === t.key ? 600 : 400,
                  cursor: "pointer",
                  fontSize: "14px",
                  marginBottom: "-2px",
                }}
              >
                {t.label}
              </button>
            ))}
          </div>

          {loading && <p style={{ color: "#666", fontStyle: "italic" }}>Loading intelligence data...</p>}

          {/* Tab Content */}
          {activeTab === "overview" && (
            <div>
              <h3 style={{ marginBottom: "12px" }}>Detected Tech Stack</h3>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "8px", marginBottom: "24px" }}>
                {snapshot.tech_stack.map((tool) => (
                  <span
                    key={tool.name}
                    style={{
                      padding: "6px 12px",
                      backgroundColor: "#e3f2fd",
                      color: "#1565c0",
                      borderRadius: "16px",
                      fontSize: "13px",
                      fontWeight: 500,
                      display: "flex",
                      alignItems: "center",
                      gap: "6px",
                    }}
                  >
                    {tool.name}
                    <span style={{ fontSize: "11px", color: "#666", fontWeight: 400 }}>
                      ({tool.category})
                    </span>
                  </span>
                ))}
              </div>

              {dashboard && (
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: "12px" }}>
                  {Object.entries(dashboard.tech_stack_summary).map(([cat, count]) => (
                    <div key={cat} style={{ padding: "12px", border: "1px solid #e0e0e0", borderRadius: "6px" }}>
                      <div style={{ fontSize: "12px", color: "#666", textTransform: "capitalize" }}>{cat.replace("_", " ")}</div>
                      <div style={{ fontSize: "24px", fontWeight: 700, color: "#333" }}>{count}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === "radar" && <TechRadar entries={radar} />}
          {activeTab === "dependencies" && <DependencyGraphView graphs={snapshot.dependency_graphs} />}
          {activeTab === "vulnerabilities" && <VulnerabilityAlerts alerts={snapshot.vulnerability_alerts} />}
          {activeTab === "changes" && (
            <div>
              <h3 style={{ marginBottom: "16px" }}>Change Events</h3>
              {snapshot.change_events.length === 0 ? (
                <p style={{ color: "#888", fontStyle: "italic" }}>No changes detected.</p>
              ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                  {snapshot.change_events.map((e, idx) => (
                    <div key={idx} style={{ padding: "12px", border: "1px solid #e0e0e0", borderRadius: "6px" }}>
                      <div style={{ display: "flex", justifyContent: "space-between" }}>
                        <span style={{ fontWeight: 600, fontSize: "13px" }}>{e.change_type.replace("_", " ")}</span>
                        <span style={{ fontSize: "11px", textTransform: "uppercase", color: "#666" }}>{e.severity}</span>
                      </div>
                      <div style={{ fontSize: "13px", color: "#444", marginTop: "4px" }}>{e.description}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </>
      )}

      {!snapshot && (
        <div style={{ textAlign: "center", padding: "60px 20px", color: "#888" }}>
          <div style={{ fontSize: "48px", marginBottom: "16px" }}>🔍</div>
          <h3 style={{ marginBottom: "8px", color: "#555" }}>No Analysis Yet</h3>
          <p style={{ fontSize: "14px" }}>Enter a repository URL above and click Analyze to get started.</p>
        </div>
      )}
    </div>
  );
}

function DashboardCard({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div style={{ padding: "16px", borderRadius: "8px", border: "1px solid #e0e0e0", textAlign: "center" }}>
      <div style={{ fontSize: "28px", fontWeight: 700, color }}>{value}</div>
      <div style={{ fontSize: "12px", color: "#666", marginTop: "4px", textTransform: "uppercase", letterSpacing: "0.5px" }}>{label}</div>
    </div>
  );
}
