import { useState } from "react";

import type { Workspace } from "../../modules/workspaces/types";
import { WorkspaceSwitcher } from "../../modules/workspaces/WorkspaceSwitcher";
import { useRole } from "../../shared/roles/useRole";
import { Icon } from "../../shared/ui/Icon";
import type { GlobalNavigation, NavigationGroup } from "../navigation";
import type { AppRoute } from "../router";
import type { ApiState, WorkspaceLoadState } from "../types";

interface AppSidebarProps {
  workspaces: Workspace[];
  activeWorkspaceId: string | null;
  workspaceLoadState: WorkspaceLoadState;
  workspaceLoadError: string;
  navigationGroups: readonly NavigationGroup[];
  activeGlobalNavigation: GlobalNavigation | null;
  apiState: ApiState;
  serviceLabel: string;
  onSelectWorkspace: (workspace: Workspace) => void;
  onManageWorkspaces: () => void;
  onNavigate: (route: AppRoute) => void;
}

export function AppSidebar({
  workspaces,
  activeWorkspaceId,
  workspaceLoadState,
  workspaceLoadError,
  navigationGroups,
  activeGlobalNavigation,
  apiState,
  serviceLabel,
  onSelectWorkspace,
  onManageWorkspaces,
  onNavigate,
}: AppSidebarProps) {
  const { capabilities } = useRole();
  const [collapsed, setCollapsed] = useState(() => {
    try {
      return globalThis.localStorage.getItem("tdp.sidebar-collapsed") === "true";
    } catch {
      return false;
    }
  });

  function toggleCollapsed(): void {
    setCollapsed((current) => {
      const next = !current;
      try {
        globalThis.localStorage.setItem("tdp.sidebar-collapsed", String(next));
      } catch {
        // Storage unavailable
      }
      return next;
    });
  }

  return (
    <aside className={collapsed ? "sidebar sidebar--collapsed" : "sidebar"} aria-label="Primary navigation">
      <div className="product-mark" aria-label="Technical Documentation Platform">
        <span className="product-mark__symbol" aria-hidden="true">
          <Icon name="documents" size={17} />
        </span>
        <span className="product-mark__copy">
          <strong>Technical Docs</strong>
          <small>Documentation platform</small>
        </span>
      </div>

      {!collapsed && (
        <WorkspaceSwitcher
          workspaces={workspaces}
          activeWorkspaceId={activeWorkspaceId}
          status={workspaceLoadState}
          errorMessage={workspaceLoadError}
          onSelect={onSelectWorkspace}
          onManage={onManageWorkspaces}
        />
      )}

      <nav className="primary-navigation">
        {navigationGroups.map((group) => {
          const visibleItems = group.items.filter((item) => {
            if (item.adminOnly && !capabilities.canViewAuditLogs) return false;
            return true;
          });

          if (visibleItems.length === 0) return null;

          return (
            <section
              className="navigation-group"
              aria-labelledby={`nav-${group.label.replaceAll(" ", "-")}`}
              key={group.label}
            >
              {!collapsed && (
                <h2 id={`nav-${group.label.replaceAll(" ", "-")}`}>{group.label}</h2>
              )}
              <ul className="navigation-list">
                {visibleItems.map((item) => (
                  <li key={item.id}>
                    <button
                      type="button"
                      className={
                        item.id === activeGlobalNavigation
                          ? "navigation-item is-active"
                          : "navigation-item"
                      }
                      aria-current={item.id === activeGlobalNavigation ? "page" : undefined}
                      onClick={() => onNavigate(item.route)}
                      title={collapsed ? item.label : undefined}
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
          );
        })}
      </nav>

      {!collapsed && (
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
      )}

      <button
        type="button"
        className="sidebar-collapse-toggle"
        onClick={toggleCollapsed}
        aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        aria-expanded={!collapsed}
        title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
      >
        <Icon name={collapsed ? "arrow-right" : "arrow-right"} size={14} />
      </button>
    </aside>
  );
}
