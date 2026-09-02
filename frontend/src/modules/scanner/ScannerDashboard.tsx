import { useCallback, useEffect, useState } from "react";
import { getDashboard } from "./api";
import type { DashboardAlert, DashboardResponse, RepoSummary } from "./types";

interface ScannerDashboardProps {
  onSelectScan?: (scanId: string) => void;
  onSelectRepo?: (repoUrl: string) => void;
}

export function ScannerDashboard({ onSelectScan, onSelectRepo }: ScannerDashboardProps) {
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async (signal?: AbortSignal) => {
    try {
      const result = await getDashboard(signal);
      setData(result);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    void load(controller.signal);
    return () => controller.abort();
  }, [load]);

  if (loading) {
    return (
      <div className="scanner-dashboard">
        <div className="dashboard-loading">Loading dashboard...</div>
      </div>
    );
  }

  if (!data || data.total_repos === 0) {
    return (
      <div className="scanner-dashboard">
        <div className="dashboard-empty">
          <h3>No scan data yet</h3>
          <p>Start scanning repositories to see your dashboard overview.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="scanner-dashboard">
      <div className="dashboard-summary">
        <div className="dashboard-stat">
          <span className="dashboard-stat__value">{data.total_repos}</span>
          <span className="dashboard-stat__label">Repositories</span>
        </div>
        <div className="dashboard-stat">
          <span className="dashboard-stat__value">{data.total_scans}</span>
          <span className="dashboard-stat__label">Total Scans</span>
        </div>
        <div className="dashboard-stat">
          <span className="dashboard-stat__value" style={{ color: getScoreColor(data.avg_health_score) }}>{data.avg_health_score}</span>
          <span className="dashboard-stat__label">Avg Score</span>
        </div>
        <div className="dashboard-stat">
          <span className="dashboard-stat__value" style={{ color: data.alerts.length > 0 ? "#dc2626" : "#16a34a" }}>{data.alerts.length}</span>
          <span className="dashboard-stat__label">Alerts</span>
        </div>
      </div>

      {data.alerts.length > 0 && (
        <div className="dashboard-alerts">
          <h3>Alerts</h3>
          <div className="dashboard-alerts__list">
            {data.alerts.map((alert, i) => (
              <div key={i} className={"dashboard-alert dashboard-alert--" + alert.severity}>
                <span className="dashboard-alert__icon">{alert.severity === "critical" ? "\u26A0" : "\u25B2"}</span>
                <div className="dashboard-alert__content">
                  <span className="dashboard-alert__repo">{alert.repository_name}</span>
                  <span className="dashboard-alert__message">{alert.message}</span>
                </div>
                {alert.scan_id && (
                  <button type="button" className="dashboard-alert__action" onClick={() => onSelectScan?.(alert.scan_id)}>View</button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="dashboard-repos">
        <h3>Repositories</h3>
        <div className="dashboard-repo-grid">
          {data.repos.map((repo) => (
            <RepoCard key={repo.repository_url} repo={repo} onSelectScan={onSelectScan} onSelectRepo={onSelectRepo} />
          ))}
        </div>
      </div>
    </div>
  );
}

function RepoCard({ repo, onSelectScan, onSelectRepo }: { repo: RepoSummary; onSelectScan?: (id: string) => void; onSelectRepo?: (url: string) => void }) {
  const trendPoints = repo.score_trend.map((t) => t.score);
  const lastPt = trendPoints.length > 0 ? trendPoints[trendPoints.length - 1] : undefined;
  const prevPt = trendPoints.length > 1 ? trendPoints[trendPoints.length - 2] : undefined;
  const latestTrend = (lastPt !== undefined && prevPt !== undefined) ? lastPt - prevPt : 0;

  return (
    <div className="dashboard-repo-card" onClick={() => onSelectRepo?.(repo.repository_url)} role="button" tabIndex={0} onKeyDown={(e) => { if (e.key === "Enter") onSelectRepo?.(repo.repository_url); }}>
      <div className="dashboard-repo-card__header">
        <span className="dashboard-repo-card__name">{repo.repository_name}</span>
        <span className="dashboard-repo-card__branch">{repo.branch}</span>
      </div>

      <div className="dashboard-repo-card__scores">
        <div className="dashboard-repo-card__score" style={{ color: getScoreColor(repo.health_score), background: getScoreBg(repo.health_score) }}>
          {repo.health_score}
        </div>
        {repo.sonarqube_score !== null && (
          <>
            <span className="dashboard-repo-card__vs">vs</span>
            <div className="dashboard-repo-card__score dashboard-repo-card__score--sq" style={{ color: getScoreColor(repo.sonarqube_score), background: getScoreBg(repo.sonarqube_score) }}>
              {repo.sonarqube_score}
            </div>
          </>
        )}
        {latestTrend !== 0 && (
          <span className="dashboard-repo-card__trend" style={{ color: latestTrend > 0 ? "#16a34a" : "#dc2626" }}>
            {latestTrend > 0 ? "\u2191" : "\u2193"}{Math.abs(latestTrend)}
          </span>
        )}
      </div>

      {trendPoints.length > 1 && (
        <div className="dashboard-repo-card__sparkline">
          <Sparkline values={trendPoints} width={120} height={30} />
        </div>
      )}

      <div className="dashboard-repo-card__metrics">
        <span className="dashboard-repo-card__metric">{repo.total_files} files</span>
        <span className="dashboard-repo-card__metric">{repo.frameworks.slice(0, 2).join(", ") || "No frameworks"}</span>
        <span className="dashboard-repo-card__metric">{repo.tests_passed}/{repo.total_tests} tests</span>
        {repo.lint_issues > 0 && <span className="dashboard-repo-card__metric dashboard-repo-card__metric--warn">{repo.lint_issues} lint</span>}
        {repo.vulnerabilities > 0 && <span className="dashboard-repo-card__metric dashboard-repo-card__metric--bad">{repo.vulnerabilities} vulns</span>}
      </div>

      <div className="dashboard-repo-card__footer">
        <span className="dashboard-repo-card__scans">{repo.scan_count} scans</span>
        <span className="dashboard-repo-card__time">{getTimeAgo(repo.last_scan_at)}</span>
        <button type="button" className="dashboard-repo-card__view" onClick={(e) => { e.stopPropagation(); onSelectScan?.(repo.latest_scan_id); }}>View Scan</button>
      </div>
    </div>
  );
}

function Sparkline({ values, width, height }: { values: number[]; width: number; height: number }) {
  if (values.length < 2) return null;
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const padding = 2;

  const points = values.map((v, i) => {
    const x = padding + (i / (values.length - 1)) * (width - padding * 2);
    const y = height - padding - ((v - min) / range) * (height - padding * 2);
    return `${x},${y}`;
  });

  const lastValue = values[values.length - 1] ?? 0;
  const color = lastValue >= 70 ? "#16a34a" : lastValue >= 40 ? "#f59e0b" : "#dc2626";

  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
      <polyline fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" points={points.join(" ")} />
      <circle cx={(points[points.length - 1] ?? "0,0").split(",")[0]} cy={(points[points.length - 1] ?? "0,0").split(",")[1]} r="3" fill={color} />
    </svg>
  );
}

function getScoreColor(score: number): string {
  if (score >= 70) return "#16a34a";
  if (score >= 40) return "#f59e0b";
  return "#dc2626";
}

function getScoreBg(score: number): string {
  if (score >= 70) return "#dcfce7";
  if (score >= 40) return "#fef3c7";
  return "#fef2f2";
}

function getTimeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return mins + "m ago";
  const hours = Math.floor(mins / 60);
  if (hours < 24) return hours + "h ago";
  const days = Math.floor(hours / 24);
  return days + "d ago";
}
