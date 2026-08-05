import type { ApiState } from "../types";

interface SystemStatusProps {
  apiState: ApiState;
}

export function SystemStatus({ apiState }: SystemStatusProps) {
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
            <dd>{apiState.status === "available" ? apiState.health.environment : "Local"}</dd>
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
