from tdp.modules.scanner.domain.model import (
    DocumentSuggestion,
    FileAnalysis,
    ProjectStage,
    TechStack,
)


def suggest_documents(
    tech_stack: TechStack,
    file_analysis: FileAnalysis,
    stage: ProjectStage,
) -> list[DocumentSuggestion]:
    suggestions: list[DocumentSuggestion] = []

    suggestions.append(DocumentSuggestion(
        template_key="BRD", document_type="BRD",
        name="Business Requirements Document",
        reason="Core document for any software project.",
        priority="must",
    ))

    suggestions.append(DocumentSuggestion(
        template_key="SRS", document_type="SRS",
        name="Software Requirements Specification",
        reason="Technical requirements based on detected tech stack.",
        priority="must",
    ))

    if tech_stack.frameworks or len(tech_stack.languages) > 1:
        suggestions.append(DocumentSuggestion(
            template_key="ARCH", document_type="HLD",
            name="System Architecture Document",
            reason=f"Project uses {len(tech_stack.frameworks)} framework(s): {', '.join(tech_stack.frameworks)}.",
            priority="must",
        ))

    web_frameworks = {"FastAPI", "Flask", "Django", "Express.js", "NestJS", "Spring Boot", "Gin", "Echo"}
    if web_frameworks & set(tech_stack.frameworks):
        matched = [f for f in tech_stack.frameworks if f in web_frameworks]
        suggestions.append(DocumentSuggestion(
            template_key="API_DOC", document_type="LLD",
            name="API Documentation",
            reason=f"Web framework detected: {matched[0]}.",
            priority="must",
        ))

    if tech_stack.databases:
        suggestions.append(DocumentSuggestion(
            template_key="DB_DOC", document_type="LLD",
            name="Database Schema Documentation",
            reason=f"Databases detected: {', '.join(tech_stack.databases)}.",
            priority="should",
        ))

    if tech_stack.has_tests:
        suggestions.append(DocumentSuggestion(
            template_key="TEST_CASES", document_type="UAT_EVIDENCE",
            name="Test Case Specification",
            reason="Project has existing tests. Formalize test cases.",
            priority="should",
        ))
        suggestions.append(DocumentSuggestion(
            template_key="TEST_REPORT", document_type="AS_BUILT",
            name="Test Report",
            reason="Document test results for compliance.",
            priority="should",
        ))

    if stage in (ProjectStage.TESTING_PHASE, ProjectStage.DEPLOYMENT):
        suggestions.append(DocumentSuggestion(
            template_key="UAT_REPORT", document_type="UAT_EVIDENCE",
            name="UAT Report",
            reason=f"Project is in {stage.value} stage. UAT documentation needed.",
            priority="must",
        ))

    if tech_stack.has_docker:
        suggestions.append(DocumentSuggestion(
            template_key="DEPLOY_GUIDE", document_type="INSTALLATION_GUIDE",
            name="Deployment Guide",
            reason="Docker configuration detected. Document deployment process.",
            priority="must",
        ))

    if tech_stack.package_manager:
        suggestions.append(DocumentSuggestion(
            template_key="INSTALL_GUIDE", document_type="INSTALLATION_GUIDE",
            name="Installation Guide",
            reason=f"Package manager: {tech_stack.package_manager}. Document setup process.",
            priority="should",
        ))

    if tech_stack.has_ci_cd:
        suggestions.append(DocumentSuggestion(
            template_key="SOP", document_type="SOP",
            name="Standard Operating Procedure",
            reason="CI/CD pipeline detected. Document operational procedures.",
            priority="should",
        ))

    if not file_analysis.has_readme:
        suggestions.append(DocumentSuggestion(
            template_key="USER_GUIDE", document_type="USER_GUIDE",
            name="User Guide",
            reason="No README found. Project needs user documentation.",
            priority="must",
        ))

    if not file_analysis.has_changelog:
        suggestions.append(DocumentSuggestion(
            template_key="RELEASE_NOTES", document_type="AS_BUILT",
            name="Release Notes",
            reason="No CHANGELOG found. Start documenting releases.",
            priority="should",
        ))

    suggestions.append(DocumentSuggestion(
        template_key="HANDOVER", document_type="PROJECT_HANDOVER",
        name="Project Handover Document",
        reason="Essential for team transitions and knowledge transfer.",
        priority="could",
    ))

    return suggestions
