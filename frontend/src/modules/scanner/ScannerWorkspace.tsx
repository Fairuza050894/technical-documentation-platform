import { useCallback, useEffect, useRef, useState } from "react";

import { deleteScan, generateDocuments, getScan, listGeneratedDocuments, listScans, rescanScan, startScan } from "./api";
import type { GeneratedDocument } from "./api";
import { MarkdownPreview } from "./MarkdownPreview";
import { ScanComparisonView } from "./ScanComparisonView";
import { SonarQubeComparison } from "./SonarQubeComparison";
import type { HealthLevel, ScanResult } from "./types";
import { HEALTH_COLORS, PRIORITY_LABELS, STATUS_LABELS, STATUS_STEPS } from "./types";

interface ScannerWorkspaceProps {
  embedded?: boolean;
}

type DetailTab = "overview" | "tech" | "tests" | "security" | "documents" | "sonarqube";

interface RepoGroup {
  repoName: string;
  repoUrl: string;
  scans: ScanResult[];
  latest: ScanResult;
}

export function ScannerWorkspace({ embedded = false }: ScannerWorkspaceProps) {
  const [scans, setScans] = useState<ScanResult[]>([]);
  const [selectedScan, setSelectedScan] = useState<ScanResult | null>(null);
  const [repoUrl, setRepoUrl] = useState("");
  const [branch, setBranch] = useState("main");
  const [isBusy, setIsBusy] = useState(false);
  const [toast, setToast] = useState<{ message: string; isError: boolean } | null>(null);
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);
  const [generatedDocs, setGeneratedDocs] = useState<GeneratedDocument[]>([]);
  const [generatingKeys, setGeneratingKeys] = useState<Set<string>>(new Set());
  const [selectedDoc, setSelectedDoc] = useState<GeneratedDocument | null>(null);
  const [selectedSuggestionKeys, setSelectedSuggestionKeys] = useState<Set<string>>(new Set());
  const [activeTab, setActiveTab] = useState<DetailTab>("overview");
  const [showComparison, setShowComparison] = useState(false);
  const [rescanningId, setRescanningId] = useState<string | null>(null);
  const [expandedRepos, setExpandedRepos] = useState<Set<string>>(new Set());
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Group scans by repository
  const repoGroups: RepoGroup[] = [];
  const groupMap = new Map<string, ScanResult[]>();
  for (const scan of scans) {
    const key = scan.repository_url;
    const existing = groupMap.get(key);
    if (existing) {
      existing.push(scan);
    } else {
      groupMap.set(key, [scan]);
    }
  }
  for (const [url, groupScans] of groupMap) {
    const sorted = groupScans.sort((a, b) => new Date(b.started_at).getTime() - new Date(a.started_at).getTime());
    const first = sorted[0];
    if (!first) continue;
    repoGroups.push({
      repoName: first.repository_name,
      repoUrl: url,
      scans: sorted,
      latest: first,
    });
  }

  const load = useCallback(async (signal?: AbortSignal) => {
    try {
      const collection = await listScans(signal);
      setScans(collection.items);
    } catch (error: unknown) {
      if (error instanceof DOMException && error.name === "AbortError") return;
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    void load(controller.signal);
    return () => controller.abort();
  }, [load]);

  useEffect(() => {
    const activeScans = scans.filter((s) => !["COMPLETED", "FAILED"].includes(s.status));
    if (activeScans.length > 0) {
      pollingRef.current = setInterval(async () => {
        try {
          for (const scan of activeScans) {
            const updated = await getScan(scan.id);
            setScans((prev) => prev.map((s) => (s.id === updated.id ? updated : s)));
            if (selectedScan?.id === updated.id) {
              setSelectedScan(updated);
            }
          }
        } catch {
          // ignore
        }
      }, 3000);
    }
    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
    };
  }, [scans, selectedScan]);

  function showToast(msg: string, isError = false): void {
    setToast({ message: msg, isError });
    setTimeout(() => setToast(null), 3000);
  }

  async function handleStartScan(): Promise<void> {
    if (!repoUrl.trim() || isBusy) return;
    setIsBusy(true);
    try {
      const scan = await startScan(repoUrl.trim(), branch.trim());
      setScans((prev) => [scan, ...prev]);
      setSelectedScan(scan);
      setActiveTab("overview");
      setRepoUrl("");
      showToast("Scan started...");
    } catch (error: unknown) {
      showToast(error instanceof Error ? error.message : "Scan failed.", true);
    } finally {
      setIsBusy(false);
    }
  }

  function handleSelectScan(scan: ScanResult): void {
    setSelectedScan(scan);
    setSelectedDoc(null);
    setActiveTab("overview");
    setShowComparison(false);
    void loadGeneratedDocs(scan.id);
  }

  async function loadGeneratedDocs(scanId: string): Promise<void> {
    try {
      const docs = await listGeneratedDocuments(scanId);
      setGeneratedDocs(docs);
    } catch {
      setGeneratedDocs([]);
    }
  }

  async function handleRescan(scanId: string): Promise<void> {
    setRescanningId(scanId);
    try {
      const newScan = await rescanScan(scanId);
      setScans((prev) => [newScan, ...prev]);
      setSelectedScan(newScan);
      setActiveTab("overview");
      setShowComparison(false);
      showToast("Re-scan started...");
    } catch (error: unknown) {
      showToast(error instanceof Error ? error.message : "Re-scan failed.", true);
    } finally {
      setRescanningId(null);
    }
  }

  async function handleGenerate(scanId: string, keys: string[]): Promise<void> {
    if (keys.length === 0) return;
    const keySet = new Set(keys);
    setGeneratingKeys(keySet);
    try {
      const docs = await generateDocuments(scanId, keys);
      setGeneratedDocs((prev) => [...docs, ...prev]);
      setSelectedSuggestionKeys(new Set());
      showToast(docs.length + " document(s) generated");
    } catch (error: unknown) {
      showToast(error instanceof Error ? error.message : "Generation failed.", true);
    } finally {
      setGeneratingKeys(new Set());
    }
  }

  function toggleSuggestionKey(key: string): void {
    setSelectedSuggestionKeys((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  }

  async function executeDelete(scanId: string): Promise<void> {
    setConfirmDeleteId(null);
    try {
      await deleteScan(scanId);
      setScans((prev) => prev.filter((s) => s.id !== scanId));
      if (selectedScan?.id === scanId) {
        setSelectedScan(null);
        setGeneratedDocs([]);
        setSelectedDoc(null);
      }
      showToast("Scan deleted");
    } catch (error: unknown) {
      showToast(error instanceof Error ? error.message : "Delete failed.", true);
    }
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

  function toggleRepoExpand(url: string): void {
    setExpandedRepos((prev) => {
      const next = new Set(prev);
      if (next.has(url)) next.delete(url);
      else next.add(url);
      return next;
    });
  }

  const isCompleted = selectedScan?.status === "COMPLETED";
  const isFailed = selectedScan?.status === "FAILED";
  const isActive = selectedScan && !isCompleted && !isFailed;

  const tabs: { key: DetailTab; label: string; count?: number }[] = [];
  if (isCompleted) {
    tabs.push({ key: "overview", label: "Overview" });
    tabs.push({ key: "tech", label: "Tech Stack" });
    if (selectedScan.test_suites.length > 0) tabs.push({ key: "tests", label: "Tests" });
    if (selectedScan.security_scan.total_vulnerabilities > 0) tabs.push({ key: "security", label: "Security", count: selectedScan.security_scan.total_vulnerabilities });
    tabs.push({ key: "documents", label: "Documents", count: generatedDocs.length || undefined });
    if (selectedScan.sonarqube && !selectedScan.sonarqube.error) tabs.push({ key: "sonarqube", label: "SonarQube" });
  }

  const previousScans = selectedScan
    ? scans.filter((s) => s.id !== selectedScan.id && s.status === "COMPLETED" && s.repository_url === selectedScan.repository_url)
    : [];

  return (
    <div className="scanner-workspace workspace-canvas">
      {!embedded && (
        <header className="topbar">
          <div>
            <p className="eyebrow">Repository analysis</p>
            <h1>Repository Scanner</h1>
          </div>
          <span className="environment-badge">{repoGroups.length} repo{repoGroups.length !== 1 ? "s" : ""}</span>
        </header>
      )}

      <div className="scanner-layout">
        {/* Left Panel */}
        <div className="scanner-left">
          <div className="scanner-form">
            <h3>Scan a repository</h3>
            <p className="scanner-form__desc">Clone, analyze tech stack, run tests, and get document suggestions.</p>
            <div className="scanner-form__fields">
              <div className="field">
                <label htmlFor="repo-url">Repository URL</label>
                <input id="repo-url" type="url" value={repoUrl} onChange={(e) => setRepoUrl(e.target.value)} placeholder="https://github.com/org/repo.git" onKeyDown={(e) => { if (e.key === "Enter") void handleStartScan(); }} />
              </div>
              <div className="field">
                <label htmlFor="repo-branch">Branch</label>
                <input id="repo-branch" type="text" value={branch} onChange={(e) => setBranch(e.target.value)} placeholder="main" onKeyDown={(e) => { if (e.key === "Enter") void handleStartScan(); }} />
              </div>
            </div>
            <button type="button" className="scanner-form__btn" disabled={isBusy || !repoUrl.trim()} onClick={() => void handleStartScan()}>
              {isBusy ? "Starting..." : "Start scan"}
            </button>
          </div>

          {repoGroups.length > 0 && (
            <div className="scanner-history">
              <div className="scanner-history__header">
                <h3>Repositories</h3>
                <span className="scanner-history__count">{repoGroups.length}</span>
              </div>
              <div className="scanner-history__list">
                {repoGroups.map((group) => {
                  const isExpanded = expandedRepos.has(group.repoUrl);
                  const hasMultiple = group.scans.length > 1;
                  const latest = group.latest;
                  const prevScan = group.scans.length > 1 ? group.scans[1] : null;
                  const scoreDelta = prevScan ? latest.health.score - prevScan.health.score : 0;

                  return (
                    <div key={group.repoUrl} className="scanner-repo-group">
                      <div
                        className={"scanner-repo-item" + (selectedScan?.id === latest.id ? " scanner-repo-item--selected" : "")}
                        onClick={() => handleSelectScan(latest)}
                        role="button"
                        tabIndex={0}
                        onKeyDown={(e) => { if (e.key === "Enter") handleSelectScan(latest); }}
                      >
                        <div className="scanner-repo-item__left">
                          <span className={"scanner-status-dot scanner-status-dot--" + latest.status.toLowerCase()} />
                          <div className="scanner-repo-item__info">
                            <span className="scanner-repo-item__name">{group.repoName}</span>
                            <div className="scanner-repo-item__meta">
                              <span className="scanner-repo-item__branch">{latest.branch}</span>
                              <span className="scanner-repo-item__time">{getTimeAgo(latest.started_at)}</span>
                              {hasMultiple && <span className="scanner-repo-item__count">{group.scans.length} scans</span>}
                            </div>
                          </div>
                        </div>
                        <div className="scanner-repo-item__right">
                          {latest.status === "COMPLETED" && (
                            <div className="scanner-repo-item__score-wrap">
                              <span className="scanner-repo-item__score" style={{ color: getScoreColor(latest.health.score), borderColor: getScoreBg(latest.health.score), background: getScoreBg(latest.health.score) }}>
                                {latest.health.score}
                              </span>
                              {prevScan && scoreDelta !== 0 && (
                                <span className="scanner-repo-item__delta" style={{ color: getScoreColor(latest.health.score) }}>
                                  {scoreDelta > 0 ? "+" : ""}{scoreDelta}
                                </span>
                              )}
                            </div>
                          )}
                          {latest.status === "FAILED" && (
                            <span className="scanner-history-item__status-label scanner-history-item__status-label--failed">Failed</span>
                          )}
                          {!["COMPLETED", "FAILED"].includes(latest.status) && (
                            <span className="scanner-history-item__status-label scanner-history-item__status-label--pending">{STATUS_LABELS[latest.status]}</span>
                          )}
                        </div>
                      </div>

                      {/* Actions row */}
                      <div className="scanner-repo-actions">
                        {latest.status === "COMPLETED" && (
                          <button type="button" className="scanner-repo-action" onClick={(e) => { e.stopPropagation(); void handleRescan(latest.id); }} disabled={rescanningId === latest.id} title="Re-scan now">
                            {rescanningId === latest.id ? "Scanning..." : "\u21BB Re-scan"}
                          </button>
                        )}
                        {hasMultiple && (
                          <button type="button" className="scanner-repo-action scanner-repo-action--expand" onClick={(e) => { e.stopPropagation(); toggleRepoExpand(group.repoUrl); }}>
                            {isExpanded ? "\u25B2 Hide history" : "\u25BC History (" + group.scans.length + ")"}
                          </button>
                        )}
                        {["COMPLETED", "FAILED"].includes(latest.status) && (
                          <button type="button" className="scanner-repo-action scanner-repo-action--delete" onClick={(e) => { e.stopPropagation(); setConfirmDeleteId(latest.id); }}>
                            Delete
                          </button>
                        )}
                      </div>

                      {/* Expanded history */}
                      {isExpanded && hasMultiple && (
                        <div className="scanner-repo-history">
                          {group.scans.slice(1).map((scan) => (
                            <div
                              key={scan.id}
                              className={"scanner-repo-history-item" + (selectedScan?.id === scan.id ? " scanner-repo-history-item--selected" : "")}
                              onClick={() => handleSelectScan(scan)}
                              role="button"
                              tabIndex={0}
                              onKeyDown={(e) => { if (e.key === "Enter") handleSelectScan(scan); }}
                            >
                              <span className={"scanner-status-dot scanner-status-dot--" + scan.status.toLowerCase()} />
                              <span className="scanner-repo-history-item__time">{getTimeAgo(scan.started_at)}</span>
                              {scan.status === "COMPLETED" && (
                                <span className="scanner-repo-history-item__score" style={{ color: getScoreColor(scan.health.score) }}>{scan.health.score}</span>
                              )}
                              {scan.status === "FAILED" && <span style={{ color: "#dc2626", fontSize: 10 }}>Failed</span>}
                              <button type="button" className="scanner-repo-history-item__delete" onClick={(e) => { e.stopPropagation(); setConfirmDeleteId(scan.id); }}>Delete</button>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        {/* Right Panel */}
        <div className="scanner-right">
          {selectedScan === null ? (
            <div className="scanner-empty">
              <span className="scanner-empty__icon">{"\u{1F50D}"}</span>
              <h3>No scan selected</h3>
              <p>Start a new scan or select one from history.</p>
            </div>
          ) : (
            <div className="scanner-detail">
              {/* Progress */}
              {isActive && (
                <div className="scanner-progress">
                  <div className="scanner-progress__header">
                    <strong>{selectedScan.repository_name}</strong>
                    <span className="scanner-progress__status">{STATUS_LABELS[selectedScan.status]}</span>
                  </div>
                  <div className="scanner-progress__bar">
                    <div className="scanner-progress__fill" style={{ width: ((STATUS_STEPS.indexOf(selectedScan.status) + 1) / STATUS_STEPS.length * 100) + "%" }} />
                  </div>
                  <div className="scanner-progress__steps">
                    {STATUS_STEPS.map((step, i) => (
                      <span key={step} className={"scanner-progress__step" + (STATUS_STEPS.indexOf(selectedScan.status) >= i ? " scanner-progress__step--done" : "")}>{STATUS_LABELS[step]}</span>
                    ))}
                  </div>
                </div>
              )}

              {/* Error */}
              {isFailed && (
                <div className="scanner-error">
                  <h3>Scan Failed</h3>
                  <p>{selectedScan.error_message || "An unknown error occurred."}</p>
                </div>
              )}

              {/* Completed content */}
              {isCompleted && (
                <>
                  {/* Comparison View */}
                  {showComparison && previousScans.length > 0 && (
                    <ScanComparisonView
                      scan={selectedScan}
                      previousScans={previousScans}
                      onClose={() => setShowComparison(false)}
                    />
                  )}

                  {/* Health + Compare trigger */}
                  {!showComparison && (
                    <>
                      {previousScans.length > 0 && (
                        <button type="button" className="scanner-compare-trigger" onClick={() => setShowComparison(true)}>
                          {"\u2194"} Compare with previous scan
                        </button>
                      )}

                      {/* Health Score Bar */}
                      <div className="scanner-health-bar-compact">
                        <div className="scanner-health-bar-compact__score" style={{ color: getScoreColor(selectedScan.health.score), background: getScoreBg(selectedScan.health.score) }}>
                          {selectedScan.health.score}
                        </div>
                        <div className="scanner-health-bar-compact__metrics">
                          <CompactMetric label="Tests" level={selectedScan.health.test_coverage} />
                          <CompactMetric label="Quality" level={selectedScan.health.code_quality} />
                          <CompactMetric label="Security" level={selectedScan.health.security} />
                          <CompactMetric label="Docs" level={selectedScan.health.documentation} />
                        </div>
                      </div>

                      {/* Tab Bar */}
                      <div className="scanner-tabs">
                        {tabs.map((tab) => (
                          <button
                            key={tab.key}
                            type="button"
                            className={"scanner-tab" + (activeTab === tab.key ? " scanner-tab--active" : "")}
                            onClick={() => { setActiveTab(tab.key); setSelectedDoc(null); }}
                          >
                            {tab.label}
                            {tab.count !== undefined && <span className="scanner-tab__count">{tab.count}</span>}
                          </button>
                        ))}
                      </div>

                      {/* Tab Content */}
                      <div className="scanner-tab-content">
                        {activeTab === "overview" && <OverviewTab scan={selectedScan} />}
                        {activeTab === "tech" && <TechTab scan={selectedScan} />}
                        {activeTab === "tests" && <TestsTab scan={selectedScan} />}
                        {activeTab === "security" && <SecurityTab scan={selectedScan} />}
                        {activeTab === "sonarqube" && selectedScan.sonarqube && (
                          <SonarQubeComparison internalScore={selectedScan.health.score} sonarqube={selectedScan.sonarqube} />
                        )}
                        {activeTab === "documents" && (
                          <DocumentsTab
                            scan={selectedScan}
                            generatedDocs={generatedDocs}
                            selectedDoc={selectedDoc}
                            setSelectedDoc={setSelectedDoc}
                            selectedSuggestionKeys={selectedSuggestionKeys}
                            toggleSuggestionKey={toggleSuggestionKey}
                            generatingKeys={generatingKeys}
                            onGenerate={(keys) => void handleGenerate(selectedScan.id, keys)}
                          />
                        )}
                      </div>
                    </>
                  )}
                </>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Confirm dialog */}
      {confirmDeleteId && (
        <div className="confirm-dialog-overlay" onClick={() => setConfirmDeleteId(null)}>
          <div className="confirm-dialog" onClick={(e) => e.stopPropagation()}>
            <p className="confirm-dialog__message">Delete this scan result?</p>
            <div className="confirm-dialog__actions">
              <button type="button" className="button button--quiet" onClick={() => setConfirmDeleteId(null)}>Cancel</button>
              <button type="button" className="button button--danger" onClick={() => void executeDelete(confirmDeleteId)}>Delete</button>
            </div>
          </div>
        </div>
      )}

      {/* Toast */}
      {toast && (
        <div className={"toast-message " + (toast.isError ? "toast-message--error" : "toast-message--success")} role="alert">{toast.message}</div>
      )}
    </div>
  );
}

/* ── Compact Health Bar ── */

function CompactMetric({ label, level }: { label: string; level: string }) {
  const color = HEALTH_COLORS[level as HealthLevel] || "#9ca3af";
  return (
    <span className="scanner-compact-metric">
      <span className="scanner-compact-metric__dot" style={{ background: color }} />
      <span className="scanner-compact-metric__label">{label}</span>
      <span className="scanner-compact-metric__level" style={{ color }}>{level}</span>
    </span>
  );
}

/* ── Overview Tab ── */

function OverviewTab({ scan }: { scan: ScanResult }) {
  return (
    <div className="scanner-tab-panel">
      <div className="scanner-health-detail">
        <svg viewBox="0 0 120 120" className="scanner-health-ring">
          <circle cx="60" cy="60" r="52" fill="none" stroke="#f3f4f6" strokeWidth="8" />
          <circle
            cx="60" cy="60" r="52" fill="none"
            stroke={scan.health.score >= 70 ? "#16a34a" : scan.health.score >= 40 ? "#f59e0b" : "#dc2626"}
            strokeWidth="8"
            strokeDasharray={2 * Math.PI * 52}
            strokeDashoffset={2 * Math.PI * 52 * (1 - scan.health.score / 100)}
            strokeLinecap="round"
            transform="rotate(-90 60 60)"
          />
          <text x="60" y="55" textAnchor="middle" className="scanner-health-ring__text">{scan.health.score}</text>
          <text x="60" y="75" textAnchor="middle" className="scanner-health-ring__label">/ 100</text>
        </svg>
        <div className="scanner-health-detail__bars">
          <HealthBarRow label="Test Coverage" level={scan.health.test_coverage} />
          <HealthBarRow label="Code Quality" level={scan.health.code_quality} />
          <HealthBarRow label="Security" level={scan.health.security} />
          <HealthBarRow label="Documentation" level={scan.health.documentation} />
        </div>
      </div>

      {scan.health.issues.length > 0 && (
        <div className="scanner-issues">
          <h4>Issues ({scan.health.issues.length})</h4>
          <ul>
            {scan.health.issues.map((issue, i) => <li key={i}>{issue}</li>)}
          </ul>
        </div>
      )}

      <div className="scanner-stats">
        <div className="scanner-stat">
          <span className="scanner-stat__value">{scan.file_analysis.total_files.toLocaleString()}</span>
          <span className="scanner-stat__label">Files</span>
        </div>
        <div className="scanner-stat">
          <span className="scanner-stat__value">{scan.file_analysis.total_lines.toLocaleString()}</span>
          <span className="scanner-stat__label">Lines</span>
        </div>
        <div className="scanner-stat">
          <span className="scanner-stat__value">{Object.keys(scan.file_analysis.languages).length}</span>
          <span className="scanner-stat__label">Languages</span>
        </div>
        <div className="scanner-stat">
          <span className="scanner-stat__value">{scan.file_analysis.directories.length}</span>
          <span className="scanner-stat__label">Dirs</span>
        </div>
      </div>
    </div>
  );
}

function HealthBarRow({ label, level }: { label: string; level: string }) {
  const color = HEALTH_COLORS[level as HealthLevel] || "#9ca3af";
  return (
    <div className="scanner-health-bar">
      <span className="scanner-health-bar__label">{label}</span>
      <span className="scanner-health-bar__dot" style={{ background: color }} />
      <span className="scanner-health-bar__level" style={{ color }}>{level}</span>
    </div>
  );
}

/* ── Tech Stack Tab ── */

function TechTab({ scan }: { scan: ScanResult }) {
  return (
    <div className="scanner-tab-panel">
      <div className="scanner-tech-grid">
        {Object.keys(scan.tech_stack.languages).length > 0 && (
          <div className="scanner-tech-card">
            <span className="scanner-tech-card__label">Languages</span>
            <div className="scanner-tech-card__items">
              {Object.entries(scan.tech_stack.languages).map(([lang, pct]) => (
                <span key={lang} className="scanner-tag scanner-tag--lang">{lang} <span className="scanner-tag__pct">{pct}%</span></span>
              ))}
            </div>
          </div>
        )}
        {scan.tech_stack.frameworks.length > 0 && (
          <div className="scanner-tech-card">
            <span className="scanner-tech-card__label">Frameworks</span>
            <div className="scanner-tech-card__items">
              {scan.tech_stack.frameworks.map((fw) => <span key={fw} className="scanner-tag scanner-tag--fw">{fw}</span>)}
            </div>
          </div>
        )}
        {scan.tech_stack.databases.length > 0 && (
          <div className="scanner-tech-card">
            <span className="scanner-tech-card__label">Databases</span>
            <div className="scanner-tech-card__items">
              {scan.tech_stack.databases.map((db) => <span key={db} className="scanner-tag scanner-tag--db">{db}</span>)}
            </div>
          </div>
        )}
        {scan.tech_stack.tools.length > 0 && (
          <div className="scanner-tech-card">
            <span className="scanner-tech-card__label">Tools</span>
            <div className="scanner-tech-card__items">
              {scan.tech_stack.tools.map((tool) => <span key={tool} className="scanner-tag scanner-tag--tool">{tool}</span>)}
            </div>
          </div>
        )}
      </div>
      <div className="scanner-capabilities">
        <CapabilityBadge label="Docker" active={scan.tech_stack.has_docker} />
        <CapabilityBadge label="CI/CD" active={scan.tech_stack.has_ci_cd} />
        <CapabilityBadge label="Tests" active={scan.tech_stack.has_tests} />
        <CapabilityBadge label="Linting" active={scan.tech_stack.has_linting} />
        <CapabilityBadge label="Type Check" active={scan.tech_stack.has_type_checking} />
      </div>
    </div>
  );
}

function CapabilityBadge({ label, active }: { label: string; active: boolean }) {
  return <span className={active ? "scanner-capability scanner-capability--active" : "scanner-capability"}>{active ? "\u2713" : "\u2717"} {label}</span>;
}

/* ── Tests Tab ── */

function TestsTab({ scan }: { scan: ScanResult }) {
  return (
    <div className="scanner-tab-panel">
      {scan.test_suites.map((suite) => (
        <div key={suite.name} className="scanner-test-suite">
          <div className="scanner-test-suite__header">
            <strong>{suite.name}</strong>
            <span className="scanner-test-suite__framework">{suite.framework}</span>
          </div>
          <div className="scanner-test-bar">
            <div className="scanner-test-bar__passed" style={{ width: suite.total > 0 ? (suite.passed / suite.total * 100) + "%" : "0%" }} />
            <div className="scanner-test-bar__failed" style={{ width: suite.total > 0 ? (suite.failed / suite.total * 100) + "%" : "0%" }} />
          </div>
          <div className="scanner-test-suite__stats">
            <span className="scanner-test-stat scanner-test-stat--passed">{suite.passed} passed</span>
            <span className="scanner-test-stat scanner-test-stat--failed">{suite.failed} failed</span>
            <span className="scanner-test-stat scanner-test-stat--skipped">{suite.skipped} skipped</span>
          </div>
        </div>
      ))}
      {scan.lint_results.length > 0 && (
        <>
          <h4 style={{ margin: "16px 0 8px", fontSize: 13, fontWeight: 700, color: "#111827" }}>Lint Results</h4>
          {scan.lint_results.map((lint) => (
            <div key={lint.tool} className="scanner-test-suite">
              <div className="scanner-test-suite__header">
                <strong>{lint.tool}</strong>
                <span className="scanner-test-suite__framework">{lint.total_issues} issues</span>
              </div>
              <div className="scanner-test-suite__stats">
                <span className="scanner-test-stat scanner-test-stat--failed">{lint.errors} errors</span>
                <span className="scanner-test-stat scanner-test-stat--skipped">{lint.warnings} warnings</span>
              </div>
            </div>
          ))}
        </>
      )}
    </div>
  );
}

/* ── Security Tab ── */

function SecurityTab({ scan }: { scan: ScanResult }) {
  return (
    <div className="scanner-tab-panel">
      <div className="scanner-security-summary">
        {scan.security_scan.critical > 0 && <span className="scanner-security-badge scanner-security-badge--critical">{scan.security_scan.critical} Critical</span>}
        {scan.security_scan.high > 0 && <span className="scanner-security-badge scanner-security-badge--high">{scan.security_scan.high} High</span>}
        {scan.security_scan.medium > 0 && <span className="scanner-security-badge scanner-security-badge--medium">{scan.security_scan.medium} Medium</span>}
        {scan.security_scan.low > 0 && <span className="scanner-security-badge scanner-security-badge--low">{scan.security_scan.low} Low</span>}
      </div>
      {scan.security_scan.issues.length > 0 && (
        <div className="scanner-security-list">
          {scan.security_scan.issues.map((issue, i) => (
            <div key={i} className="scanner-security-item">
              <span className={"scanner-security-severity scanner-security-severity--" + issue.severity}>{issue.severity}</span>
              <span className="scanner-security-package">{issue.package}</span>
              {issue.description && <span className="scanner-security-desc">{issue.description}</span>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

/* ── Documents Tab ── */

interface DocumentsTabProps {
  scan: ScanResult;
  generatedDocs: GeneratedDocument[];
  selectedDoc: GeneratedDocument | null;
  setSelectedDoc: (doc: GeneratedDocument | null) => void;
  selectedSuggestionKeys: Set<string>;
  toggleSuggestionKey: (key: string) => void;
  generatingKeys: Set<string>;
  onGenerate: (keys: string[]) => void;
}

function DocumentsTab({ scan, generatedDocs, selectedDoc, setSelectedDoc, selectedSuggestionKeys, toggleSuggestionKey, generatingKeys, onGenerate }: DocumentsTabProps) {
  return (
    <div className="scanner-tab-panel">
      {selectedDoc && (
        <div className="scanner-doc-preview">
          <div className="scanner-doc-preview__header">
            <div>
              <span className="scanner-doc-preview__key">{selectedDoc.template_key}</span>
              <strong>{selectedDoc.name}</strong>
            </div>
            <button type="button" className="button button--quiet button--sm" onClick={() => setSelectedDoc(null)}>Close preview</button>
          </div>
          <div className="scanner-doc-preview__body">
            <MarkdownPreview content={selectedDoc.content} />
          </div>
        </div>
      )}

      {generatedDocs.length > 0 && !selectedDoc && (
        <div className="scanner-generated-list">
          {generatedDocs.map((doc) => (
            <div
              key={doc.id}
              className="scanner-generated-item"
              onClick={() => setSelectedDoc(doc)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => { if (e.key === "Enter") setSelectedDoc(doc); }}
            >
              <span className="scanner-generated-item__key">{doc.template_key}</span>
              <div className="scanner-generated-item__info">
                <strong>{doc.name}</strong>
                <span className="scanner-generated-item__time">{new Date(doc.created_at).toLocaleString()}</span>
              </div>
              <span className="scanner-generated-item__view">View</span>
            </div>
          ))}
        </div>
      )}

      <div className="scanner-suggestions-section">
        <div className="scanner-suggestions-header">
          <h4>{generatedDocs.length > 0 ? "Generate more" : "Select documents to generate"}</h4>
          {selectedSuggestionKeys.size > 0 && (
            <button type="button" className="scanner-generate-btn" disabled={generatingKeys.size > 0} onClick={() => onGenerate(Array.from(selectedSuggestionKeys))}>
              {generatingKeys.size > 0 ? "Generating..." : "Generate " + selectedSuggestionKeys.size}
            </button>
          )}
        </div>
        <div className="scanner-suggestions">
          {scan.suggestions.map((suggestion) => {
            const isGenerated = generatedDocs.some((d) => d.template_key === suggestion.template_key);
            const isSelected = selectedSuggestionKeys.has(suggestion.template_key);
            const isGenerating = generatingKeys.has(suggestion.template_key);
            return (
              <div
                key={suggestion.template_key}
                className={"scanner-suggestion" + (isSelected ? " scanner-suggestion--selected" : "") + (isGenerated ? " scanner-suggestion--generated" : "")}
                onClick={() => { if (!isGenerated) toggleSuggestionKey(suggestion.template_key); }}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => { if (e.key === "Enter" && !isGenerated) toggleSuggestionKey(suggestion.template_key); }}
              >
                <div className="scanner-suggestion__left">
                  <span className="scanner-suggestion__check">{isGenerated ? "\u2713" : isSelected ? "\u2611" : "\u2610"}</span>
                  <span className="scanner-suggestion__key">{suggestion.template_key}</span>
                  <div className="scanner-suggestion__info">
                    <strong className="scanner-suggestion__name">{suggestion.name}</strong>
                    <p className="scanner-suggestion__reason">{suggestion.reason}</p>
                  </div>
                </div>
                <div className="scanner-suggestion__right">
                  <span className={"scanner-suggestion__priority scanner-suggestion__priority--" + suggestion.priority}>{PRIORITY_LABELS[suggestion.priority] || suggestion.priority}</span>
                  {isGenerated && <span className="scanner-suggestion__done">Done</span>}
                  {isGenerating && <span className="scanner-suggestion__generating">...</span>}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
