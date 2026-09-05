const API_BASE = "";

export interface TechTool {
  name: string;
  category: string;
  version: string | null;
  confidence: string;
  evidence_files: string[];
}

export interface DependencyGraph {
  ecosystem: string;
  direct_count: number;
  transitive_count: number;
  packages: { name: string; version: string; direct: boolean }[];
  outdated_count: number;
  vulnerable_count: number;
}

export interface VulnerabilityAlert {
  id: string;
  package_name: string;
  package_version: string;
  ecosystem: string;
  severity: string;
  summary: string;
  fixed_version: string | null;
  aliases: string[];
  published_at: string | null;
  references: string[];
}

export interface ChangeEvent {
  change_type: string;
  description: string;
  affected_files: string[];
  before_snapshot: string | null;
  after_snapshot: string | null;
  severity: string;
}

export interface Snapshot {
  id: string;
  repo_id: string;
  repo_url: string;
  branch: string;
  commit_sha: string;
  commit_message: string;
  committed_at: string;
  tech_stack: TechTool[];
  dependency_graphs: DependencyGraph[];
  change_events: ChangeEvent[];
  vulnerability_alerts: VulnerabilityAlert[];
  total_packages: number;
  critical_vulnerabilities: number;
  created_at: string;
}

export interface TechRadarEntry {
  tool_name: string;
  category: string;
  version: string | null;
  ring: string;
  first_detected_at: string;
  last_seen_at: string;
  scan_count: number;
}

export interface Dashboard {
  repo_id: string;
  repo_url: string;
  latest_snapshot_id: string | null;
  total_snapshots: number;
  tech_stack_summary: Record<string, number>;
  total_vulnerabilities: number;
  critical_vulnerabilities: number;
  total_packages: number;
  last_scanned_at: string | null;
}

export async function analyzeRepo(url: string, branch: string = "main"): Promise<Snapshot> {
  const res = await fetch(`${API_BASE}/api/intelligence/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ repository_url: url, branch }),
  });
  if (!res.ok) throw new Error(`Analyze failed: ${res.status}`);
  return res.json();
}

export async function getSnapshots(repoId: string): Promise<{ items: Snapshot[]; total: number }> {
  const res = await fetch(`${API_BASE}/api/intelligence/snapshots/${repoId}`);
  if (!res.ok) throw new Error(`List snapshots failed: ${res.status}`);
  return res.json();
}

export async function getDashboard(repoId: string): Promise<Dashboard> {
  const res = await fetch(`${API_BASE}/api/intelligence/dashboard/${repoId}`);
  if (!res.ok) throw new Error(`Dashboard failed: ${res.status}`);
  return res.json();
}

export async function getTechRadar(repoId: string): Promise<TechRadarEntry[]> {
  const res = await fetch(`${API_BASE}/api/intelligence/radar/${repoId}`);
  if (!res.ok) throw new Error(`Radar failed: ${res.status}`);
  return res.json();
}
