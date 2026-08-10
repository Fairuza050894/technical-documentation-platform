import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ProjectDocumentationOverview } from "./ProjectDocumentationOverview";
import type { ProjectDocumentationContext } from "./governanceTypes";

const projectId = "11111111-1111-4111-8111-111111111111";
const evidenceId = "22222222-2222-4222-8222-222222222222";

function documentationContext(): ProjectDocumentationContext {
  return {
    checklist: {
      project_id: projectId,
      policy_key: "project-documentation-baseline-v1",
      registry_schema_version: "document-type-registry-v1",
      total: 2,
      required_total: 2,
      supplementary_total: 0,
      available_total: 0,
      missing_required_total: 2,
      items: [
        {
          document_type: "HLD",
          display_name: "High Level Design",
          automation_profile: "HYBRID",
          requirement: "REQUIRED",
          availability: "MISSING",
          latest_document_id: null,
          latest_version_id: null,
          latest_version: null,
          latest_status: null,
        },
        {
          document_type: "AS_BUILT",
          display_name: "As-Built Documentation",
          automation_profile: "EVIDENCE_DRIVEN",
          requirement: "REQUIRED",
          availability: "MISSING",
          latest_document_id: null,
          latest_version_id: null,
          latest_version: null,
          latest_status: null,
        },
      ],
    },
    readiness: {
      project_id: projectId,
      project_status: "ACTIVE",
      policy_version: "document-readiness-v1",
      total: 2,
      ready_total: 1,
      partially_ready_total: 0,
      not_ready_total: 1,
      eligible_total: 1,
      required_total: 2,
      required_not_ready_total: 1,
      items: [
        {
          project_id: projectId,
          policy_version: "document-readiness-v1",
          document_type: "HLD",
          display_name: "High Level Design",
          automation_profile: "HYBRID",
          requirement: "REQUIRED",
          availability: "MISSING",
          latest_status: null,
          readiness_state: "READY",
          eligible: true,
          findings: [],
          evidence_count: 1,
          observed_claim_count: 1,
          inferred_claim_count: 0,
          unverified_claim_count: 0,
        },
        {
          project_id: projectId,
          policy_version: "document-readiness-v1",
          document_type: "AS_BUILT",
          display_name: "As-Built Documentation",
          automation_profile: "EVIDENCE_DRIVEN",
          requirement: "REQUIRED",
          availability: "MISSING",
          latest_status: null,
          readiness_state: "NOT_READY",
          eligible: false,
          findings: [
            {
              rule_code: "ASBUILT_OBSERVED_CLAIM_REQUIRED",
              document_type: "AS_BUILT",
              severity: "BLOCKER",
              message: "As-Built factual statements require an observed governed claim.",
              missing_input: "observed-as-built-claim",
              remediation: "Add an observed As-Built claim backed by persisted evidence.",
              supporting_references: [],
            },
          ],
          evidence_count: 1,
          observed_claim_count: 0,
          inferred_claim_count: 1,
          unverified_claim_count: 0,
        },
      ],
    },
    evidence: [
      {
        id: evidenceId,
        workspace_id: "workspace-1",
        project_id: projectId,
        feature_id: null,
        kind: "CATALOG_SNAPSHOT",
        source_system: "API_CATALOG",
        source_reference: "synchronization:sync-1",
        origin_id: "sync-1",
        checksum: "a".repeat(64),
        content_reference: "catalog-snapshot:sync-1",
        collection_method: "DETERMINISTIC_NORMALIZATION",
        collected_by: "Technical Writer",
        captured_at: "2026-08-10T00:00:00Z",
        created_at: "2026-08-10T00:00:00Z",
      },
    ],
    claims: [
      {
        id: "33333333-3333-4333-8333-333333333333",
        workspace_id: "workspace-1",
        project_id: projectId,
        feature_id: null,
        statement: "The solution boundary is represented by the normalized API catalog.",
        classification: "OBSERVED",
        evidence_ids: [evidenceId],
        derivation_reference: "",
        relevant_document_types: ["HLD"],
        asserted_by: "Technical Writer",
        created_at: "2026-08-10T00:00:00Z",
      },
      {
        id: "44444444-4444-4444-8444-444444444444",
        workspace_id: "workspace-1",
        project_id: projectId,
        feature_id: null,
        statement: "The deployment shape is inferred from the API boundary.",
        classification: "INFERRED",
        evidence_ids: [evidenceId],
        derivation_reference: "rule:boundary-v1",
        relevant_document_types: ["AS_BUILT"],
        asserted_by: "Technical Writer",
        created_at: "2026-08-10T00:00:00Z",
      },
    ],
  };
}

describe("ProjectDocumentationOverview", () => {
  it("keeps availability, readiness, and traceability distinct", () => {
    render(
      <ProjectDocumentationOverview
        projectStatus="ACTIVE"
        context={documentationContext()}
        loadState="ready"
        error=""
        onNavigateStage={vi.fn()}
      />,
    );

    expect(screen.getByRole("heading", { name: "Project documentation" })).toBeInTheDocument();
    expect(screen.getByText("Required coverage")).toBeInTheDocument();
    expect(screen.getAllByText("Not created")).toHaveLength(2);
    expect(screen.getByText("Ready")).toBeInTheDocument();
    expect(screen.getAllByText("Blocked").length).toBeGreaterThan(0);

    fireEvent.click(screen.getAllByText("Readiness details")[0]!);
    expect(
      screen.getByText("The solution boundary is represented by the normalized API catalog."),
    ).toBeInTheDocument();
    expect(screen.getAllByText(/1 directly referenced evidence artifact/)).toHaveLength(2);
  });

  it("shows remediation without inventing a navigation target", () => {
    const navigateStage = vi.fn();
    render(
      <ProjectDocumentationOverview
        projectStatus="ACTIVE"
        context={documentationContext()}
        loadState="ready"
        error=""
        onNavigateStage={navigateStage}
      />,
    );

    fireEvent.click(screen.getAllByText("Readiness details")[1]!);
    expect(
      screen.getByText("Add an observed As-Built claim backed by persisted evidence."),
    ).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /As-Built/ })).not.toBeInTheDocument();
    expect(navigateStage).not.toHaveBeenCalled();
  });

  it("preserves archived-project governance as read-only", () => {
    render(
      <ProjectDocumentationOverview
        projectStatus="ARCHIVED"
        context={documentationContext()}
        loadState="ready"
        error=""
        onNavigateStage={vi.fn()}
      />,
    );

    expect(
      screen.getByText(/Read-only view. Existing governance, readiness, evidence, and claims/),
    ).toBeInTheDocument();
  });
});
