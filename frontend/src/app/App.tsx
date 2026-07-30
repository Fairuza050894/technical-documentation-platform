import { useEffect, useState } from "react";

import { ApiCatalogWorkspace } from "../modules/catalog/ApiCatalogWorkspace";
import { ChangesWorkspace } from "../modules/changes/ChangesWorkspace";
import { DocumentsWorkspace } from "../modules/documents/DocumentsWorkspace";
import { OperationalOverview } from "../modules/overview/OperationalOverview";
import { ProjectWorkspace } from "../modules/projects/ProjectWorkspace";
import { SourceWorkspace } from "../modules/sources/SourceWorkspace";
import { Icon, type IconName } from "../shared/ui/Icon";

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
      { id: "Overview", label: "Overview", icon: "overview" },
      { id: "Projects", label: "Projects", icon: "projects" },
    ],
  },
  {
    label: "Source intelligence",
    items: [
      { id: "Sources", label: "Source registry", icon: "source" },
      { id: "API Catalog", label: "API catalog", icon: "catalog" },
      { id: "Changes", label: "Change analysis", icon: "changes" },
    ],
  },
  {
    label: "Documentation",
    items: [{ id: "Documents", label: "Documents", icon: "documents" }],
  },
  {
    label: "Platform",
    items: [{ id: "System status", label: "System status", icon: "server" }],
  },
] as const satisfies ReadonlyArray<{
  label: string;
  items: ReadonlyArray<{ id: string; label: string; icon: IconName }>;
}>;

type NavigationItem = (typeof navigationGroups)[number]["items"][number]["id"];

const navigationLabels = Object.fromEntries(
  navigationGroups.flatMap((group) => group.items.map((item) => [item.id, item.label])),
) as Record<NavigationItem, string>;

const navigationIcons = Object.fromEntries(
  navigationGroups.flatMap((group) => group.items.map((item) => [item.id, item.icon])),
) as Record<NavigationItem, IconName>;

export function App() {
  const [apiState, setApiState] = useState<ApiState>({ status: "loading" });
  const [activeNavigation, setActiveNavigation] = useState<NavigationItem>("Overview");

  useEffect(() => {
    document.documentElement.scrollTop = 0;
    document.body.scrollTop = 0;
  }, [activeNavigation]);

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

  function navigate(target: NavigationItem): void {
    setActiveNavigation(target);
  }

  const activeLabel = navigationLabels[activeNavigation];
  const activeIcon = navigationIcons[activeNavigation];
  const environment =
    apiState.status === "available" ? apiState.health.environment : "local";
  const serviceLabel =
    apiState.status === "loading"
      ? "Checking"
      : apiState.status === "available"
        ? "Connected"
        : "Offline";

  return (
    <div className="app-shell">
      <aside className="sidebar" aria-label="Primary navigation">
        <div className="product-mark" aria-label="Technical Documentation Platform">
          <span className="product-mark__symbol" aria-hidden="true">
            <Icon name="documents" size={17} />
          </span>
          <span className="product-mark__copy">
            <strong>Technical Docs</strong>
            <small>Documentation platform</small>
          </span>
        </div>

        <div className="workspace-context" aria-label="Current workspace context">
          <span className="workspace-context__icon" aria-hidden="true">
            <Icon name="folder" size={16} />
          </span>
          <span className="workspace-context__copy">
            <small>Workspace</small>
            <strong>All projects</strong>
          </span>
          <Icon className="workspace-context__chevron" name="chevron-down" size={14} />
        </div>

        <nav className="primary-navigation">
          {navigationGroups.map((group) => (
            <section
              className="navigation-group"
              aria-labelledby={`nav-${group.label.replaceAll(" ", "-")}`}
              key={group.label}
            >
              <h2 id={`nav-${group.label.replaceAll(" ", "-")}`}>{group.label}</h2>
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
                      onClick={() => navigate(item.id)}
                    >
                      <span className="navigation-item__icon" aria-hidden="true">
                        <Icon name={item.icon} size={17} />
                      </span>
                      <span className="navigation-item__label">{item.label}</span>
                    </button>
                  </li>
                ))}
              </ul>
            </section>
          ))}
        </nav>

        <div className="sidebar-service" aria-label={`Backend API ${serviceLabel}`}>
          <span className="sidebar-service__icon" aria-hidden="true">
            <Icon name="server" size={16} />
          </span>
          <span className="sidebar-service__copy">
            <strong>Backend API</strong>
            <small>
              {apiState.status === "loading" && "Checking service"}
              {apiState.status === "available" && `v${apiState.health.version}`}
              {apiState.status === "unavailable" && "Not connected"}
            </small>
          </span>
          <span
            className={
              apiState.status === "available"
                ? "service-dot service-dot--available"
                : "service-dot"
            }
            aria-hidden="true"
          />
        </div>
      </aside>

      <div className="application-frame">
        <header className="utility-bar">
          <div className="breadcrumb" aria-label="Breadcrumb">
            <span>Workspace</span>
            <span aria-hidden="true">/</span>
            <strong>
              <Icon name={activeIcon} size={15} />
              {activeLabel}
            </strong>
          </div>

          <div className="utility-status" aria-label="Runtime context">
            <span className="utility-status__item">
              <span className="utility-status__label">Scope</span>
              <strong>All projects</strong>
            </span>
            <span className="utility-status__divider" aria-hidden="true" />
            <span className="utility-status__item">
              <span className="utility-status__label">Environment</span>
              <strong>{environment}</strong>
            </span>
            <span className="utility-status__divider" aria-hidden="true" />
            <span
              className={
                apiState.status === "available"
                  ? "runtime-state runtime-state--success"
                  : apiState.status === "unavailable"
                    ? "runtime-state runtime-state--danger"
                    : "runtime-state"
              }
            >
              <span className="runtime-state__dot" aria-hidden="true" />
              {serviceLabel}
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
          <p className="eyebrow">Platform runtime</p>
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
          <span className="environment-badge__dot" aria-hidden="true" />
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
