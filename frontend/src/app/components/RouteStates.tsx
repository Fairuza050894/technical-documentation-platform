import { Icon } from "../../shared/ui/Icon";

interface WorkspaceContextErrorProps {
  message: string;
  onManage: () => void;
}

export function WorkspaceContextError({
  message,
  onManage,
}: WorkspaceContextErrorProps) {
  return (
    <section
      className="content-section project-workbench-state"
      aria-labelledby="workspace-context-error-title"
    >
      <span className="project-workbench-state__icon" aria-hidden="true">
        <Icon name="alert" size={22} />
      </span>
      <h1 id="workspace-context-error-title">Workspace context unavailable</h1>
      <p>{message}</p>
      <button type="button" className="button button--primary" onClick={onManage}>
        Manage workspaces
      </button>
    </section>
  );
}

interface RouteNotFoundProps {
  pathname: string;
  onGoHome: () => void;
}

export function RouteNotFound({ pathname, onGoHome }: RouteNotFoundProps) {
  return (
    <section
      className="content-section project-workbench-state"
      aria-labelledby="route-not-found-title"
    >
      <span className="project-workbench-state__icon" aria-hidden="true">
        <Icon name="alert" size={22} />
      </span>
      <h1 id="route-not-found-title">Page not found</h1>
      <p>
        No workspace route matches <code>{pathname}</code>.
      </p>
      <button type="button" className="button button--primary" onClick={onGoHome}>
        Return home
      </button>
    </section>
  );
}
