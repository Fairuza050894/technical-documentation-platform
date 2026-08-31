import type { SonarQubeResult } from "./types";

interface SonarQubeComparisonProps {
  internalScore: number;
  sonarqube: SonarQubeResult;
}

const RATING_COLORS: Record<string, string> = {
  A: "#16a34a",
  B: "#65a30d",
  C: "#f59e0b",
  D: "#dc2626",
  E: "#7f1d1d",
};

export function SonarQubeComparison({ internalScore, sonarqube }: SonarQubeComparisonProps) {
  if (sonarqube.error) {
    return (
      <div className="sq-comparison sq-comparison--error">
        <h3>SonarQube Analysis</h3>
        <p className="sq-error">{sonarqube.error}</p>
      </div>
    );
  }

  const delta = internalScore - sonarqube.total_score;

  return (
    <div className="sq-comparison">
      <div className="sq-header">
        <h3>Internal vs SonarQube</h3>
        <span className="sq-project">{sonarqube.project_key}</span>
      </div>

      {/* Score comparison */}
      <div className="sq-scores">
        <div className="sq-score-card">
          <span className="sq-score-label">Internal</span>
          <span className="sq-score-value" style={{ color: getScoreColor(internalScore) }}>
            {internalScore}
          </span>
        </div>
        <div className="sq-score-delta" style={{ color: delta >= 0 ? "#16a34a" : "#dc2626" }}>
          {delta >= 0 ? "+" : ""}{delta}
        </div>
        <div className="sq-score-card">
          <span className="sq-score-label">SonarQube</span>
          <span className="sq-score-value" style={{ color: getScoreColor(sonarqube.total_score) }}>
            {sonarqube.total_score}
          </span>
        </div>
      </div>

      {/* Rating badges */}
      <div className="sq-ratings">
        <RatingBadge label="Security" rating={sonarqube.security_rating} score={sonarqube.security_score} max={25} />
        <RatingBadge label="Reliability" rating={sonarqube.reliability_rating} score={sonarqube.reliability_score} max={25} />
        <RatingBadge label="Maintainability" rating={sonarqube.sqale_rating} score={sonarqube.maintainability_score} max={25} />
        <RatingBadge label="Coverage" rating={coverageRating(sonarqube.coverage)} score={sonarqube.coverage_score} max={25} />
      </div>

      {/* Metrics grid */}
      <div className="sq-metrics">
        <MetricItem label="Lines of Code" value={sonarqube.ncloc.toLocaleString()} />
        <MetricItem label="Bugs" value={sonarqube.bugs} severity={sonarqube.bugs > 0 ? "warning" : "good"} />
        <MetricItem label="Vulnerabilities" value={sonarqube.vulnerabilities} severity={sonarqube.vulnerabilities > 0 ? "bad" : "good"} />
        <MetricItem label="Code Smells" value={sonarqube.code_smells} severity={sonarqube.code_smells > 50 ? "warning" : sonarqube.code_smells > 0 ? "neutral" : "good"} />
        <MetricItem label="Coverage" value={sonarqube.coverage.toFixed(1) + "%"} severity={sonarqube.coverage > 0 ? "good" : "bad"} />
        <MetricItem label="Duplications" value={sonarqube.duplicated_lines_density.toFixed(1) + "%"} severity={sonarqube.duplicated_lines_density > 5 ? "warning" : "good"} />
        <MetricItem label="Security Hotspots" value={sonarqube.security_hotspots} severity={sonarqube.security_hotspots > 0 ? "warning" : "good"} />
        <MetricItem label="Cognitive Complexity" value={sonarqube.cognitive_complexity} severity={sonarqube.cognitive_complexity > 1000 ? "bad" : sonarqube.cognitive_complexity > 500 ? "warning" : "good"} />
      </div>

      {/* Issues breakdown */}
      <div className="sq-issues">
        <h4>Issues by Severity</h4>
        <div className="sq-issue-bar">
          {sonarqube.issues_blocker > 0 && <span className="sq-issue-segment sq-issue-segment--blocker" style={{ flex: sonarqube.issues_blocker }}>{sonarqube.issues_blocker} Blocker</span>}
          {sonarqube.issues_critical > 0 && <span className="sq-issue-segment sq-issue-segment--critical" style={{ flex: sonarqube.issues_critical }}>{sonarqube.issues_critical} Critical</span>}
          {sonarqube.issues_major > 0 && <span className="sq-issue-segment sq-issue-segment--major" style={{ flex: sonarqube.issues_major }}>{sonarqube.issues_major} Major</span>}
          {sonarqube.issues_minor > 0 && <span className="sq-issue-segment sq-issue-segment--minor" style={{ flex: sonarqube.issues_minor }}>{sonarqube.issues_minor} Minor</span>}
          {sonarqube.issues_info > 0 && <span className="sq-issue-segment sq-issue-segment--info" style={{ flex: sonarqube.issues_info }}>{sonarqube.issues_info} Info</span>}
        </div>
      </div>
    </div>
  );
}

function RatingBadge({ label, rating, score, max }: { label: string; rating: string; score: number; max: number }) {
  const color = RATING_COLORS[rating] || "#9ca3af";
  return (
    <div className="sq-rating-badge">
      <span className="sq-rating-letter" style={{ background: color }}>{rating}</span>
      <div className="sq-rating-info">
        <span className="sq-rating-label">{label}</span>
        <span className="sq-rating-score">{score}/{max}</span>
      </div>
    </div>
  );
}

function MetricItem({ label, value, severity }: { label: string; value: string | number; severity?: "good" | "neutral" | "warning" | "bad" }) {
  const colors = { good: "#16a34a", neutral: "#6b7280", warning: "#f59e0b", bad: "#dc2626" };
  return (
    <div className="sq-metric-item">
      <span className="sq-metric-value" style={severity ? { color: colors[severity] } : undefined}>{value}</span>
      <span className="sq-metric-label">{label}</span>
    </div>
  );
}

function coverageRating(pct: number): string {
  if (pct >= 80) return "A";
  if (pct >= 60) return "B";
  if (pct >= 40) return "C";
  if (pct >= 20) return "D";
  return "E";
}

function getScoreColor(score: number): string {
  if (score >= 70) return "#16a34a";
  if (score >= 40) return "#f59e0b";
  return "#dc2626";
}
