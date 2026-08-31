from dataclasses import dataclass
from typing import Any

import httpx


@dataclass(frozen=True, slots=True)
class SonarQubeConfig:
    url: str
    token: str
    project_key: str


@dataclass
class SonarQubeMetrics:
    project_key: str
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
    error: str = ""


class SonarQubeClient:
    METRIC_KEYS = [
        "bugs", "vulnerabilities", "code_smells", "coverage",
        "duplicated_lines_density", "ncloc", "sqale_rating",
        "reliability_rating", "security_rating", "security_hotspots",
        "cognitive_complexity",
    ]

    ISSUE_SEVERITIES = ["BLOCKER", "CRITICAL", "MAJOR", "MINOR", "INFO"]

    def __init__(self, config: SonarQubeConfig) -> None:
        self._config = config
        self._base_url = config.url.rstrip("/")
        self._headers = {"Authorization": f"Bearer {config.token}"}

    def fetch_metrics(self) -> SonarQubeMetrics:
        try:
            measures = self._fetch_measures()
            issue_counts = self._fetch_issue_counts()
            return SonarQubeMetrics(
                project_key=self._config.project_key,
                bugs=int(measures.get("bugs", "0")),
                vulnerabilities=int(measures.get("vulnerabilities", "0")),
                code_smells=int(measures.get("code_smells", "0")),
                coverage=float(measures.get("coverage", "0")),
                duplicated_lines_density=float(measures.get("duplicated_lines_density", "0")),
                ncloc=int(measures.get("ncloc", "0")),
                sqale_rating=self._rating_letter(measures.get("sqale_rating", "1.0")),
                reliability_rating=self._rating_letter(measures.get("reliability_rating", "1.0")),
                security_rating=self._rating_letter(measures.get("security_rating", "1.0")),
                security_hotspots=int(measures.get("security_hotspots", "0")),
                cognitive_complexity=int(measures.get("cognitive_complexity", "0")),
                issues_blocker=issue_counts.get("BLOCKER", 0),
                issues_critical=issue_counts.get("CRITICAL", 0),
                issues_major=issue_counts.get("MAJOR", 0),
                issues_minor=issue_counts.get("MINOR", 0),
                issues_info=issue_counts.get("INFO", 0),
            )
        except Exception as exc:
            return SonarQubeMetrics(
                project_key=self._config.project_key,
                error=str(exc),
            )

    def _fetch_measures(self) -> dict[str, str]:
        response = httpx.get(
            f"{self._base_url}/api/measures/component",
            params={
                "component": self._config.project_key,
                "metricKeys": ",".join(self.METRIC_KEYS),
            },
            headers=self._headers,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        component = data.get("component", {})
        measures_list = component.get("measures", [])
        return {m["metric"]: m["value"] for m in measures_list if "value" in m}

    def _fetch_issue_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for severity in self.ISSUE_SEVERITIES:
            response = httpx.get(
                f"{self._base_url}/api/issues/search",
                params={
                    "componentKeys": self._config.project_key,
                    "severities": severity,
                    "ps": 1,
                },
                headers=self._headers,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            counts[severity] = data.get("total", 0)
        return counts

    @staticmethod
    def _rating_letter(value: str) -> str:
        mapping = {"1.0": "A", "2.0": "B", "3.0": "C", "4.0": "D", "5.0": "E"}
        return mapping.get(value, "A")


def map_sonarqube_to_health(metrics: SonarQubeMetrics) -> dict[str, Any]:
    if metrics.error:
        return {"error": metrics.error}

    # Security: based on vulnerabilities + security_rating
    security_score = 25
    if metrics.security_rating == "E":
        security_score = 0
    elif metrics.security_rating == "D":
        security_score = 5
    elif metrics.security_rating == "C":
        security_score = 10
    elif metrics.security_rating == "B":
        security_score = 20

    # Reliability: based on bugs + reliability_rating
    reliability_score = 25
    if metrics.reliability_rating == "E":
        reliability_score = 0
    elif metrics.reliability_rating == "D":
        reliability_score = 5
    elif metrics.reliability_rating == "C":
        reliability_score = 10
    elif metrics.reliability_rating == "B":
        reliability_score = 20

    # Maintainability: based on code_smells + sqale_rating
    maintainability_score = 25
    if metrics.sqale_rating == "E":
        maintainability_score = 0
    elif metrics.sqale_rating == "D":
        maintainability_score = 5
    elif metrics.sqale_rating == "C":
        maintainability_score = 10
    elif metrics.sqale_rating == "B":
        maintainability_score = 20

    # Coverage: based on coverage percentage
    coverage_score = 25
    if metrics.coverage == 0:
        coverage_score = 0
    elif metrics.coverage < 20:
        coverage_score = 5
    elif metrics.coverage < 50:
        coverage_score = 10
    elif metrics.coverage < 80:
        coverage_score = 20

    total_score = security_score + reliability_score + maintainability_score + coverage_score

    return {
        "total_score": total_score,
        "security_score": security_score,
        "reliability_score": reliability_score,
        "maintainability_score": maintainability_score,
        "coverage_score": coverage_score,
        "security_rating": metrics.security_rating,
        "reliability_rating": metrics.reliability_rating,
        "maintainability_rating": metrics.sqale_rating,
        "coverage_pct": metrics.coverage,
        "bugs": metrics.bugs,
        "vulnerabilities": metrics.vulnerabilities,
        "code_smells": metrics.code_smells,
        "duplicated_lines_density": metrics.duplicated_lines_density,
        "security_hotspots": metrics.security_hotspots,
        "cognitive_complexity": metrics.cognitive_complexity,
        "issues_blocker": metrics.issues_blocker,
        "issues_critical": metrics.issues_critical,
        "issues_major": metrics.issues_major,
        "issues_minor": metrics.issues_minor,
        "issues_info": metrics.issues_info,
    }
