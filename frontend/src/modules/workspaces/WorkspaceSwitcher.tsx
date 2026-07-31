import {
  useCallback,
  useEffect,
  useId,
  useMemo,
  useRef,
  useState,
  type KeyboardEvent,
} from "react";

import { Icon } from "../../shared/ui/Icon";
import type { Workspace } from "./types";

export type WorkspaceSwitcherStatus = "loading" | "ready" | "error";

interface WorkspaceSwitcherProps {
  workspaces: Workspace[];
  activeWorkspaceId: string | null;
  status: WorkspaceSwitcherStatus;
  errorMessage?: string;
  onSelect: (workspace: Workspace) => void;
  onManage: () => void;
}

const SEARCH_THRESHOLD = 6;

export function WorkspaceSwitcher({
  workspaces,
  activeWorkspaceId,
  status,
  errorMessage = "Workspace context is unavailable.",
  onSelect,
  onManage,
}: WorkspaceSwitcherProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [focusedIndex, setFocusedIndex] = useState(-1);
  const rootRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const optionRefs = useRef<Array<HTMLButtonElement | null>>([]);
  const popoverId = useId();

  const activeWorkspace = useMemo(
    () => workspaces.find((workspace) => workspace.id === activeWorkspaceId) ?? null,
    [activeWorkspaceId, workspaces],
  );
  const selectableWorkspaces = useMemo(
    () => workspaces.filter((workspace) => workspace.status === "ACTIVE"),
    [workspaces],
  );
  const filteredWorkspaces = useMemo(() => {
    const normalizedQuery = query.trim().toLocaleLowerCase();
    if (normalizedQuery.length === 0) {
      return selectableWorkspaces;
    }
    return selectableWorkspaces.filter((workspace) =>
      `${workspace.key} ${workspace.name}`.toLocaleLowerCase().includes(normalizedQuery),
    );
  }, [query, selectableWorkspaces]);
  const showSearch = selectableWorkspaces.length >= SEARCH_THRESHOLD;

  const closeMenu = useCallback((restoreFocus = false): void => {
    setIsOpen(false);
    setQuery("");
    setFocusedIndex(-1);
    if (restoreFocus) {
      triggerRef.current?.focus();
    }
  }, []);

  const openMenu = useCallback(
    (preferredPosition: "current" | "first" | "last" = "current"): void => {
      if (status === "loading") {
        return;
      }
      let nextIndex = 0;
      if (preferredPosition === "last") {
        nextIndex = Math.max(selectableWorkspaces.length - 1, 0);
      } else if (preferredPosition === "current") {
        const currentIndex = selectableWorkspaces.findIndex(
          (workspace) => workspace.id === activeWorkspaceId,
        );
        nextIndex = currentIndex >= 0 ? currentIndex : 0;
      }
      setIsOpen(true);
      setFocusedIndex(selectableWorkspaces.length === 0 ? -1 : nextIndex);
    },
    [activeWorkspaceId, selectableWorkspaces, status],
  );

  useEffect(() => {
    if (!isOpen) {
      return undefined;
    }

    const handleOutsideClick = (event: MouseEvent): void => {
      if (event.target instanceof Node && !rootRef.current?.contains(event.target)) {
        closeMenu();
      }
    };

    document.addEventListener("mousedown", handleOutsideClick);
    return () => document.removeEventListener("mousedown", handleOutsideClick);
  }, [closeMenu, isOpen]);

  useEffect(() => {
    if (isOpen && focusedIndex >= 0) {
      optionRefs.current[focusedIndex]?.focus();
    }
  }, [focusedIndex, isOpen]);

  function handleRootKeyDown(event: KeyboardEvent<HTMLDivElement>): void {
    if (event.key === "Escape" && isOpen) {
      event.preventDefault();
      event.stopPropagation();
      closeMenu(true);
    }
  }

  function handleTriggerKeyDown(event: KeyboardEvent<HTMLButtonElement>): void {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      openMenu("current");
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      openMenu("last");
    }
  }

  function handleOptionKeyDown(event: KeyboardEvent<HTMLButtonElement>, index: number): void {
    if (filteredWorkspaces.length === 0) {
      return;
    }

    let nextIndex: number | null = null;
    if (event.key === "ArrowDown") {
      nextIndex = (index + 1) % filteredWorkspaces.length;
    } else if (event.key === "ArrowUp") {
      nextIndex = (index - 1 + filteredWorkspaces.length) % filteredWorkspaces.length;
    } else if (event.key === "Home") {
      nextIndex = 0;
    } else if (event.key === "End") {
      nextIndex = filteredWorkspaces.length - 1;
    }

    if (nextIndex !== null) {
      event.preventDefault();
      setFocusedIndex(nextIndex);
    }
  }

  function select(workspace: Workspace): void {
    closeMenu(true);
    if (workspace.id !== activeWorkspaceId) {
      onSelect(workspace);
    }
  }

  const triggerLabel = resolveTriggerLabel(status, activeWorkspace);
  const triggerName =
    activeWorkspace === null
      ? `Switch workspace. ${triggerLabel}`
      : `Switch workspace. Current workspace: ${activeWorkspace.key} — ${activeWorkspace.name}`;

  return (
    <div
      className="workspace-switcher"
      ref={rootRef}
      onKeyDown={handleRootKeyDown}
    >
      <button
        type="button"
        className={
          isOpen
            ? "workspace-context workspace-switcher__trigger is-open"
            : "workspace-context workspace-switcher__trigger"
        }
        ref={triggerRef}
        aria-controls={isOpen ? popoverId : undefined}
        aria-expanded={isOpen}
        aria-haspopup="dialog"
        aria-label={triggerName}
        disabled={status === "loading"}
        onClick={() => (isOpen ? closeMenu() : openMenu())}
        onKeyDown={handleTriggerKeyDown}
      >
        <span className="workspace-context__icon" aria-hidden="true">
          <Icon name="folder" size={16} />
        </span>
        <span className="workspace-switcher__identity">
          <small>Workspace</small>
          <strong>{activeWorkspace?.key ?? triggerLabel}</strong>
          <span title={activeWorkspace?.name}>{activeWorkspace?.name ?? statusDetail(status)}</span>
        </span>
        <Icon
          className="workspace-context__chevron"
          name="chevron-down"
          size={14}
        />
      </button>

      {isOpen && (
        <div
          className="workspace-switcher__popover"
          id={popoverId}
          role="dialog"
          aria-label="Switch workspace"
        >
          <div className="workspace-switcher__header">
            <div>
              <strong>Switch workspace</strong>
              <span>{selectableWorkspaces.length} available</span>
            </div>
            <span className="workspace-switcher__shortcut" aria-hidden="true">Esc</span>
          </div>

          {showSearch && (
            <div className="workspace-switcher__search">
              <label htmlFor={`${popoverId}-search`}>Find workspace</label>
              <input
                id={`${popoverId}-search`}
                type="search"
                value={query}
                placeholder="Search key or name"
                autoComplete="off"
                onChange={(event) => {
                  setQuery(event.target.value);
                  setFocusedIndex(-1);
                }}
                onKeyDown={(event) => {
                  if (event.key === "ArrowDown" && filteredWorkspaces.length > 0) {
                    event.preventDefault();
                    setFocusedIndex(0);
                  }
                }}
              />
            </div>
          )}

          <div
            className="workspace-switcher__options"
            role="menu"
            aria-label="Available workspaces"
          >
            {filteredWorkspaces.map((workspace, index) => {
              const isCurrent = workspace.id === activeWorkspaceId;
              return (
                <button
                  type="button"
                  className={
                    isCurrent
                      ? "workspace-switcher__option is-current"
                      : "workspace-switcher__option"
                  }
                  key={workspace.id}
                  ref={(element) => {
                    optionRefs.current[index] = element;
                  }}
                  role="menuitemradio"
                  aria-checked={isCurrent}
                  aria-label={`${workspace.key} — ${workspace.name}${
                    isCurrent ? ", current workspace" : ""
                  }`}
                  onClick={() => select(workspace)}
                  onKeyDown={(event) => handleOptionKeyDown(event, index)}
                >
                  <span className="workspace-switcher__option-mark" aria-hidden="true">
                    {isCurrent && <Icon name="check" size={15} />}
                  </span>
                  <span className="workspace-switcher__option-copy">
                    <strong>{workspace.key}</strong>
                    <span title={workspace.name}>{workspace.name}</span>
                  </span>
                  {isCurrent && <span className="workspace-switcher__current">Current</span>}
                </button>
              );
            })}

            {filteredWorkspaces.length === 0 && (
              <div className="workspace-switcher__empty">
                <strong>No workspace found</strong>
                <span>Try another key or workspace name.</span>
              </div>
            )}
          </div>

          {status === "error" && (
            <p className="workspace-switcher__error" role="status">{errorMessage}</p>
          )}

          <button
            type="button"
            className="workspace-switcher__manage"
            onClick={() => {
              closeMenu();
              onManage();
            }}
          >
            <Icon name="settings" size={15} />
            <span>
              <strong>Manage workspaces</strong>
              <small>Create, archive, and review boundaries</small>
            </span>
            <Icon name="arrow-right" size={14} />
          </button>
        </div>
      )}
    </div>
  );
}

function resolveTriggerLabel(
  status: WorkspaceSwitcherStatus,
  activeWorkspace: Workspace | null,
): string {
  if (activeWorkspace !== null) {
    return activeWorkspace.key;
  }
  if (status === "loading") {
    return "Loading";
  }
  if (status === "error") {
    return "Unavailable";
  }
  return "Not selected";
}

function statusDetail(status: WorkspaceSwitcherStatus): string {
  if (status === "loading") {
    return "Loading workspace context";
  }
  if (status === "error") {
    return "Open Workspace management to recover";
  }
  return "Choose an operational boundary";
}
