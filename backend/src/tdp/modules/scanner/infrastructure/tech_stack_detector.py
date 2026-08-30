import os
from pathlib import Path

from tdp.modules.scanner.domain.model import TechStack
from tdp.modules.scanner.infrastructure.file_analyzer import FileAnalysis


def detect_tech_stack(analysis: FileAnalysis, repo_path: str) -> TechStack:
    root = Path(repo_path)
    stack = TechStack()

    total_files = sum(analysis.languages.values()) or 1
    for lang, count in sorted(analysis.languages.items(), key=lambda x: -x[1]):
        if lang not in ("Markdown", "YAML", "JSON", "XML", "TOML", "HTML", "CSS", "SCSS"):
            stack.languages[lang] = round(count / total_files * 100, 1)

    cfg = set(analysis.config_files)

    if "package.json" in cfg:
        stack.package_manager = "npm"
        if (root / "yarn.lock").exists():
            stack.package_manager = "yarn"
        elif (root / "pnpm-lock.yaml").exists():
            stack.package_manager = "pnpm"
    elif "requirements.txt" in cfg or "Pipfile" in cfg or "pyproject.toml" in cfg:
        stack.package_manager = "pip"
    elif "go.mod" in cfg:
        stack.package_manager = "go modules"
    elif "Cargo.toml" in cfg:
        stack.package_manager = "cargo"
    elif "Gemfile" in cfg:
        stack.package_manager = "bundler"

    if "Python" in analysis.languages:
        py_text = _get_python_deps_text(root)
        if "django" in py_text:
            stack.frameworks.append("Django")
        if "flask" in py_text:
            stack.frameworks.append("Flask")
        if "fastapi" in py_text:
            stack.frameworks.append("FastAPI")
        if "celery" in py_text:
            stack.tools.append("Celery")
        if "sqlalchemy" in py_text:
            stack.tools.append("SQLAlchemy")
        if "pydantic" in py_text:
            stack.tools.append("Pydantic")

    if "JavaScript" in analysis.languages or "TypeScript" in analysis.languages or "TypeScript (React)" in analysis.languages or "JavaScript (React)" in analysis.languages:
        pkg_text = _get_package_json_text(root)
        if '"next"' in pkg_text:
            stack.frameworks.append("Next.js")
        if '"react"' in pkg_text:
            stack.frameworks.append("React")
        if '"react-dom"' in pkg_text:
            if "React" not in stack.frameworks:
                stack.frameworks.append("React")
        if '"vue"' in pkg_text:
            stack.frameworks.append("Vue.js")
        if '"@angular/core"' in pkg_text:
            stack.frameworks.append("Angular")
        if '"express"' in pkg_text:
            stack.frameworks.append("Express.js")
        if '"fastify"' in pkg_text:
            stack.frameworks.append("Fastify")
        if '"@nestjs/core"' in pkg_text:
            stack.frameworks.append("NestJS")
        if '"svelte"' in pkg_text:
            stack.frameworks.append("Svelte")
        if '"tailwindcss"' in pkg_text:
            stack.tools.append("Tailwind CSS")
        if '"prisma"' in pkg_text or '"@prisma/client"' in pkg_text:
            stack.tools.append("Prisma")
        if '"drizzle-orm"' in pkg_text:
            stack.tools.append("Drizzle ORM")
        if '"zod"' in pkg_text:
            stack.tools.append("Zod")
        if '"trpc"' in pkg_text or '"@trpc/server"' in pkg_text:
            stack.frameworks.append("tRPC")

    if "Java" in analysis.languages:
        pom_text = _get_pom_text(root)
        if "spring-boot" in pom_text:
            stack.frameworks.append("Spring Boot")
        if "spring-cloud" in pom_text:
            stack.tools.append("Spring Cloud")

    if "Go" in analysis.languages:
        go_text = _get_go_mod_text(root)
        if "gin-gonic" in go_text:
            stack.frameworks.append("Gin")
        if "labstack/echo" in go_text:
            stack.frameworks.append("Echo")
        if "gofiber" in go_text:
            stack.frameworks.append("Fiber")

    stack.has_docker = analysis.has_dockerfile or analysis.has_docker_compose

    all_text = _get_all_config_text(root, analysis)
    if "postgres" in all_text:
        stack.databases.append("PostgreSQL")
    if "mysql" in all_text:
        stack.databases.append("MySQL")
    if "sqlite" in all_text:
        stack.databases.append("SQLite")
    if "redis" in all_text:
        stack.databases.append("Redis")
    if "mongodb" in all_text or "mongoose" in all_text:
        stack.databases.append("MongoDB")

    if "jest.config.js" in cfg or "jest.config.ts" in cfg:
        stack.tools.append("Jest")
    if "vitest.config.ts" in cfg:
        stack.tools.append("Vitest")
    if "pytest.ini" in cfg or "tox.ini" in cfg:
        stack.tools.append("pytest")
    if cfg & {".eslintrc", ".eslintrc.js", ".eslintrc.json", "eslint.config.js"}:
        stack.tools.append("ESLint")
    if cfg & {".prettierrc", "prettier.config.js"}:
        stack.tools.append("Prettier")
    if "tsconfig.json" in cfg:
        stack.tools.append("TypeScript Compiler")

    stack.has_ci_cd = (root / ".github" / "workflows").exists() or ".gitlab-ci.yml" in cfg
    stack.has_tests = _has_tests(root, analysis)
    stack.has_linting = bool(cfg & {".eslintrc", ".eslintrc.js", ".eslintrc.json", "eslint.config.js", ".flake8", "ruff.toml", "mypy.ini"})
    stack.has_type_checking = bool(cfg & {"tsconfig.json", "jsconfig.json", "mypy.ini"})

    return stack


