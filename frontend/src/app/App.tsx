import { useEffect, useState } from "react";

import { ProjectWorkspace } from "../modules/projects/ProjectWorkspace";

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

const navigationItems = [
  "Overview",
  "Projects",
  "Sources",
  "API Catalog",
  "Changes",
  "Documents",
  "Sync History",
] as const;

type NavigationItem = (typeof navigationItems)[number];

export function App() {
  const [apiState, setApiState] = useState<ApiState>({ status: "loading" });
  const [activeNavigation, setActiveNavigation] = useState<NavigationItem>("Projects");

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

  return (
    <div className="app-shell">
      <aside className="sidebar" aria-label="Primary navigation">
        <div className="product-mark" aria-label="Technical Documentation Platform">
          <span className="product-mark__symbol">TD</span>
          <span>
            <strong>Documentation</strong>
            <small>Technical platform</small>
          </span>
        </div>

        <nav>
          <ul className="navigation-list">
            {navigationItems.map((item) => (
              <li key={item}>
                <button
                  type="button"
                  className={
                    item === activeNavigation ? "navigation-item is-active" : "navigation-item"
                  }
                  aria-current={item === activeNavigation ? "page" : undefined}
                  onClick={() => setActiveNavigation(item)}
                >
                  {item}
                </button>
              </li>
            ))}
          </ul>
        </nav>
      </aside>

      <main className="main-content">
        {activeNavigation === "Projects" ? (
          <ProjectWorkspace />
        ) : (
          <Overview apiState={apiState} activeNavigation={activeNavigation} />
        )}
      </main>
    </div>
  );
}

function Overview({
  apiState,
  activeNavigation,
}: {
  apiState: ApiState;
  activeNavigation: NavigationItem;
}) {
  return (
    <>
      <header className="topbar">
        <div>
          <p className="eyebrow">Engineering foundation</p>
          <h1>{activeNavigation === "Overview" ? "Workspace overview" : activeNavigation}</h1>
        </div>
        <span className="environment-badge">Local development</span>
      </header>

      {activeNavigation === "Overview" ? (
        <>
          <section className="content-section" aria-labelledby="foundation-title">
            <div className="section-heading">
              <div>
                <h2 id="foundation-title">Foundation status</h2>
                <p>The application shell reports real local service status without demo metrics.</p>
              </div>
            </div>

            <div className="status-grid">
              <article className="status-card">
                <span className="status-label">Frontend</span>
                <strong>Application shell ready</strong>
                <p>React, TypeScript, design tokens, linting, tests, and production build.</p>
                <span className="status-indicator status-indicator--success">Configured</span>
              </article>

              <article className="status-card">
                <span className="status-label">Backend API</span>
                <strong>
                  {apiState.status === "loading" && "Checking local service"}
                  {apiState.status === "available" && apiState.health.service}
                  {apiState.status === "unavailable" && "Service is not running"}
                </strong>
                <p>
                  {apiState.status === "available"
                    ? `Version ${apiState.health.version} · ${apiState.health.environment}`
                    : "Start the backend with make dev-backend."}
                </p>
                <span
                  className={
                    apiState.status === "available"
                      ? "status-indicator status-indicator--success"
                      : "status-indicator status-indicator--neutral"
                  }
                >
                  {apiState.status === "loading" && "Checking"}
                  {apiState.status === "available" && "Available"}
                  {apiState.status === "unavailable" && "Offline"}
                </span>
              </article>

              <article className="status-card">
                <span className="status-label">Current vertical slice</span>
                <strong>Project management</strong>
                <p>Create, list, and archive source and documentation project boundaries.</p>
                <span className="status-indicator status-indicator--success">Implemented</span>
              </article>
            </div>
          </section>

          <section className="content-section" aria-labelledby="principles-title">
            <div className="section-heading">
              <div>
                <h2 id="principles-title">Product constraints</h2>
                <p>These constraints guide every implementation decision.</p>
              </div>
            </div>
            <dl className="constraint-list">
              <div>
                <dt>Source-backed facts</dt>
                <dd>Every generated fact must keep a verifiable source reference.</dd>
              </div>
              <div>
                <dt>Deterministic pipeline</dt>
                <dd>Parsing, normalization, change detection, and rendering do not depend on AI.</dd>
              </div>
              <div>
                <dt>Explicit uncertainty</dt>
                <dd>Missing or conflicting information is shown, never silently invented.</dd>
              </div>
            </dl>
          </section>
        </>
      ) : (
        <section className="content-section" aria-labelledby="planned-feature-title">
          <div className="empty-state">
            <h2 id="planned-feature-title">Planned module</h2>
            <p>This module will be implemented in a dedicated vertical slice.</p>
          </div>
        </section>
      )}
    </>
  );
}
