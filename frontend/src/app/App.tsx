import { useEffect, useState } from "react";

import { ApiCatalogWorkspace } from "../modules/catalog/ApiCatalogWorkspace";
import { ChangesWorkspace } from "../modules/changes/ChangesWorkspace";
import { DocumentsWorkspace } from "../modules/documents/DocumentsWorkspace";
import {
  OperationalOverview,
  type OverviewNavigationTarget,
} from "../modules/overview/OperationalOverview";
import { ProjectWorkspace } from "../modules/projects/ProjectWorkspace";
import { SourceWorkspace } from "../modules/sources/SourceWorkspace";

interface HealthResponse {
  status: "ok";
  service: string;
  version: string;
  environment: string;
}

type ApiState =
  | { status: "loading" }
  | { status: "available"; health: HealthResponse }
  | { status: "unavailable" };

const navigationGroups = [
  {
    label: "Workspace",
    items: [
      { id: "Overview", label: "Overview" },
      { id: "Projects", label: "Projects" },
    ],
  },
  {
    label: "Sources",
    items: [
      { id: "Sources", label: "Source registry" },
      { id: "API Catalog", label: "API catalog" },
      { id: "Changes", label: "Change analysis" },
    ],
  },
  {
    label: "Documentation",
    items: [{ id: "Documents", label: "Documents" }],
  },
  {
    label: "System",
    items: [{ id: "System status", label: "System status" }],
  },
] as const;

type NavigationItem = (typeof navigationGroups)[number]["items"][number]["id"];

const navigationLabels = Object.fromEntries(
  navigationGroups.flatMap((group) => group.items.map((item) => [item.id, item.label])),
) as Record<NavigationItem, string>;

export function App() {
  const [apiState, setApiState] = useState<ApiState>({ status: "loading" });
  const [activeNavigation, setActiveNavigation] = useState<NavigationItem>("Overview");

  useEffect(() => {
    const controller = new AbortController();

    async function loadHealth(): Promise<void> {
      try {
        const response = await fetch("http://127.0.0.1:8000/api/health", {
          signal: controller.signal,
        });
        if (!response.ok) {
          throw new Error(`Health request failed with ${response.status}`);
        }
        const health = (await response.json()) as HealthResponse;
        setApiState({ status: "available", health });
      } catch (error: unknown) {
        if (error instanceof DOMException && error.name === "AbortError") {
          return;
        }
        setApiState({ status: "unavailable" });
      }
    }

    void loadHealth();
    return () => controller.abort();
  }, []);

  function navigate(target: OverviewNavigationTarget): void {
    setActiveNavigation(target);
  }

  const activeLabel = navigationLabels[activeNavigation];

  return (
    <div className="app-shell">
      <aside className="sidebar" aria-label="Primary navigation">
        <div className="product-mark" aria-label="Technical Documentation Platform">
          <span className="product-mark__symbol" aria-hidden="true">
            TD
          </span>
          <span>
            <strong>Technical Docs</strong>
            <small>Documentation platform</small>
          </span>
        </div>

        <div className="workspace-context" aria-label="Current workspace context">
          <span>Workspace</span>
          <strong>All projects</strong>
        </div>

        <nav className="primary-navigation">
          {navigationGroups.map((group) => (
            <section className="navigation-group" aria-labelledby={`nav-${group.label}`} key={group.label}>
              <h2 id={`nav-${group.label}`}>{group.label}</h2>
              <ul className="navigation-list">
                {group.items.map((item) => (
                  <li key={item.id}>
                    <button
                      type="button"
                      className={
                        item.id === activeNavigation
                          ? "navigation-item is-active"
                          : "navigation-item"
                      }
                      aria-current={item.id === activeNavigation ? "page" : undefined}
                      onClick={() => setActiveNavigation(item.id)}
                    >
                      <span className="navigation-item__marker" aria-hidden="true" />
                      {item.label}
                    </button>
                  </li>
                ))}
              </ul>
            </section>
          ))}
        </nav>

        <div className="sidebar-service">
          <span
            className={
              apiState.status === "available"
                ? "service-dot service-dot--available"
                : "service-dot"
            }
            aria-hidden="true"
          />
          <span>
            <strong>Backend API</strong>
            <small>
              {apiState.status === "loading" && "Checking service"}
              {apiState.status === "available" && `v${apiState.health.version}`}
              {apiState.status === "unavailable" && "Offline"}
            </small>
          </span>
        </div>
      </aside>

      <div className="application-frame">
        <header className="utility-bar">
          <div className="breadcrumb" aria-label="Breadcrumb">
            <span>Workspace</span>
            <span aria-hidden="true">/</span>
            <strong>{activeLabel}</strong>
          </div>

          <div className="utility-status" aria-label="Runtime context">
            <span className="context-chip">All projects</span>
            <span className="context-chip">
              {apiState.status === "available" ? apiState.health.environment : "local"}
            </span>
            <span
              className={
                apiState.status === "available"
                  ? "context-chip context-chip--success"
                  : "context-chip context-chip--warning"
              }
            >
              {apiState.status === "loading" && "API checking"}
              {apiState.status === "available" && "API available"}
              {apiState.status === "unavailable" && "API offline"}
            </span>
          </div>
        </header>

        <main className="main-content">
          <div className="workspace-canvas">
            {activeNavigation === "Overview" && (
              <OperationalOverview
                serviceState={apiState.status}
                serviceVersion={
                  apiState.status === "available" ? apiState.health.version : undefined
                }
                onNavigate={navigate}
              />
            )}
            {activeNavigation === "Projects" && <ProjectWorkspace />}
            {activeNavigation === "Sources" && <SourceWorkspace />}
            {activeNavigation === "API Catalog" && <ApiCatalogWorkspace />}
            {activeNavigation === "Changes" && <ChangesWorkspace />}
            {activeNavigation === "Documents" && <DocumentsWorkspace />}
            {activeNavigation === "System status" && <SystemStatus apiState={apiState} />}
          </div>
        </main>
      </div>
    </div>
  );
}