def _get_python_deps_text(root: Path) -> str:
    parts = []
    search_dirs = [root, root / "backend", root / "server", root / "api", root / "src"]
    for d in search_dirs:
        for fname in ["requirements.txt", "requirements-dev.txt", "pyproject.toml", "setup.py", "setup.cfg", "Pipfile"]:
            try:
                parts.append((d / fname).read_text(encoding="utf-8", errors="ignore").lower())
            except OSError:
                pass
    return " ".join(parts)


def _get_package_json_text(root: Path) -> str:
    search_dirs = [root, root / "frontend", root / "client", root / "web", root / "app"]
    parts = []
    for d in search_dirs:
        try:
            parts.append((d / "package.json").read_text(encoding="utf-8", errors="ignore"))
        except OSError:
            pass
    return " ".join(parts)


def _get_pom_text(root: Path) -> str:
    try:
        return (root / "pom.xml").read_text(encoding="utf-8", errors="ignore").lower()
    except OSError:
        return ""


def _get_go_mod_text(root: Path) -> str:
    try:
        return (root / "go.mod").read_text(encoding="utf-8", errors="ignore").lower()
    except OSError:
        return ""


def _has_tests(root: Path, analysis: FileAnalysis) -> bool:
    dirs = set(analysis.directories)
    if any("test" in d.lower() or "spec" in d.lower() for d in dirs):
        return True
    cfg = set(analysis.config_files)
    if cfg & {"pytest.ini", "tox.ini", "jest.config.js", "jest.config.ts", "vitest.config.ts"}:
        return True
    for dirpath, _, filenames in os.walk(root):
        for fn in filenames:
            if fn.startswith("test_") or fn.endswith(".test.ts") or fn.endswith(".test.js"):
                return True
    return False


def _file_contains(root: Path, filename: str, terms: list[str]) -> bool:
    filepath = root / filename
    if not filepath.exists():
        return False
    try:
        text = filepath.read_text(encoding="utf-8", errors="ignore").lower()
        return any(term.lower() in text for term in terms)
    except OSError:
        return False


def _get_all_config_text(root: Path, analysis: FileAnalysis) -> str:
    parts = []
    for cfg in analysis.config_files:
        try:
            parts.append((root / cfg).read_text(encoding="utf-8", errors="ignore").lower())
        except OSError:
            pass
    for req in ["requirements.txt", "package.json", "go.mod", "Cargo.toml"]:
        try:
            parts.append((root / req).read_text(encoding="utf-8", errors="ignore").lower())
        except OSError:
            pass
    return " ".join(parts)
