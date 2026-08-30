import os
from pathlib import Path

from tdp.modules.scanner.domain.model import FileAnalysis


EXTENSION_MAP = {
    ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
    ".jsx": "JavaScript (React)", ".tsx": "TypeScript (React)",
    ".java": "Java", ".kt": "Kotlin", ".go": "Go", ".rs": "Rust",
    ".rb": "Ruby", ".php": "PHP", ".cs": "C#",
    ".c": "C", ".cpp": "C++", ".h": "C/C++ Header",
    ".swift": "Swift", ".dart": "Dart",
    ".sql": "SQL", ".graphql": "GraphQL",
    ".html": "HTML", ".css": "CSS", ".scss": "SCSS",
    ".md": "Markdown", ".yaml": "YAML", ".yml": "YAML",
    ".json": "JSON", ".xml": "XML", ".toml": "TOML",
    ".sh": "Shell", ".bash": "Shell", ".zsh": "Shell",
    ".dockerfile": "Dockerfile", ".tf": "Terraform",
}

SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv",
    "dist", "build", ".next", ".nuxt", "target", "vendor",
    ".tox", ".mypy_cache", ".pytest_cache", "coverage",
    ".gradle", ".idea", ".vscode", "__sapper__",
}


def analyze_files(repo_path: str) -> FileAnalysis:
    root = Path(repo_path)
    analysis = FileAnalysis()

    for dirpath, dirnames, filenames in os.walk(root):
        rel_dir = os.path.relpath(dirpath, root)
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]

        if rel_dir != "." and not any(skip in rel_dir for skip in SKIP_DIRS):
            depth = rel_dir.count(os.sep)
            if depth < 3:
                analysis.directories.append(rel_dir)

        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            analysis.total_files += 1

            try:
                with open(filepath, encoding="utf-8", errors="ignore") as f:
                    analysis.total_lines += sum(1 for _ in f)
            except (OSError, UnicodeDecodeError):
                pass

            ext = os.path.splitext(filename)[1].lower()
            if ext in EXTENSION_MAP:
                lang = EXTENSION_MAP[ext]
                analysis.languages[lang] = analysis.languages.get(lang, 0) + 1

            upper_name = filename.upper()
            if upper_name.startswith("README"):
                analysis.has_readme = True
            if upper_name.startswith("LICENSE"):
                analysis.has_license = True
            if upper_name.startswith("CHANGELOG") or upper_name.startswith("CHANGES"):
                analysis.has_changelog = True
            if ".env.example" in filename.lower() or ".env.sample" in filename.lower():
                analysis.has_env_example = True
            if filename.lower() == "dockerfile" or filename.lower().endswith(".dockerfile"):
                analysis.has_dockerfile = True
            if "docker-compose" in filename.lower():
                analysis.has_docker_compose = True
            if filename == "Makefile":
                analysis.has_makefile = True
            if filename == ".gitignore":
                analysis.has_gitignore = True

            config_files = [
                "package.json", "requirements.txt", "Pipfile", "pyproject.toml",
                "setup.py", "setup.cfg", "Cargo.toml", "go.mod", "Gemfile",
                "composer.json", "pom.xml", "build.gradle", "Dockerfile",
                "docker-compose.yml", "docker-compose.yaml",
                ".eslintrc", ".eslintrc.js", ".eslintrc.json", "eslint.config.js",
                ".prettierrc", "prettier.config.js",
                "tsconfig.json", "jsconfig.json",
                "jest.config.js", "jest.config.ts", "vitest.config.ts",
                "pytest.ini", "tox.ini", "mypy.ini", ".flake8", "ruff.toml",
                "Makefile", "Caddyfile", "nginx.conf",
                ".env.example", ".env.sample",
            ]
            if filename in config_files:
                analysis.config_files.append(filename)

    return analysis
