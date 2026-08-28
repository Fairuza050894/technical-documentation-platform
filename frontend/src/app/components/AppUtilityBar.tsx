import type { Project } from "../../modules/projects/types";
import type { Workspace } from "../../modules/workspaces/types";
import { GlobalSearch } from "../../shared/search/GlobalSearch";
import { Icon } from "../../shared/ui/Icon";
import type { PageContext } from "../navigation";
import type { AppRoute } from "../router";
import type { ApiState } from "../types";

interface AppUtilityBarProps {
  pageContext: PageContext;
  route: AppRoute;
  activeWorkspace: Workspace | null;
  activeProject: Project | null;
  environment: string;
  apiState: ApiState;
  serviceLabel: string;
  onNavigate: (route: AppRoute) => void;
}

export function AppUtilityBar({
  pageContext,
  route,
  activeWorkspace,
  activeProject,
  environment,
  apiState,
  serviceLabel,
  onNavigate,
}: AppUtilityBarProps) {
  return (
    <header className="utility-bar">
      <div className="breadcrumb" aria-label="Breadcrumb">
        {pageContext.breadcrumb.map((item, index) => (
          <span className="breadcrumb__segment" key={`${item}-${index}`}>
            {index > 0 && <span aria-hidden="true">/</span>}
            {index === pageContext.breadcrumb.length - 1 ? (
              <strong>
                <Icon name={pageContext.icon} size={15} />
                {item}
              </strong>
            ) : (
              <span>{item}</span>
            )}
          </span>
        ))}
      </div>

      <div className="utility-status" aria-label="Runtime context">
        <GlobalSearch route={route} onNavigate={onNavigate} />
        <span className="utility-status__divider" aria-hidden="true" />
        <span className="utility-status__item">
          <span className="utility-status__label">Scope</span>
          <strong>
            {route.name === "project"
              ? activeProject?.key ?? "Project"
              : activeWorkspace?.key ?? "No workspace"}
          </strong>
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
  );
}
