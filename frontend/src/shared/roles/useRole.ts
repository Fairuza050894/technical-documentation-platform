import { useMemo } from "react";

import { useAuth } from "../auth/AuthContext";

export type Role = "admin" | "editor" | "viewer";

interface RoleCapabilities {
  canViewAuditLogs: boolean;
  canManageWorkspaces: boolean;
  canManageProjects: boolean;
  canEditDocuments: boolean;
  canManageSources: boolean;
  canViewSystemStatus: boolean;
  canExportData: boolean;
  canManageMembers: boolean;
}

const ROLE_CAPABILITIES: Record<Role, RoleCapabilities> = {
  admin: {
    canViewAuditLogs: true,
    canManageWorkspaces: true,
    canManageProjects: true,
    canEditDocuments: true,
    canManageSources: true,
    canViewSystemStatus: true,
    canExportData: true,
    canManageMembers: true,
  },
  editor: {
    canViewAuditLogs: false,
    canManageWorkspaces: false,
    canManageProjects: true,
    canEditDocuments: true,
    canManageSources: true,
    canViewSystemStatus: true,
    canExportData: true,
    canManageMembers: false,
  },
  viewer: {
    canViewAuditLogs: false,
    canManageWorkspaces: false,
    canManageProjects: false,
    canEditDocuments: false,
    canManageSources: false,
    canViewSystemStatus: true,
    canExportData: false,
    canManageMembers: false,
  },
};

export function useRole(): {
  role: Role;
  capabilities: RoleCapabilities;
  isAdmin: boolean;
  isEditor: boolean;
  isViewer: boolean;
} {
  const { session } = useAuth();

  const role: Role = useMemo(() => {
    const rawRole = session?.role ?? "viewer";
    if (rawRole === "admin" || rawRole === "editor") return rawRole;
    return "viewer";
  }, [session?.role]);

  const capabilities = ROLE_CAPABILITIES[role];

  return {
    role,
    capabilities,
    isAdmin: role === "admin",
    isEditor: role === "editor",
    isViewer: role === "viewer",
  };
}