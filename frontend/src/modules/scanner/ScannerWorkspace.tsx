import { useCallback, useEffect, useRef, useState } from "react";

import { deleteScan, generateDocuments, getDashboard, getScan, listGeneratedDocuments, listScans, rescanScan, startScan } from "./api";
import type { GeneratedDocument } from "./api";
import { MarkdownPreview } from "./MarkdownPreview";
import { ScanComparisonView } from "./ScanComparisonView";
import { SonarQubeComparison } from "./SonarQubeComparison";
import { WebhookEventsPanel } from "./WebhookEventsPanel";
import type { DashboardResponse, HealthLevel, RepoSummary, ScanResult, SonarQubeResult } from "./types";
import { HEALTH_COLORS, PRIORITY_LABELS, STATUS_LABELS, STATUS_STEPS } from "./types";

interface ScannerWorkspaceProps {
  embedded?: boolean;
}

type DetailTab = "overview" | "tech" | "tests" | "security" | "documents" | "sonarqube" | "webhooks";

interface RepoGroup {
  repoName: string;
  repoUrl: string;
  scans: ScanResult[];
  latest: ScanResult;
}

export function ScannerWorkspace({ embedded = false }: ScannerWorkspaceProps) {
  const [scans, setScans] = useState<ScanResult[]>([]);
  const [dashboard, setDashboard] = useState<DashboardResponse | null>(null);
  const [selectedScan, setSelectedScan] = useState<ScanResult | null>(null);
  const [selectedRepoUrl, setSelectedRepoUrl] = useState<string | null>(null);
  const [repoUrl, setRepoUrl] = useState("");
  const [branch, setBranch] = useState("main");
  const [isBusy, setIsBusy] = useState(false);
  const [activeTab, setActiveTab] = useState<DetailTab>("overview");
  const [generatedDocs, setGeneratedDocs] = useState<GeneratedDocument[]>([]);
  const [compareTarget, setCompareTarget] = useState<string | null>(null);
    const [searchQuery, setSearchQuery] = useState("");
  const [sortBy, setSortBy] = useState<"score" | "name" | "recent">("score");
  const [showScanForm, setShowScanForm] = useState(false);
  const [selectedSuggestions, setSelectedSuggestions] = useState<Set<string>>(new Set());
  const [expandedDocs, setExpandedDocs] = useState<Set<string>>(new Set());
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const loadScans = useCallback(async (signal?: AbortSignal) => {
    try {
      const data = await listScans(signal);
      setScans(data.items);
    } catch {
      // ignore
    }
  }, []);

  const loadDashboard = useCallback(async (signal?: AbortSignal) => {
    try {
      const data = await getDashboard(signal);
      setDashboard(data);
    } catch {
      // ignore
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    void loadScans(controller.signal);
    void loadDashboard(controller.signal);
    return () => controller.abort();
  }, [loadScans, loadDashboard]);

  useEffect(() => {
    if (selectedScan && (selectedScan.status === "PENDING" || selectedScan.status === "CLONING" || selectedScan.status === "ANALYZING" || selectedScan.status === "TESTING" || selectedScan.status === "GENERATING")) {
      pollRef.current = setInterval(async () => {
        try {
          const updated = await getScan(selectedScan.id);
          setSelectedScan(updated);
          void loadScans();
          void loadDashboard();
          if (updated.status === "COMPLETED" || updated.status === "FAILED") {
            if (pollRef.current) clearInterval(pollRef.current);
          }
        } catch {
          if (pollRef.current) clearInterval(pollRef.current);
        }
      }, 3000);
    }
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [selectedScan, loadScans, loadDashboard]);

  useEffect(() => {
    if (selectedScan) {
      void listGeneratedDocuments(selectedScan.id).then(setGeneratedDocs).catch(() => setGeneratedDocs([]));
    }
  }, [selectedScan]);

  // Group scans by repo
  const repoGroups: RepoGroup[] = [];
  const repoMap = new Map<string, ScanResult[]>();
  for (const scan of scans) {
    const existing = repoMap.get(scan.repository_url) ?? [];
    existing.push(scan);
    repoMap.set(scan.repository_url, existing);
  }
  for (const [url, repoScans] of repoMap) {
    const sorted = [...repoScans].sort((a, b) => new Date(b.started_at).getTime() - new Date(a.started_at).getTime());
    const first = sorted[0];
    if (first) {
      repoGroups.push({
        repoName: first.repository_name,
        repoUrl: url,
        scans: sorted,
        latest: first,
      });
    }
  }

  // Filter and sort
  const filteredGroups = repoGroups
    .filter((g) => {
      if (!searchQuery) return true;
      const q = searchQuery.toLowerCase();
      return g.repoName.toLowerCase().includes(q) || g.repoUrl.toLowerCase().includes(q);
    })
    .sort((a, b) => {
      if (sortBy === "score") return a.latest.health.score - b.latest.health.score;
      if (sortBy === "name") return a.repoName.localeCompare(b.repoName);
      return new Date(b.latest.started_at).getTime() - new Date(a.latest.started_at).getTime();
    });

  // Auto-select first repo if none selected
  useEffect(() => {
    if (!selectedRepoUrl && filteredGroups.length > 0) {
      const firstGroup = filteredGroups[0];
      if (firstGroup) {
        setSelectedRepoUrl(firstGroup.repoUrl);
        setSelectedScan(firstGroup.latest);
      }
    }
  }, [filteredGroups, selectedRepoUrl]);

  const selectedGroup = filteredGroups.find((g) => g.repoUrl === selectedRepoUrl);

  const handleStartScan = async () => {
    if (!repoUrl.trim()) return;
    setIsBusy(true);
    try {
      const scan = await startScan(repoUrl.trim(), branch.trim() || "main");
      setSelectedScan(scan);
      setSelectedRepoUrl(scan.repository_url);
      setRepoUrl("");
      setBranch("main");
      setShowScanForm(false);
      await loadScans();
      await loadDashboard();
    } catch (err) {
      console.error(err);
    } finally {
      setIsBusy(false);
    }
  };

  const handleRescan = async (scanId: string) => {
    setIsBusy(true);
    try {
      const newScan = await rescanScan(scanId);
      setSelectedScan(newScan);
      await loadScans();
      await loadDashboard();
    } catch (err) {
      console.error(err);
    } finally {
      setIsBusy(false);
    }
  };

  const handleDelete = async (scanId: string) => {
    await deleteScan(scanId);
    if (selectedScan?.id === scanId) {
      setSelectedScan(null);
    }
    await loadScans();
    await loadDashboard();
  };

  const handleGenerate = async (scanId: string) => {
    setIsBusy(true);
    try {
      await generateDocuments(scanId, []);
      const docs = await listGeneratedDocuments(scanId);
      setGeneratedDocs(docs);
      setActiveTab("documents");
    } catch (err) {
      console.error(err);
    } finally {
      setIsBusy(false);
    }
  };

  const handleSelectRepo = (repoUrl: string) => {
    setSelectedRepoUrl(repoUrl);
    const group = repoGroups.find((g) => g.repoUrl === repoUrl);
    if (group) {
      setSelectedScan(group.latest);
    }
    setActiveTab("overview");
    setCompareTarget(null);
  };

  const handleSelectScan = (scan: ScanResult) => {
    setSelectedScan(scan);
    setActiveTab("overview");
    setCompareTarget(null);
  };

  return (
    <div className="scanner-unified">
      {/* Summary Header */}
      <div className="scanner-header">
        <div className="scanner-header__title">
          <h1>Repository Scanner</h1>
          <span className="scanner-header__subtitle">Code health, analysis, and documentation</span>
        </div>
        <div className="scanner-header__stats">
          <div className="scanner-header__stat">
            <span className="scanner-header__stat-value">{dashboard?.total_repos ?? repoGroups.length}</span>
            <span className="scanner-header__stat-label">Repos</span>
          </div>
          <div className="scanner-header__stat">
            <span className="scanner-header__stat-value">{dashboard?.total_scans ?? scans.length}</span>
            <span className="scanner-header__stat-label">Scans</span>
          </div>
          <div className="scanner-header__stat">
            <span className="scanner-header__stat-value" style={{ color: getScoreColor(dashboard?.avg_health_score ?? 0) }}>{dashboard?.avg_health_score ?? "-"}</span>
            <span className="scanner-header__stat-label">Avg Score</span>
          </div>
          <div className="scanner-header__stat">
            <span className="scanner-header__stat-value" style={{ color: (dashboard?.alerts.length ?? 0) > 0 ? "#dc2626" : "#16a34a" }}>{dashboard?.alerts.length ?? 0}</span>
            <span className="scanner-header__stat-label">Alerts</span>
          </div>
        </div>
        <button type="button" className="scanner-header__scan-btn" onClick={() => setShowScanForm(!showScanForm)}>
          {showScanForm ? "Cancel" : "+ Scan Repository"}
        </button>
      </div>

      {/* Scan Form */}
      {showScanForm && (
        <div className="scanner-scan-form">
          <div className="scanner-scan-form__fields">
            <input
              className="scanner-scan-form__input"
              placeholder="Repository URL (https://github.com/org/repo.git)"
              value={repoUrl}
              onChange={(e) => setRepoUrl(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter") void handleStartScan(); }}
            />
            <input
              className="scanner-scan-form__input scanner-scan-form__input--branch"
              placeholder="Branch"
              value={branch}
              onChange={(e) => setBranch(e.target.value)}
            />
            <button type="button" className="scanner-scan-form__btn" disabled={isBusy || !repoUrl.trim()} onClick={handleStartScan}>
              {isBusy ? "Scanning..." : "Start Scan"}
            </button>
          </div>
        </div>
      )}

      {/* Alerts Bar */}
      {dashboard && dashboard.alerts.length > 0 && (
        <div className="scanner-alerts-bar">
          {dashboard.alerts.slice(0, 3).map((alert, i) => (
            <div key={i} className={`scanner-alert-item scanner-alert-item--${alert.severity}`}>
              <span className="scanner-alert-item__icon">{alert.severity === "critical" ? "\u26A0" : "\u25B2"}</span>
              <span className="scanner-alert-item__repo">{alert.repository_name}</span>
              <span className="scanner-alert-item__msg">{alert.message}</span>
              <button type="button" className="scanner-alert-item__action" onClick={() => {
                const group = repoGroups.find((g) => g.repoName === alert.repository_name);
                if (group) handleSelectRepo(group.repoUrl);
              }}>View</button>
            </div>
          ))}
        </div>
      )}

      {/* Main Layout: Sidebar + Content */}
      <div className="scanner-body">
        {/* Sidebar */}
        <div className="scanner-sidebar">
          <div className="scanner-sidebar__search">
            <input
              className="scanner-sidebar__search-input"
              placeholder="Search repositories..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            <select className="scanner-sidebar__sort" value={sortBy} onChange={(e) => setSortBy(e.target.value as "score" | "name" | "recent")}>
              <option value="score">Sort: Score</option>
              <option value="name">Sort: Name</option>
              <option value="recent">Sort: Recent</option>
            </select>
          </div>

          <div className="scanner-sidebar__list">
            {filteredGroups.length === 0 ? (
              <div className="scanner-sidebar__empty">
                {searchQuery ? "No matching repositories" : "No scans yet"}
              </div>
            ) : (
              filteredGroups.map((group) => {
                const isSelected = group.repoUrl === selectedRepoUrl;
                const score = group.latest.health.score;
                const sqScore = group.latest.sonarqube && typeof group.latest.sonarqube === "object" && "total_score" in group.latest.sonarqube
                  ? (group.latest.sonarqube as unknown as Record<string, unknown>).total_score as number
                  : null;

                return (
                  <button
                    key={group.repoUrl}
                    type="button"
                    className={`scanner-sidebar__item ${isSelected ? "scanner-sidebar__item--selected" : ""}`}
                    onClick={() => handleSelectRepo(group.repoUrl)}
                  >
                    <div className="scanner-sidebar__item-header">
                      <span className="scanner-sidebar__item-name">{group.repoName}</span>
                      <span className="scanner-sidebar__item-branch">{group.latest.branch}</span>
                    </div>
                    <div className="scanner-sidebar__item-scores">
                      <span className="scanner-sidebar__score-badge" style={{ background: getScoreBg(score), color: getScoreColor(score) }}>{score}</span>
                      {sqScore !== null && sqScore !== undefined && sqScore > 0 && (
                        <span className="scanner-sidebar__score-badge scanner-sidebar__score-badge--sq" style={{ background: getScoreBg(sqScore), color: getScoreColor(sqScore) }}>SQ:{sqScore}</span>
                      )}
                    </div>
                    <div className="scanner-sidebar__item-meta">
                      <span>{group.scans.length} scan{group.scans.length !== 1 ? "s" : ""}</span>
                      <span>{getTimeAgo(group.latest.started_at)}</span>
                    </div>
                  </button>
                );
              })
            )}
          </div>
        </div>

        {/* Content */}
        <div className="scanner-content">
          {!selectedScan ? (
            <div className="scanner-content__empty">
              <h3>Select a repository</h3>
              <p>Choose a repository from the sidebar or start a new scan.</p>
            </div>
          ) : (
            <>
              {/* Content Header */}
              <div className="scanner-content__header">
                <div className="scanner-content__title-row">
                  <h2>{selectedScan.repository_name}</h2>
                  <span className="scanner-content__branch">{selectedScan.branch}</span>
                  <span className={`scanner-content__status scanner-content__status--${selectedScan.status.toLowerCase()}`}>
                    {STATUS_LABELS[selectedScan.status as keyof typeof STATUS_LABELS] ?? selectedScan.status}
                  </span>
                </div>
                <div className="scanner-content__actions">
                  <button type="button" className="scanner-action-btn" disabled={isBusy} onClick={() => void handleRescan(selectedScan.id)}>
                    Re-scan
                  </button>
                  <button type="button" className="scanner-action-btn" disabled={isBusy} onClick={() => void handleGenerate(selectedScan.id)}>
                    Generate Docs
                  </button>
                  {selectedGroup && selectedGroup.scans.length >= 2 && (
                    <select
                      className="scanner-action-select"
                      value={compareTarget ?? ""}
                      onChange={(e) => {
                        setCompareTarget(e.target.value || null);
                        setActiveTab("overview");
                      }}
                    >
                      <option value="">Compare with...</option>
                      {selectedGroup.scans.filter((s) => s.id !== selectedScan.id).map((s) => (
                        <option key={s.id} value={s.id}>
                          {new Date(s.started_at).toLocaleDateString()} (score: {s.health.score})
                        </option>
                      ))}
                    </select>
                  )}
                  <button type="button" className="scanner-action-btn scanner-action-btn--danger" onClick={() => void handleDelete(selectedScan.id)}>
                    Delete
                  </button>
                </div>
              </div>

              {/* Progress bar for in-progress scans */}
              {selectedScan.status !== "COMPLETED" && selectedScan.status !== "FAILED" && (
                <div className="scanner-progress">
                  <div className="scanner-progress__bar">
                    <div className="scanner-progress__fill" style={{ width: `${getProgressPercent(selectedScan.status)}%` }} />
                  </div>
                  <span className="scanner-progress__label">{selectedScan.status}...</span>
                </div>
              )}

              {/* Tabs */}
              <div className="scanner-tabs">
                {([
                  { key: "overview", label: "Overview" },
                  { key: "tech", label: "Tech Stack" },
                  { key: "tests", label: "Tests & Lint" },
                  { key: "security", label: "Security" },
                  { key: "sonarqube", label: "SonarQube" },
                  { key: "documents", label: "Documents", count: generatedDocs.length || undefined },
                  { key: "webhooks", label: "Webhooks" },
                ] as { key: DetailTab; label: string; count?: number }[]).map((tab) => (
                  <button
                    key={tab.key}
                    type="button"
                    className={`scanner-tab ${activeTab === tab.key ? "scanner-tab--active" : ""}`}
                    onClick={() => setActiveTab(tab.key)}
                  >
                    {tab.label}
                    {tab.count !== undefined && <span className="scanner-tab__count">{tab.count}</span>}
                  </button>
                ))}
              </div>

              {/* Tab Content */}
              <div className="scanner-tab-content">
                {/* Compare View */}
                {compareTarget && activeTab === "overview" && selectedGroup && (
                  <ScanComparisonView
                    scan={selectedScan}
                    previousScans={selectedGroup.scans.filter((s) => s.id !== selectedScan.id)}
                    onClose={() => { setCompareTarget(null); }}
                  />
                )}

                {/* Overview Tab */}
                {activeTab === "overview" && !compareTarget && (
                  <div className="scanner-overview">
                    {/* Health Score */}
                    <div className="scanner-overview__score-section">
                      <div className="scanner-overview__score-ring" style={{ borderColor: getScoreColor(selectedScan.health.score) }}>
                        <span className="scanner-overview__score-value" style={{ color: getScoreColor(selectedScan.health.score) }}>
                          {selectedScan.health.score}
                        </span>
                        <span className="scanner-overview__score-label">Health</span>
                      </div>
                      {selectedScan.sonarqube && selectedScan.sonarqube && typeof selectedScan.sonarqube === "object" && "total_score" in (selectedScan.sonarqube as unknown as unknown as Record<string, unknown>) && (selectedScan.sonarqube as unknown as Record<string, unknown>).total_score as number > 0 && (
                        <div className="scanner-overview__score-ring" style={{ borderColor: getScoreColor((selectedScan.sonarqube as unknown as Record<string, unknown>).total_score as number) }}>
                          <span className="scanner-overview__score-value" style={{ color: getScoreColor((selectedScan.sonarqube as unknown as Record<string, unknown>).total_score as number) }}>
                            {(selectedScan.sonarqube as unknown as Record<string, unknown>).total_score as number}
                          </span>
                          <span className="scanner-overview__score-label">SonarQube</span>
                        </div>
                      )}
                    </div>

                    {/* Metrics Grid */}
                    <div className="scanner-overview__metrics">
                      <div className="scanner-metric">
                        <span className="scanner-metric__value">{selectedScan.file_analysis.total_files}</span>
                        <span className="scanner-metric__label">Files</span>
                      </div>
                      <div className="scanner-metric">
                        <span className="scanner-metric__value">{formatNumber(selectedScan.file_analysis.total_lines)}</span>
                        <span className="scanner-metric__label">Lines</span>
                      </div>
                      <div className="scanner-metric">
                        <span className="scanner-metric__value">{selectedScan.test_suites.reduce((sum, t) => sum + t.total, 0)}</span>
                        <span className="scanner-metric__label">Tests</span>
                      </div>
                      <div className="scanner-metric">
                        <span className="scanner-metric__value">{selectedScan.lint_results.reduce((sum, r) => sum + r.total_issues, 0)}</span>
                        <span className="scanner-metric__label">Lint Issues</span>
                      </div>
                      <div className="scanner-metric">
                        <span className="scanner-metric__value">{selectedScan.security_scan.total_vulnerabilities}</span>
                        <span className="scanner-metric__label">Vulnerabilities</span>
                      </div>
                      <div className="scanner-metric">
                        <span className="scanner-metric__value">{selectedScan.tech_stack.frameworks.length}</span>
                        <span className="scanner-metric__label">Frameworks</span>
                      </div>
                    </div>

                    {/* Health Issues */}
                    {selectedScan.health.issues.length > 0 && (
                      <div className="scanner-overview__issues">
                        <h3>Issues</h3>
                        <div className="scanner-issues-list">
                          {selectedScan.health.issues.map((issue, i) => (
                            <div key={i} className="scanner-issue scanner-issue--warning">
                              <span className="scanner-issue__message">{issue}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Scan History */}
                    {selectedGroup && selectedGroup.scans.length > 1 && (
                      <div className="scanner-overview__history">
                        <h3>Scan History</h3>
                        <div className="scanner-history-list">
                          {selectedGroup.scans.map((scan) => (
                            <button
                              key={scan.id}
                              type="button"
                              className={`scanner-history-item ${scan.id === selectedScan.id ? "scanner-history-item--current" : ""}`}
                              onClick={() => handleSelectScan(scan)}
                            >
                              <span className="scanner-history-item__score" style={{ color: getScoreColor(scan.health.score) }}>{scan.health.score}</span>
                              <span className="scanner-history-item__date">{new Date(scan.started_at).toLocaleString()}</span>
                              <span className={`scanner-history-item__status scanner-history-item__status--${scan.status.toLowerCase()}`}>{scan.status}</span>
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Tech Stack Tab */}
                {activeTab === "tech" && (
                  <div className="scanner-tech">
                    <div className="scanner-tech__section">
                      <h3>Languages</h3>
                      <div className="scanner-tech__tags">
                        {Object.entries(selectedScan.file_analysis.languages).map(([lang, count]: [string, number]) => (
                          <span key={lang} className="scanner-tech__tag">{lang} ({count})</span>
                        ))}
                      </div>
                    </div>
                    <div className="scanner-tech__section">
                      <h3>Frameworks</h3>
                      <div className="scanner-tech__tags">
                        {selectedScan.tech_stack.frameworks.length > 0
                          ? selectedScan.tech_stack.frameworks.map((f) => <span key={f} className="scanner-tech__tag scanner-tech__tag--fw">{f}</span>)
                          : <span className="scanner-tech__empty">No frameworks detected</span>}
                      </div>
                    </div>
                    <div className="scanner-tech__section">
                      <h3>Databases</h3>
                      <div className="scanner-tech__tags">
                        {selectedScan.tech_stack.databases.length > 0
                          ? selectedScan.tech_stack.databases.map((d) => <span key={d} className="scanner-tech__tag scanner-tech__tag--db">{d}</span>)
                          : <span className="scanner-tech__empty">No databases detected</span>}
                      </div>
                    </div>
                    <div className="scanner-tech__section">
                      <h3>Tools</h3>
                      <div className="scanner-tech__tags">
                        {selectedScan.tech_stack.tools.length > 0
                          ? selectedScan.tech_stack.tools.map((t) => <span key={t} className="scanner-tech__tag">{t}</span>)
                          : <span className="scanner-tech__empty">No tools detected</span>}
                      </div>
                    </div>
                                       <div className="scanner-tech__section">
                      <h3>Capabilities</h3>
                      <div className="scanner-tech__tags">
                        {selectedScan.tech_stack.has_docker && <span className="scanner-tech__tag scanner-tech__tag--cap">Docker</span>}
                        {selectedScan.tech_stack.has_ci_cd && <span className="scanner-tech__tag scanner-tech__tag--cap">CI/CD</span>}
                        {selectedScan.tech_stack.has_tests && <span className="scanner-tech__tag scanner-tech__tag--cap">Tests</span>}
                        {selectedScan.tech_stack.has_linting && <span className="scanner-tech__tag scanner-tech__tag--cap">Linting</span>}
                        {selectedScan.tech_stack.has_type_checking && <span className="scanner-tech__tag scanner-tech__tag--cap">Type Checking</span>}
                        {selectedScan.tech_stack.package_manager && <span className="scanner-tech__tag scanner-tech__tag--cap">{selectedScan.tech_stack.package_manager}</span>}
                      </div>
                    </div>
                  </div>
                )}

                {/* Tests & Lint Tab */}
                {activeTab === "tests" && (
                  <div className="scanner-tests">
                    <div className="scanner-tests__section">
                      <h3>Test Suites</h3>
                      {selectedScan.test_suites.length === 0 ? (
                        <p className="scanner-tests__empty">No test suites found</p>
                      ) : (
                        <div className="scanner-tests__list">
                          {selectedScan.test_suites.map((suite, i) => (
                            <div key={i} className="scanner-test-suite">
                              <div className="scanner-test-suite__header">
                                <span className="scanner-test-suite__name">{suite.name}</span>
                                <span className="scanner-test-suite__framework">{suite.framework}</span>
                              </div>
                              <div className="scanner-test-suite__bar">
                                <div className="scanner-test-suite__passed" style={{ width: suite.total > 0 ? `${(suite.passed / suite.total) * 100}%` : "0%" }} />
                                <div className="scanner-test-suite__failed" style={{ width: suite.total > 0 ? `${(suite.failed / suite.total) * 100}%` : "0%" }} />
                                <div className="scanner-test-suite__skipped" style={{ width: suite.total > 0 ? `${(suite.skipped / suite.total) * 100}%` : "0%" }} />
                              </div>
                              <div className="scanner-test-suite__stats">
                                <span className="scanner-test-suite__stat scanner-test-suite__stat--passed">{suite.passed} passed</span>
                                <span className="scanner-test-suite__stat scanner-test-suite__stat--failed">{suite.failed} failed</span>
                                <span className="scanner-test-suite__stat scanner-test-suite__stat--skipped">{suite.skipped} skipped</span>
                                <span className="scanner-test-suite__stat">{suite.total} total</span>
                                
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                    <div className="scanner-tests__section">
                      <h3>Lint Results</h3>
                      {selectedScan.lint_results.length === 0 ? (
                        <p className="scanner-tests__empty">No lint results</p>
                      ) : (
                        <div className="scanner-tests__list">
                          {selectedScan.lint_results.map((result, i) => (
                            <div key={i} className="scanner-lint-result">
                              <div className="scanner-lint-result__header">
                                <span className="scanner-lint-result__tool">{result.tool}</span>
                                <span className="scanner-lint-result__total">{result.total_issues} issues</span>
                              </div>
                              <div className="scanner-lint-result__breakdown">
                                {result.errors > 0 && <span className="scanner-lint-result__stat scanner-lint-result__stat--error">{result.errors} errors</span>}
                                {result.warnings > 0 && <span className="scanner-lint-result__stat scanner-lint-result__stat--warning">{result.warnings} warnings</span>}
                                
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Security Tab */}
                {activeTab === "security" && (
                  <div className="scanner-security">
                    <div className="scanner-security__summary">
                      <div className="scanner-security__stat">
                        <span className="scanner-security__stat-value" style={{ color: "#dc2626" }}>{selectedScan.security_scan.critical}</span>
                        <span className="scanner-security__stat-label">Critical</span>
                      </div>
                      <div className="scanner-security__stat">
                        <span className="scanner-security__stat-value" style={{ color: "#f59e0b" }}>{selectedScan.security_scan.high}</span>
                        <span className="scanner-security__stat-label">High</span>
                      </div>
                      <div className="scanner-security__stat">
                        <span className="scanner-security__stat-value" style={{ color: "#3b82f6" }}>{selectedScan.security_scan.medium}</span>
                        <span className="scanner-security__stat-label">Medium</span>
                      </div>
                      <div className="scanner-security__stat">
                        <span className="scanner-security__stat-value" style={{ color: "#6b7280" }}>{selectedScan.security_scan.low}</span>
                        <span className="scanner-security__stat-label">Low</span>
                      </div>
                    </div>
                    {selectedScan.security_scan.issues.length > 0 && (
                      <div className="scanner-security__list">
                        <h3>Vulnerabilities</h3>
                        {selectedScan.security_scan.issues.slice(0, 50).map((vuln: {package: string; severity: string; description: string; fix_version: string}, i: number) => (
                          <div key={i} className={`scanner-vuln scanner-vuln--${vuln.severity}`}>
                            <span className="scanner-vuln__severity">{vuln.severity}</span>
                            <div className="scanner-vuln__details">
                              <span className="scanner-vuln__name">{vuln.package}</span>
                              {vuln.fix_version && <span className="scanner-vuln__version">fix: {vuln.fix_version}</span>}
                              {vuln.description && <span className="scanner-vuln__desc">{vuln.description}</span>}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* SonarQube Tab */}
                {activeTab === "sonarqube" && (
                  <div className="scanner-sonarqube">
                    {selectedScan.sonarqube && (selectedScan.sonarqube as SonarQubeResult).project_key ? (
                      <SonarQubeComparison
                        internalScore={selectedScan.health.score}
                        sonarqube={selectedScan.sonarqube as SonarQubeResult}
                      />
                    ) : (
                      <div className="scanner-sonarqube__empty">
                        <h3>No SonarQube Data</h3>
                        <p>SonarQube analysis was not configured for this scan. Set SONARQUBE_URL, SONARQUBE_TOKEN, and SONARQUBE_PROJECT_KEY environment variables to enable SonarQube integration.</p>
                      </div>
                    )}
                  </div>
                )}

                {/* Documents Tab */}
                {activeTab === "documents" && (
                  <div className="scanner-documents">
                    {/* Suggestions Section */}
                    {selectedScan.suggestions.length > 0 && (
                      <div className="scanner-documents__suggestions">
                        <div className="scanner-documents__suggestions-header">
                          <h3>Recommended Documents</h3>
                          <div className="scanner-documents__suggestions-actions">
                            <button
                              type="button"
                              className="scanner-documents__icon-btn"
                              title="Select All"
                              onClick={() => {
                                const allKeys = new Set(selectedScan.suggestions.map((s) => s.template_key));
                                setSelectedSuggestions(allKeys);
                              }}
                            >
                              <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2"><rect x="1" y="1" width="14" height="14" rx="2" fill="#111827" stroke="#111827"/><polyline points="3.5,8 6.5,11 12.5,5" stroke="white" fill="none"/></svg>
                            </button>
                            <button
                              type="button"
                              className="scanner-documents__icon-btn"
                              title="Deselect All"
                              onClick={() => setSelectedSuggestions(new Set())}
                            >
                              <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="#9ca3af" strokeWidth="1.5"><rect x="1" y="1" width="14" height="14" rx="2"/></svg>
                            </button>
                            <button
                              type="button"
                              className="scanner-documents__generate-btn"
                              disabled={selectedSuggestions.size === 0 || isBusy}
                              onClick={async () => {
                                setIsBusy(true);
                                try {
                                  await generateDocuments(selectedScan.id, Array.from(selectedSuggestions));
                                  const docs = await listGeneratedDocuments(selectedScan.id);
                                  setGeneratedDocs(docs);
                                  setSelectedSuggestions(new Set());
                                } catch (err) {
                                  console.error(err);
                                } finally {
                                  setIsBusy(false);
                                }
                              }}
                            >
                              {isBusy ? "Generating..." : selectedSuggestions.size === 0 ? "Select documents to generate" : `Generate ${selectedSuggestions.size} Document${selectedSuggestions.size !== 1 ? "s" : ""}`}
                            </button>
                          </div>
                        </div>
                        <div className="scanner-documents__suggestions-list">
                          {selectedScan.suggestions.map((sug) => {
                            const isChecked = selectedSuggestions.has(sug.template_key);
                            const isGenerated = generatedDocs.some((d) => d.template_key === sug.template_key);
                            return (
                              <label
                                key={sug.template_key}
                                className={`scanner-suggestion ${isChecked ? "scanner-suggestion--selected" : ""} ${isGenerated ? "scanner-suggestion--generated" : ""}`}
                              >
                                <input
                                  type="checkbox"
                                  checked={isChecked}
                                  disabled={isGenerated}
                                  onChange={(e) => {
                                    const next = new Set(selectedSuggestions);
                                    if (e.target.checked) {
                                      next.add(sug.template_key);
                                    } else {
                                      next.delete(sug.template_key);
                                    }
                                    setSelectedSuggestions(next);
                                  }}
                                />
                                <span className="scanner-suggestion__name">{sug.name}</span>
                                <span className="scanner-suggestion__type">{sug.document_type}</span>
                                <span className={`scanner-suggestion__priority scanner-suggestion__priority--${sug.priority}`}>
                                  {PRIORITY_LABELS[sug.priority as keyof typeof PRIORITY_LABELS] ?? sug.priority}
                                </span>
                                {isGenerated && <span className="scanner-suggestion__done">Generated</span>}
                              </label>
                            );
                          })}
                        </div>
                      </div>
                    )}

                    {/* Generated Documents Section */}
                    {generatedDocs.length > 0 && (
                      <div className="scanner-documents__generated">
                        <h3>Generated Documents ({generatedDocs.length})</h3>
                        <div className="scanner-documents__list">
                          {generatedDocs.map((doc) => {
                            const isExpanded = expandedDocs.has(doc.template_key);
                            return (
                              <div key={doc.template_key} className={`scanner-document ${isExpanded ? "scanner-document--expanded" : ""}`}>
                                <button
                                  type="button"
                                  className="scanner-document__header"
                                  onClick={() => {
                                    const next = new Set(expandedDocs);
                                    if (isExpanded) {
                                      next.delete(doc.template_key);
                                    } else {
                                      next.add(doc.template_key);
                                    }
                                    setExpandedDocs(next);
                                  }}
                                >
                                  <span className="scanner-document__chevron">{isExpanded ? "▼" : "▶"}</span>
                                  <span className="scanner-document__title">{doc.name}</span>
                                  <span className="scanner-document__type">{doc.template_key}</span>
                                </button>
                                {isExpanded && (
                                  <div className="scanner-document__preview">
                                    <MarkdownPreview content={doc.content} />
                                  </div>
                                )}
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    )}

                    {selectedScan.suggestions.length === 0 && generatedDocs.length === 0 && (
                      <div className="scanner-documents__empty">
                        <h3>No Document Suggestions</h3>
                        <p>This scan did not produce any document suggestions. Try re-scanning the repository.</p>
                      </div>
                    )}
                  </div>
                )}

                {/* Webhooks Tab */}
                {activeTab === "webhooks" && (
                  <WebhookEventsPanel />
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
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

function formatNumber(n: number): string {
  if (n >= 1000000) return (n / 1000000).toFixed(1) + "M";
  if (n >= 1000) return (n / 1000).toFixed(1) + "K";
  return String(n);
}

function getProgressPercent(status: string): number {
  const steps: Record<string, number> = { PENDING: 5, CLONING: 20, ANALYZING: 40, TESTING: 65, GENERATING: 85 };
  return steps[status] ?? 0;
}
