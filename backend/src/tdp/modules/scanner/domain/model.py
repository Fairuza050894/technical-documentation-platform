from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4


class ScanStatus(StrEnum):
    PENDING = "PENDING"
    CLONING = "CLONING"
    ANALYZING = "ANALYZING"
    TESTING = "TESTING"
    GENERATING = "GENERATING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ProjectStage(StrEnum):
    PLANNING = "PLANNING"
    DEVELOPMENT = "DEVELOPMENT"
    TESTING_PHASE = "TESTING"
    DEPLOYMENT = "DEPLOYMENT"
    MAINTENANCE = "MAINTENANCE"


class HealthLevel(StrEnum):
    GOOD = "GOOD"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class ScanId:
    value: UUID

    @classmethod
    def new(cls) -> "ScanId":
        return cls(uuid4())

    @classmethod
    def from_string(cls, value: str) -> "ScanId":
        return cls(UUID(value))

    def __str__(self) -> str:
        return str(self.value)


@dataclass
class TechStack:
    languages: dict[str, float] = field(default_factory=dict)
    frameworks: list[str] = field(default_factory=list)
    databases: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)
    package_manager: str = ""
    has_docker: bool = False
    has_ci_cd: bool = False
    has_tests: bool = False
    has_linting: bool = False
    has_type_checking: bool = False


@dataclass
class FileAnalysis:
    total_files: int = 0
    total_lines: int = 0
    languages: dict[str, int] = field(default_factory=dict)
    directories: list[str] = field(default_factory=list)
    has_readme: bool = False
    has_license: bool = False
    has_changelog: bool = False
    has_env_example: bool = False
    has_dockerfile: bool = False
    has_docker_compose: bool = False
    has_makefile: bool = False
    has_gitignore: bool = False
    config_files: list[str] = field(default_factory=list)


@dataclass
class TestCase:
    name: str
    status: str
    duration: float = 0.0
    error_message: str = ""


@dataclass
class TestSuite:
    name: str
    framework: str
    total: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    duration: float = 0.0
    error_output: str = ""
    test_cases: list[TestCase] = field(default_factory=list)


@dataclass
class LintResult:
    tool: str
    total_issues: int = 0
    errors: int = 0
    warnings: int = 0
    issues: list[str] = field(default_factory=list)


@dataclass
class SecurityIssue:
    package: str
    severity: str
    description: str
    fix_version: str = ""


@dataclass
class SecurityScan:
    tool: str
    total_vulnerabilities: int = 0
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    issues: list[SecurityIssue] = field(default_factory=list)
    error_output: str = ""


@dataclass
class DocumentSuggestion:
    template_key: str
    document_type: str
    name: str
    reason: str
    priority: str
    auto_generated: bool = False
    content: str = ""


@dataclass
class ProjectHealth:
    overall: HealthLevel = HealthLevel.UNKNOWN
    test_coverage: HealthLevel = HealthLevel.UNKNOWN
    code_quality: HealthLevel = HealthLevel.UNKNOWN
    security: HealthLevel = HealthLevel.UNKNOWN
    documentation: HealthLevel = HealthLevel.UNKNOWN
    score: int = 0
    issues: list[str] = field(default_factory=list)



@dataclass
class SonarQubeResult:
    project_key: str = ""
    bugs: int = 0
    vulnerabilities: int = 0
    code_smells: int = 0
    coverage: float = 0.0
    duplicated_lines_density: float = 0.0
    ncloc: int = 0
    sqale_rating: str = "A"
    reliability_rating: str = "A"
    security_rating: str = "A"
    security_hotspots: int = 0
    cognitive_complexity: int = 0
    issues_blocker: int = 0
    issues_critical: int = 0
    issues_major: int = 0
    issues_minor: int = 0
    issues_info: int = 0
    total_score: int = 0
    security_score: int = 0
    reliability_score: int = 0
    maintainability_score: int = 0
    coverage_score: int = 0
    error: str = ""


@dataclass
class ScanResult:
    id: ScanId
    repository_url: str
    repository_name: str
    branch: str
    status: ScanStatus
    stage: ProjectStage
    file_analysis: FileAnalysis
    tech_stack: TechStack
    test_suites: list[TestSuite]
    lint_results: list[LintResult]
    security_scan: SecurityScan
    health: ProjectHealth
    suggestions: list[DocumentSuggestion]
    sonarqube: SonarQubeResult
    error_message: str
    started_at: datetime
    completed_at: datetime | None

    @classmethod
    def create(cls, repository_url: str, branch: str = "main") -> "ScanResult":
        now = datetime.now(UTC)
        name = repository_url.rstrip("/").split("/")[-1].replace(".git", "")
        return cls(
            id=ScanId.new(),
            repository_url=repository_url,
            repository_name=name,
            branch=branch,
            status=ScanStatus.PENDING,
            stage=ProjectStage.DEVELOPMENT,
            file_analysis=FileAnalysis(),
            tech_stack=TechStack(),
            test_suites=[],
            lint_results=[],
            security_scan=SecurityScan(tool="none"),
            health=ProjectHealth(),
            suggestions=[],
            sonarqube=SonarQubeResult(),
            error_message="",
            started_at=now,
            completed_at=None,
        )

    def mark_completed(self) -> None:
        self.status = ScanStatus.COMPLETED
        self.completed_at = datetime.now(UTC)

    def mark_failed(self, error: str) -> None:
        self.status = ScanStatus.FAILED
        self.error_message = error
        self.completed_at = datetime.now(UTC)



@dataclass
class MetricDelta:
    label: str
    before: str
    after: str
    direction: str  # "up", "down", "same"
    value_change: float = 0.0


@dataclass
class ScanComparison:
    scan_before_id: str
    scan_after_id: str
    repository_name: str
    time_between: str
    health_score_before: int
    health_score_after: int
    health_score_delta: int
    files_before: int
    files_after: int
    files_delta: int
    lines_before: int
    lines_after: int
    lines_delta: int
    issues_before: list[str] = field(default_factory=list)
    issues_after: list[str] = field(default_factory=list)
    issues_added: list[str] = field(default_factory=list)
    issues_removed: list[str] = field(default_factory=list)
    frameworks_before: list[str] = field(default_factory=list)
    frameworks_after: list[str] = field(default_factory=list)
    frameworks_added: list[str] = field(default_factory=list)
    frameworks_removed: list[str] = field(default_factory=list)
    test_total_before: int = 0
    test_total_after: int = 0
    test_passed_before: int = 0
    test_passed_after: int = 0
    security_total_before: int = 0
    security_total_after: int = 0
    security_critical_before: int = 0
    security_critical_after: int = 0
    metrics: list[MetricDelta] = field(default_factory=list)
    is_identical: bool = False
