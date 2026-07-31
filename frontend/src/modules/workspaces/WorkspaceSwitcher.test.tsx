import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import type { Workspace } from "./types";
import { WorkspaceSwitcher } from "./WorkspaceSwitcher";

const generalWorkspace: Workspace = {
  id: "workspace-general",
  key: "GENERAL",
  name: "General Workspace",
  description: "Default workspace",
  status: "ACTIVE",
  created_at: "2026-07-31T00:00:00Z",
  updated_at: "2026-07-31T00:00:00Z",
};

const erpWorkspace: Workspace = {
  ...generalWorkspace,
  id: "workspace-erp",
  key: "ERP",
  name: "ERP Workspace",
};

const archivedWorkspace: Workspace = {
  ...generalWorkspace,
  id: "workspace-archived",
  key: "OLD",
  name: "Archived Workspace",
  status: "ARCHIVED",
};

function renderSwitcher(workspaces: Workspace[] = [generalWorkspace, erpWorkspace]) {
  const onSelect = vi.fn();
  const onManage = vi.fn();
  render(
    <WorkspaceSwitcher
      workspaces={workspaces}
      activeWorkspaceId={generalWorkspace.id}
      status="ready"
      onSelect={onSelect}
      onManage={onManage}
    />,
  );
  return { onSelect, onManage };
}

describe("WorkspaceSwitcher", () => {
  it("shows workspace identity separately and selects an active workspace", () => {
    const { onSelect } = renderSwitcher([
      generalWorkspace,
      erpWorkspace,
      archivedWorkspace,
    ]);

    fireEvent.click(
      screen.getByRole("button", {
        name: "Switch workspace. Current workspace: GENERAL — General Workspace",
      }),
    );

    expect(screen.getByRole("dialog", { name: "Switch workspace" })).toBeInTheDocument();
    expect(
      screen.getByRole("menuitemradio", {
        name: "GENERAL — General Workspace, current workspace",
      }),
    ).toHaveAttribute("aria-checked", "true");
    expect(
      screen.queryByRole("menuitemradio", { name: /Archived Workspace/ }),
    ).not.toBeInTheDocument();

    fireEvent.click(
      screen.getByRole("menuitemradio", { name: "ERP — ERP Workspace" }),
    );

    expect(onSelect).toHaveBeenCalledWith(erpWorkspace);
    expect(screen.queryByRole("dialog", { name: "Switch workspace" })).not.toBeInTheDocument();
  });

  it("supports Arrow keys and Escape while restoring trigger focus", () => {
    renderSwitcher();
    const trigger = screen.getByRole("button", {
      name: "Switch workspace. Current workspace: GENERAL — General Workspace",
    });

    fireEvent.keyDown(trigger, { key: "ArrowDown" });
    const currentOption = screen.getByRole("menuitemradio", {
      name: "GENERAL — General Workspace, current workspace",
    });
    const erpOption = screen.getByRole("menuitemradio", { name: "ERP — ERP Workspace" });
    expect(currentOption).toHaveFocus();

    fireEvent.keyDown(currentOption, { key: "ArrowDown" });
    expect(erpOption).toHaveFocus();
    fireEvent.keyDown(erpOption, { key: "Home" });
    expect(currentOption).toHaveFocus();
    fireEvent.keyDown(currentOption, { key: "End" });
    expect(erpOption).toHaveFocus();

    fireEvent.keyDown(erpOption, { key: "Escape" });
    expect(screen.queryByRole("dialog", { name: "Switch workspace" })).not.toBeInTheDocument();
    expect(trigger).toHaveFocus();
  });

  it("closes on outside click and exposes Workspace management inside the popover", () => {
    const { onManage } = renderSwitcher();
    const trigger = screen.getByRole("button", {
      name: "Switch workspace. Current workspace: GENERAL — General Workspace",
    });

    fireEvent.click(trigger);
    fireEvent.mouseDown(document.body);
    expect(screen.queryByRole("dialog", { name: "Switch workspace" })).not.toBeInTheDocument();

    fireEvent.click(trigger);
    fireEvent.click(screen.getByRole("button", { name: /Manage workspaces/ }));
    expect(onManage).toHaveBeenCalledTimes(1);
  });

  it("keeps Workspace management available when context loading fails", () => {
    const onManage = vi.fn();
    render(
      <WorkspaceSwitcher
        workspaces={[]}
        activeWorkspaceId={null}
        status="error"
        errorMessage="Workspace service is unavailable."
        onSelect={vi.fn()}
        onManage={onManage}
      />,
    );

    fireEvent.click(
      screen.getByRole("button", { name: "Switch workspace. Unavailable" }),
    );
    expect(screen.getByRole("status")).toHaveTextContent(
      "Workspace service is unavailable.",
    );
    fireEvent.click(screen.getByRole("button", { name: /Manage workspaces/ }));
    expect(onManage).toHaveBeenCalledTimes(1);
  });

  it("adds search when the active Workspace list becomes large", () => {
    const workspaces = Array.from({ length: 6 }, (_, index) => ({
      ...generalWorkspace,
      id: `workspace-${index}`,
      key: index === 4 ? "ERP" : `TEAM-${index}`,
      name: index === 4 ? "ERP Workspace" : `Team Workspace ${index}`,
    }));

    render(
      <WorkspaceSwitcher
        workspaces={workspaces}
        activeWorkspaceId={workspaces[0]?.id ?? null}
        status="ready"
        onSelect={vi.fn()}
        onManage={vi.fn()}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /Switch workspace/ }));
    fireEvent.change(screen.getByRole("searchbox", { name: "Find workspace" }), {
      target: { value: "ERP" },
    });

    expect(screen.getByRole("menuitemradio", { name: "ERP — ERP Workspace" })).toBeInTheDocument();
    expect(screen.queryByRole("menuitemradio", { name: /TEAM-1/ })).not.toBeInTheDocument();
  });
});
