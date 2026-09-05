import type { TechRadarEntry } from "../api";

const RING_COLORS: Record<string, string> = {
  adopt: "#2e7d32",
  trial: "#1565c0",
  assess: "#f9a825",
  hold: "#c62828",
};

const CATEGORY_ICONS: Record<string, string> = {
  language: "📝",
  framework: "🏗️",
  database: "🗄️",
  ci_cd: "🔄",
  container: "📦",
  infra: "☁️",
  observability: "📊",
  messaging: "📡",
  security: "🔒",
  build_tool: "🔧",
  testing: "🧪",
};

interface TechRadarProps {
  entries: TechRadarEntry[];
}

export function TechRadar({ entries }: TechRadarProps) {
  if (entries.length === 0) {
    return <p style={{ color: "#888", fontStyle: "italic" }}>No tech radar data. Analyze a repository first.</p>;
  }

  const byCategory: Record<string, TechRadarEntry[]> = {};
  for (const e of entries) {
    (byCategory[e.category] ??= []).push(e);
  }

  return (
    <div>
      <h3 style={{ marginBottom: "16px" }}>Tech Radar</h3>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: "16px" }}>
        {Object.entries(byCategory).map(([category, tools]) => (
          <div key={category} style={{ border: "1px solid #e0e0e0", borderRadius: "8px", padding: "16px" }}>
            <h4 style={{ marginTop: 0, marginBottom: "12px", textTransform: "capitalize", display: "flex", alignItems: "center", gap: "8px" }}>
              <span>{CATEGORY_ICONS[category] || "📌"}</span>
              {category.replace("_", " ")}
            </h4>
            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              {tools.map((tool) => (
                <div
                  key={tool.tool_name}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    padding: "8px 12px",
                    backgroundColor: "#f5f5f5",
                    borderRadius: "6px",
                    borderLeft: `4px solid ${RING_COLORS[tool.ring] || "#999"}`,
                  }}
                >
                  <div>
                    <div style={{ fontWeight: 600, fontSize: "14px" }}>{tool.tool_name}</div>
                    {tool.version && <div style={{ fontSize: "12px", color: "#666" }}>v{tool.version}</div>}
                  </div>
                  <span
                    style={{
                      fontSize: "11px",
                      fontWeight: 700,
                      textTransform: "uppercase",
                      padding: "2px 8px",
                      borderRadius: "12px",
                      backgroundColor: RING_COLORS[tool.ring] || "#999",
                      color: "white",
                    }}
                  >
                    {tool.ring}
                  </span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
