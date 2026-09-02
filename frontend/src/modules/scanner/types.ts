export type ScanStatus = "PENDING" | "CLONING" | "ANALYZING" | "TESTING" | "GENERATING" | "COMPLETED" | "FAILED";

export type ProjectStage = "PLANNING" | "DEVELOPMENT" | "TESTING" | "DEPLOYMENT" | "MAINTENANCE";

export type HealthLevel = "GOOD" | "WARNING" | "CRITICAL" | "UNKNOWN";

export interface FileAnalysis {
  total_files: number;
  total_lines: number;
  languages: Record<string, number>;
  directories: string[];
  has_readme: boolean;
  has_license: boolean;
  has_changelog: boolean;
  has_dockerfile: boolean;
  has_docker_compose: boolean;
  config_files: string[];
}

export interface TechStack {
  languages: Record<string, number>;
  frameworks: string[];
  databases: string[];
  tools: string[];
  package_manager: string;
  has_docker: boolean;
  has_ci_cd: boolean;
  has_tests: boolean;
  has_linting: boolean;
  has_type_checking: boolean;
}

export interface TestSuite {
  name: string;
  framework: string;
  total: number;
  passed: number;
  failed: number;
  skipped: number;
  error_output: string;
}

export interface LintResult {
  tool: string;
  total_issues: number;
  errors: number;
  warnings: number;
}

export interface SecurityScan {
  tool: string;
  total_vulnerabilities: number;
  critical: number;
  high: number;
  medium: number;
  low: number;
  issues: Array<{
    package: string;
    severity: string;
    description: string;
    fix_version: string;
  }>;
}

export interface ProjectHealth {
  overall: HealthLevel;
  test_coverage: HealthLevel;
  code_quality: HealthLevel;
  security: HealthLevel;
  documentation: HealthLevel;
  score: number;
  issues: string[];
}

export interface DocumentSuggestion {
  template_key: string;
  document_type: string;
  name: string;
  reason: string;
  priority: string;
  auto_generated: boolean;
}


export interface SonarQubeResult {
  project_key: string;
  bugs: number;
  vulnerabilities: number;
  code_smells: number;
  coverage: number;
  duplicated_lines_density: number;
  ncloc: number;
  sqale_rating: string;
  reliability_rating: string;
  security_rating: string;
  security_hotspots: number;
  cognitive_complexity: number;
  issues_blocker: number;
  issues_critical: number;
  issues_major: number;
  issues_minor: number;
  issues_info: number;
  total_score: number;
  security_score: number;
  reliability_score: number;
  maintainability_score: number;
  coverage_score: number;
  error: string;
}


export interface WebhookEvent {
  id: string;
  event_type: string;
  repository_url: string;
  repository_name: string;
  branch: string;
  commit_sha: string;
  commit_message: string;
  sender: string;
  status: string;
  scan_id: string;
  previous_scan_id: string;
  score_delta: number;
  error_message: string;
  created_at: string;
  processed_at: string | null;
}

export interface WebhookEventCollection {
  items: WebhookEvent[];
  total: number;
}

export interface ScanResult {
  id: string;
  repository_url: string;
  repository_name: string;
  branch: string;
  status: ScanStatus;
  stage: ProjectStage;
  file_analysis: FileAnalysis;
  tech_stack: TechStack;
  test_suites: TestSuite[];
  lint_results: LintResult[];
  security_scan: SecurityScan;
  health: ProjectHealth;
  suggestions: DocumentSuggestion[];
  sonarqube: SonarQubeResult;
  error_message: string;
  started_at: string;
  completed_at: string | null;
}

export interface ScanCollection {
  items: ScanResult[];
  total: number;
}

export const STATUS_LABELS: Record<ScanStatus, string> = {
  PENDING: "Queued",
  CLONING: "Cloning repository...",
  ANALYZING: "Analyzing codebase...",
  TESTING: "Running tests & lint...",
  GENERATING: "Generating suggestions...",
  COMPLETED: "Completed",
  FAILED: "Failed",
};

export const STATUS_STEPS: ScanStatus[] = ["PENDING", "CLONING", "ANALYZING", "TESTING", "GENERATING", "COMPLETED"];

export const HEALTH_COLORS: Record<HealthLevel, string> = {
  GOOD: "#16a34a",
  WARNING: "#f59e0b",
  CRITICAL: "#dc2626",
  UNKNOWN: "#9ca3af",
};

export const PRIORITY_LABELS: Record<string, string> = {
  must: "Must Have",
  should: "Should Have",
  could: "Could Have",
};

export interface MetricDelta {
  label: string;
  before: string;
  after: string;
  direction: "up" | "down" | "same";
  value_change: number;
}

export interface ScanComparison {
  scan_before_id: string;
  scan_after_id: string;
  repository_name: string;
  time_between: string;
  health_score_before: number;
  health_score_after: number;
  health_score_delta: number;
  files_before: number;
  files_after: number;
  files_delta: number;
  lines_before: number;
  lines_after: number;
  lines_delta: number;
  issues_added: string[];
  issues_removed: string[];
  frameworks_added: string[];
  frameworks_removed: string[];
  test_total_before: number;
  test_total_after: number;
  test_passed_before: number;
  test_passed_after: number;
  security_total_before: number;
  security_total_after: number;
  security_critical_before: number;
  security_critical_after: number;
  metrics: MetricDelta[];
  is_identical: boolean;
}
