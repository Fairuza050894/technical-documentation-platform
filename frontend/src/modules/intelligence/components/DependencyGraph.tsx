import type { DependencyGraph as DepGraph } from "../api";

interface DependencyGraphProps {
  graphs: DepGraph[];
}

export function DependencyGraphView({ graphs }: DependencyGraphProps) {
  if (graphs.length === 0) {
    return <p style={{ color: "#888", fontStyle: "italic" }}>No dependency data available.</p>;
  }

  return (
    <div>
      <h3 style={{ marginBottom: "16px" }}>Dependency Graphs</h3>
      <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
        {graphs.map((g, idx) => (
          <div key={idx} style={{ border: "1px solid #e0e0e0", borderRadius: "8px", padding: "16px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
              <h4 style={{ margin: 0, textTransform: "uppercase", fontSize: "14px", letterSpacing: "0.5px" }}>
                {g.ecosystem}
              </h4>
              <div style={{ display: "flex", gap: "12px", fontSize: "12px" }}>
                <span style={{ color: "#2e7d32" }}>Direct: {g.direct_count}</span>
                <span style={{ color: "#1565c0" }}>Transitive: {g.transitive_count}</span>
                {g.vulnerable_count > 0 && <span style={{ color: "#c62828" }}>Vulnerable: {g.vulnerable_count}</span>}
              </div>
            </div>
            <div style={{ maxHeight: "300px", overflowY: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "13px" }}>
                <thead>
                  <tr style={{ borderBottom: "2px solid #e0e0e0" }}>
                    <th style={{ textAlign: "left", padding: "8px" }}>Package</th>
                    <th style={{ textAlign: "left", padding: "8px" }}>Version</th>
                    <th style={{ textAlign: "center", padding: "8px" }}>Type</th>
                  </tr>
                </thead>
                <tbody>
                  {g.packages.map((pkg, pidx) => (
                    <tr key={pidx} style={{ borderBottom: "1px solid #f0f0f0" }}>
                      <td style={{ padding: "6px 8px", fontFamily: "monospace", fontSize: "12px" }}>{pkg.name}</td>
                      <td style={{ padding: "6px 8px", color: "#666" }}>{pkg.version}</td>
                      <td style={{ padding: "6px 8px", textAlign: "center" }}>
                        <span
                          style={{
                            fontSize: "10px",
                            fontWeight: 700,
                            textTransform: "uppercase",
                            padding: "2px 6px",
                            borderRadius: "4px",
                            backgroundColor: pkg.direct ? "#e3f2fd" : "#f5f5f5",
                            color: pkg.direct ? "#1565c0" : "#666",
                          }}
                        >
                          {pkg.direct ? "direct" : "transitive"}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
