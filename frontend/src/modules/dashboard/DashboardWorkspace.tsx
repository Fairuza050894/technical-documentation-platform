import { useEffect, useState } from "react";
import { getDashboard } from "../scanner/api";
import type { DashboardResponse, RepoSummary } from "../scanner/types";
import { formatNumber, getScoreClass, formatDate, getTimeAgo } from "../scanner/ScannerWorkspace";
import { TrendBar } from "../../shared/ui/TrendBar";

interface TrendDataPoint {
  date: string;
  avg_score: number;
  total_repos: number;
  total_scans: number;
  critical_vulns: number;
}

export function DashboardWorkspace() {
  const [dashboard, setDashboard] = useState<DashboardResponse | null>(null);
  const [trendData, setTrendData] = useState<TrendDataPoint[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [timeRange, setTimeRange] = useState<"7d" | "30d" | "90d">("30d");

  useEffect(() => {
    const controller = new AbortController();
    async function load() {
      setIsLoading(true);
      try {
        const [dash, trends] = await Promise.all([
          getDashboard(controller.signal),
          fetchTrendData(timeRange, controller.signal),
        ]);
        setDashboard(dash);
        setTrendData(trends);
      } catch {
        // ignore
      } finally {
        setIsLoading(false);
      }
    }
    void load();
    return () => controller.abort();
  }, [timeRange]);

  const repos: RepoSummary[] = dashboard?.repos ?? [];
  const healthyRepos = repos.filter((r) => r.health_score >= 70).length;
  const degradedRepos = repos.filter((r) => r.health_score >= 40 && r.health_score < 70).length;
  const criticalRepos = repos.filter((r) => r.health_score < 40).length;
  const avgScore = dashboard?.avg_health_score ?? 0;
  const totalVulns = repos.reduce((sum, r) => sum + r.vulnerabilities, 0);

  const scoreTrend = trendData.map((d) => d.avg_score);
  const vulnTrend = trendData.map((d) => d.critical_vulns);
  const reposTrend = trendData.map((d) => d.total_repos);
  const scansTrend = trendData.map((d) => d.total_scans);

  if (isLoading) {
    return <DashboardSkeleton />;
  }

  return (
    <div className="dashboard-workspace">
      <header className="dashboard-header">
        <div>
          <p className="eyebrow">Portfolio overview</p>
          <h1>Repository Health Dashboard</h1>
        </div>
        <div className="dashboard-header__actions">
          <div className="dashboard-timerange" role="group" aria-label="Time range">
            {(["7d", "30d", "90d"] as const).map((range) => (
              <button
                key={range}
                type="button"
                className={`dashboard-timerange__btn ${timeRange === range ? "dashboard-timerange__btn--active" : ""}`}
                onClick={() => setTimeRange(range)}
                aria-pressed={timeRange === range}
              >
                {range === "7d" ? "7 days" : range === "30d" ? "30 days" : "90 days"}
              </button>
            ))}
          </div>
        </div>
      </header>

      {/* KPI Cards */}
      <section className="dashboard-kpis" aria-label="Key metrics">
        <div className="kpi-card" style={{ borderColor: avgScore >= 70 ? "var(--color-score-high-subtle)" : avgScore >= 40 ? "var(--color-score-medium-subtle)" : "var(--color-score-low-subtle)" }}>
          <div className="kpi-card__value" style={{ color: avgScore >= 70 ? "var(--color-score-high)" : avgScore >= 40 ? "var(--color-score-medium)" : "var(--color-score-low)" }}>
            {Math.round(avgScore)}
          </div>
          <div className="kpi-card__label">Avg Health Score</div>
          <TrendBar
            data={scoreTrend}
            height={20}
            width={120}
            minValue={0}
            maxValue={100}
            className="kpi-card__trend-bar"
          />
        </div>
        <div className="kpi-card">
          <div className="kpi-card__value">{repos.length}</div>
          <div className="kpi-card__label">Repositories</div>
          <div className="kpi-card__trend">{reposTrend.length > 0 ? `▲ ${reposTrend[reposTrend.length - 1]} recent` : "—"}</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-card__value">{dashboard?.total_scans ?? 0}</div>
          <div className="kpi-card__label">Total Scans</div>
          <div className="kpi-card__trend">{scansTrend.length > 0 ? `▲ ${scansTrend[scansTrend.length - 1]} recent` : "—"}</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-card__value">{totalVulns}</div>
          <div className="kpi-card__label">Vulnerabilities</div>
          <div className="kpi-card__trend">{totalVulns === 0 ? "✓ Clear" : `▼ ${totalVulns}`}</div>
        </div>
      </section>

      {/* Health Distribution */}
      <section className="dashboard-section" aria-labelledby="health-dist-title">
        <h2 id="health-dist-title">Repository Health Distribution</h2>
        <div className="dashboard-distribution">
          <div className="distribution-bar" role="img" aria-label={`Health: ${healthyRepos} healthy, ${degradedRepos} degraded, ${criticalRepos} critical`}>
            <div
              className="distribution-bar__segment distribution-bar__segment--healthy"
              style={{ width: repos.length > 0 ? `${(healthyRepos / repos.length) * 100}%` : "0%" }}
            />
            <div
              className="distribution-bar__segment distribution-bar__segment--degraded"
              style={{ width: repos.length > 0 ? `${(degradedRepos / repos.length) * 100}%` : "0%" }}
            />
            <div
              className="distribution-bar__segment distribution-bar__segment--critical"
              style={{ width: repos.length > 0 ? `${(criticalRepos / repos.length) * 100}%` : "0%" }}
            />
          </div>
          <div className="distribution-legend">
            <span className="legend-item legend-item--healthy">
              <span className="legend-dot" style={{ background: "var(--color-success)" }} /> Healthy ({healthyRepos})
            </span>
            <span className="legend-item legend-item--degraded">
              <span className="legend-dot" style={{ background: "var(--color-warning)" }} /> Degraded ({degradedRepos})
            </span>
            <span className="legend-item legend-item--critical">
              <span className="legend-dot" style={{ background: "var(--color-danger)" }} /> Critical ({criticalRepos})
            </span>
          </div>
        </div>
      </section>

      {/* Repository Table */}
      <section className="dashboard-section" aria-labelledby="repos-title">
        <h2 id="repos-title">Repository Details</h2>
        <div className="table-frame">
          <table>
            <thead>
              <tr>
                <th>Repository</th>
                <th>Branch</th>
                <th>Health Score</th>
                <th>Vulnerabilities</th>
                <th>Last Scan</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {repos.map((repo) => {
                const score = repo.health_score;
                const vulns = repo.vulnerabilities;
                return (
                  <tr key={repo.latest_scan_id || repo.repository_name}>
                    <td>
                      <strong>{repo.repository_name}</strong>
                      {repo.repository_url && <span className="table-secondary-text">{repo.repository_url}</span>}
                    </td>
                    <td>
                      <span className="scanner-content__branch">{repo.branch}</span>
                    </td>
                    <td>
                      <span className={`score-inline ${getScoreClass(score)}`}>{score}</span>
                    </td>
                    <td>
                      {vulns > 0 ? (
                        <span style={{ color: vulns > 10 ? "var(--color-danger)" : "var(--color-warning)" }}>{vulns}</span>
                      ) : (
                        <span style={{ color: "var(--color-success)" }}>0</span>
                      )}
                    </td>
                    <td>{repo.last_scan_at && formatDate(repo.last_scan_at)}</td>
                    <td>
                      <span className={score >= 70 ? "status-badge status-badge--approved" : score >= 40 ? "status-badge" : "status-badge status-badge--danger"}>
                        {score >= 70 ? "Healthy" : score >= 40 ? "Degraded" : "Critical"}
                      </span>
                    </td>
                  </tr>
                );
              })}
              {repos.length === 0 && (
                <tr>
                  <td colSpan={7} style={{ textAlign: "center", padding: "32px" }}>
                    <div className="empty-state empty-state--compact">
                      <h4>No repositories</h4>
                      <p>Add repositories using the Scanner to see portfolio health.</p>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

function DashboardSkeleton() {
  return (
    <div className="dashboard-workspace">
      <header className="dashboard-header">
        <div className="skeleton" style={{ height: "24px", width: "300px" }} />
        <div className="skeleton" style={{ height: "32px", width: "400px" }} />
      </header>
      <section className="dashboard-kpis">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="kpi-card skeleton" style={{ height: "80px" }} />
        ))}
      </section>
      <section className="dashboard-section">
        <div className="skeleton" style={{ height: "20px", marginBottom: "8px" }} />
        <div className="distribution-bar" style={{ height: "10px" }} />
      </section>
      <section className="dashboard-section">
        <div className="skeleton" style={{ height: "20px", marginBottom: "8px" }} />
        <table>
          <tbody>
            {[1, 2, 3, 4, 5].map((i) => (
              <tr key={i}>
                {[1, 2, 3, 4, 5, 6, 7].map((j) => (
                  <td key={j}><div className="skeleton skeleton-text" style={{ width: "80%" }} /></td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}

async function fetchTrendData(range: "7d" | "30d" | "90d", signal?: AbortSignal): Promise<TrendDataPoint[]> {
  const days = range === "7d" ? 7 : range === "30d" ? 30 : 90;
  // In production, this would call an API endpoint
  // For now, generate mock data based on current dashboard
  const now = Date.now();
  const dayMs = 24 * 60 * 60 * 1000;
  const data: TrendDataPoint[] = [];
  for (let i = days - 1; i >= 0; i--) {
    const date = new Date(now - i * dayMs);
    data.push({
      date: date.toISOString().split("T")[0] || "",
      avg_score: Math.max(30, Math.min(95, 65 + Math.sin(i * 0.3) * 15 + (Math.random() - 0.5) * 10)),
      total_repos: Math.max(1, 12 + Math.floor(Math.sin(i * 0.2) * 3)),
      total_scans: Math.max(0, 45 + Math.floor(Math.sin(i * 0.4) * 15)),
      critical_vulns: Math.max(0, Math.floor(8 + Math.sin(i * 0.5) * 5 + (Math.random() - 0.5) * 4)),
    });
  }
  return data;
}