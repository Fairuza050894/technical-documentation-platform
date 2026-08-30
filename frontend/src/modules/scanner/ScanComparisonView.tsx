import { useEffect, useState } from "react";

import { compareScans } from "./api";
import type { ScanComparison, ScanResult } from "./types";

interface ScanComparisonViewProps {
  scan: ScanResult;
  previousScans: ScanResult[];
  onClose: () => void;
}

export function ScanComparisonView({ scan, previousScans, onClose }: ScanComparisonViewProps) {
  const [selectedBeforeId, setSelectedBeforeId] = useState<string>(
    previousScans.length > 0 ? (previousScans[0]?.id ?? "") : ""
  );
  const [comparison, setComparison] = useState<ScanComparison | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!selectedBeforeId) return;
    setLoading(true);
    setError(null);
    compareScans(scan.id, selectedBeforeId)
      .then((result) => {
        setComparison(result);
        setLoading(false);
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Comparison failed");
        setLoading(false);
      });
  }, [scan.id, selectedBeforeId]);

  function getDeltaColor(delta: number, higherIsBetter = true): string {
    if (delta === 0) return "#6b7280";
    const isPositive = higherIsBetter ? delta > 0 : delta < 0;
    return isPositive ? "#16a34a" : "#dc2626";
  }

  function getDeltaIcon(delta: number): string {
    if (delta > 0) return "\u2191";
    if (delta < 0) return "\u2193";
    return "\u2192";
  }

  function formatDelta(delta: number): string {
    if (delta > 0) return "+" + delta;
    return String(delta);
  }

  return (
    <div className="scanner-compare">
      <div className="scanner-compare__header">
        <div>
          <h4>Scan Comparison</h4>
          <p className="scanner-compare__desc">Compare with a previous scan to see changes over time.</p>
        </div>
        <button type="button" className="button button--quiet button--sm" onClick={onClose}>Close</button>
      </div>

      {/* Selector */}
      <div className="scanner-compare__selector">
        <label htmlFor="compare-before">Compare against:</label>
        <select
          id="compare-before"
          value={selectedBeforeId}
          onChange={(e) => setSelectedBeforeId(e.target.value)}
        >
          {previousScans.map((s) => (
            <option key={s.id} value={s.id}>
              {s.repository_name} ({s.branch}) - Score {s.health.score} - {new Date(s.started_at).toLocaleDateString()}
            </option>
          ))}
        </select>
      </div>

      {loading && (
        <div className="scanner-compare__loading">
          <span className="scanner-status-dot scanner-status-dot--analyzing" />
          Comparing scans...
        </div>
      )}

      {error && (
        <div className="scanner-compare__error">{error}</div>
      )}

      {comparison && !loading && (
        <>
          {/* Identical notice */}
          {comparison.is_identical && (
            <div className="scanner-compare__identical">
              <span>{"\u2713"}</span>
              <div>
                <strong>Up to date</strong>
                <p>No changes detected between these two scans.</p>
              </div>
            </div>
          )}

          {/* Score comparison */}
          <div className="scanner-compare__score-row">
            <div className="scanner-compare__score-card scanner-compare__score-card--before">
              <span className="scanner-compare__score-label">Before</span>
              <span className="scanner-compare__score-value">{comparison.health_score_before}</span>
              <span className="scanner-compare__score-sub">/ 100</span>
            </div>
            <div className="scanner-compare__score-arrow">
              <span style={{ color: getDeltaColor(comparison.health_score_delta) }}>
                {getDeltaIcon(comparison.health_score_delta)} {formatDelta(comparison.health_score_delta)}
              </span>
            </div>
            <div className="scanner-compare__score-card scanner-compare__score-card--after">
              <span className="scanner-compare__score-label">After</span>
              <span className="scanner-compare__score-value">{comparison.health_score_after}</span>
              <span className="scanner-compare__score-sub">/ 100</span>
            </div>
          </div>

          {/* Metrics grid */}
          <div className="scanner-compare__metrics">
            {comparison.metrics.map((metric) => (
              <div key={metric.label} className="scanner-compare__metric">
                <span className="scanner-compare__metric-label">{metric.label}</span>
                <div className="scanner-compare__metric-values">
                  <span className="scanner-compare__metric-before">{metric.before}</span>
                  <span className="scanner-compare__metric-arrow" style={{ color: getDeltaColor(metric.value_change, metric.label !== "Vulnerabilities" && metric.label !== "Critical Issues" && metric.label !== "Issues Count") }}>
                    {getDeltaIcon(metric.value_change)} {formatDelta(metric.value_change)}
                  </span>
                  <span className="scanner-compare__metric-after">{metric.after}</span>
                </div>
              </div>
            ))}
          </div>

          {/* Changes detail */}
          <div className="scanner-compare__changes">
            {/* Frameworks */}
            {(comparison.frameworks_added.length > 0 || comparison.frameworks_removed.length > 0) && (
              <div className="scanner-compare__change-section">
                <h5>Framework Changes</h5>
                {comparison.frameworks_added.map((fw) => (
                  <div key={fw} className="scanner-compare__change-item scanner-compare__change-item--added">
                    <span>+</span> {fw}
                  </div>
                ))}
                {comparison.frameworks_removed.map((fw) => (
                  <div key={fw} className="scanner-compare__change-item scanner-compare__change-item--removed">
                    <span>-</span> {fw}
                  </div>
                ))}
              </div>
            )}

            {/* Issues */}
            {(comparison.issues_added.length > 0 || comparison.issues_removed.length > 0) && (
              <div className="scanner-compare__change-section">
                <h5>Issue Changes</h5>
                {comparison.issues_added.map((issue) => (
                  <div key={issue} className="scanner-compare__change-item scanner-compare__change-item--added">
                    <span>+</span> {issue}
                  </div>
                ))}
                {comparison.issues_removed.map((issue) => (
                  <div key={issue} className="scanner-compare__change-item scanner-compare__change-item--removed">
                    <span>-</span> {issue}
                  </div>
                ))}
              </div>
            )}

            {/* No changes */}
            {comparison.frameworks_added.length === 0 && comparison.frameworks_removed.length === 0 && comparison.issues_added.length === 0 && comparison.issues_removed.length === 0 && !comparison.is_identical && (
              <div className="scanner-compare__no-changes">
                Metric values changed but no structural differences detected.
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