function SystemStatus({ apiState }: { apiState: ApiState }) {
  return (
    <>
      <header className="topbar">
        <div>
          <p className="eyebrow">System</p>
          <h1>System status</h1>
          <p className="page-summary">
            Runtime metadata and deterministic documentation policies.
          </p>
        </div>
        <span
          className={
            apiState.status === "available"
              ? "environment-badge environment-badge--success"
              : "environment-badge environment-badge--warning"
          }
        >
          {apiState.status === "available" ? "Operational" : "Service unavailable"}
        </span>
      </header>

      <section className="content-section" aria-labelledby="runtime-status-title">
        <div className="section-heading">
          <div>
            <h2 id="runtime-status-title">Runtime status</h2>
            <p>Live metadata from the local backend health endpoint.</p>
          </div>
        </div>

        <dl className="system-status-grid">
          <div>
            <dt>Service</dt>
            <dd>
              {apiState.status === "available"
                ? apiState.health.service
                : "Technical Documentation Platform"}
            </dd>
          </div>
          <div>
            <dt>Availability</dt>
            <dd>
              {apiState.status === "loading" && "Checking"}
              {apiState.status === "available" && "Available"}
              {apiState.status === "unavailable" && "Offline"}
            </dd>
          </div>
          <div>
            <dt>Version</dt>
            <dd>{apiState.status === "available" ? apiState.health.version : "Unavailable"}</dd>
          </div>
          <div>
            <dt>Environment</dt>
            <dd>
              {apiState.status === "available" ? apiState.health.environment : "Local"}
            </dd>
          </div>
        </dl>
      </section>

      <section className="content-section" aria-labelledby="product-policy-title">
        <div className="section-heading">
          <div>
            <h2 id="product-policy-title">Documentation policy</h2>
            <p>Non-negotiable constraints for every generated artifact.</p>
          </div>
        </div>

        <dl className="constraint-list constraint-list--compact">
          <div>
            <dt>Source-backed facts</dt>
            <dd>Every generated fact keeps a verifiable source reference.</dd>
          </div>
          <div>
            <dt>Deterministic pipeline</dt>
            <dd>Parsing, normalization, comparison, and rendering do not depend on AI.</dd>
          </div>
          <div>
            <dt>Explicit uncertainty</dt>
            <dd>Missing or conflicting information is surfaced instead of invented.</dd>
          </div>
        </dl>
      </section>
    </>
  );
}
