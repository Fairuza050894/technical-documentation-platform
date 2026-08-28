import { useCallback, useEffect, useRef, useState } from "react";

import type { AppRoute } from "../../app/router";
import { Icon } from "../ui/Icon";
import { executeGlobalSearch } from "./searchEngine";
import type { SearchResult, SearchResultGroup } from "./types";

interface GlobalSearchProps {
  route: AppRoute;
  onNavigate: (route: AppRoute) => void;
}

export function GlobalSearch({ route, onNavigate }: GlobalSearchProps) {
  const [query, setQuery] = useState("");
  const [groups, setGroups] = useState<SearchResultGroup[]>([]);
  const [total, setTotal] = useState(0);
  const [isOpen, setIsOpen] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  const [highlightedIndex, setHighlightedIndex] = useState(-1);

  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout>>(null);

  const flatResults = groups.flatMap((group) => group.items);

  const workspaceId =
    route.name === "project" || route.name === "home" || route.name === "projects"
      ? route.workspaceId
      : null;

  const search = useCallback(
    (searchQuery: string) => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }

      if (searchQuery.trim().length < 2) {
        setGroups([]);
        setTotal(0);
        setIsSearching(false);
        return;
      }

      setIsSearching(true);
      debounceRef.current = setTimeout(() => {
        const controller = new AbortController();
        void executeGlobalSearch(searchQuery, workspaceId, controller.signal)
          .then((response) => {
            setGroups(response.groups);
            setTotal(response.total);
            setHighlightedIndex(-1);
          })
          .catch(() => {
            setGroups([]);
            setTotal(0);
          })
          .finally(() => {
            setIsSearching(false);
          });
      }, 300);
    },
    [workspaceId],
  );

  useEffect(() => {
    search(query);
    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, [query, search]);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent): void {
      if (
        containerRef.current &&
        !containerRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
        if (!query) setIsExpanded(false);
      }
    }

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [query]);

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent): void {
      if ((event.metaKey || event.ctrlKey) && event.key === "k") {
        event.preventDefault();
        setIsExpanded(true);
        setIsOpen(true);
        requestAnimationFrame(() => inputRef.current?.focus());
      }
    }

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, []);

  function handleExpand(): void {
    setIsExpanded(true);
    setIsOpen(true);
    requestAnimationFrame(() => inputRef.current?.focus());
  }

  function handleCollapse(): void {
    if (!query) {
      setIsExpanded(false);
      setIsOpen(false);
    }
  }

  function handleKeyDown(event: React.KeyboardEvent<HTMLInputElement>): void {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setHighlightedIndex((prev) =>
        prev < flatResults.length - 1 ? prev + 1 : 0,
      );
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setHighlightedIndex((prev) =>
        prev > 0 ? prev - 1 : flatResults.length - 1,
      );
    } else if (event.key === "Enter" && highlightedIndex >= 0) {
      event.preventDefault();
      const selected = flatResults[highlightedIndex];
      if (selected) selectResult(selected);
    } else if (event.key === "Escape") {
      setQuery("");
      setIsOpen(false);
      setIsExpanded(false);
      inputRef.current?.blur();
    }
  }

  function selectResult(result: SearchResult): void {
    onNavigate({
      name: "project",
      workspaceId,
      projectId: result.projectId,
      stage: result.route.stage as "overview",
      ...(result.route.featureId ? { featureId: result.route.featureId } : {}),
    });
    setQuery("");
    setIsOpen(false);
    setIsExpanded(false);
  }

  return (
    <div
      className={isExpanded ? "global-search global-search--expanded" : "global-search"}
      ref={containerRef}
    >
      {!isExpanded ? (
        <button
          type="button"
          className="global-search__trigger"
          onClick={handleExpand}
          aria-label="Search"
        >
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#5e6c82" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="11" cy="11" r="7" />
            <line x1="16.5" y1="16.5" x2="21" y2="21" />
          </svg>
        </button>
      ) : (
        <div className="global-search__field">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#5e6c82" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <circle cx="11" cy="11" r="7" />
            <line x1="16.5" y1="16.5" x2="21" y2="21" />
          </svg>
          <input
            ref={inputRef}
            type="search"
            className="global-search__input"
            placeholder="Search..."
            value={query}
            onChange={(event) => {
              setQuery(event.target.value);
              setIsOpen(true);
            }}
            onKeyDown={handleKeyDown}
            onBlur={handleCollapse}
            aria-label="Search across all modules"
            aria-expanded={isOpen && total > 0}
            aria-controls="global-search-results"
            role="combobox"
            aria-autocomplete="list"
          />
          {query && (
            <button
              type="button"
              className="global-search__clear"
              onClick={() => {
                setQuery("");
                inputRef.current?.focus();
              }}
              aria-label="Clear search"
            >
              &times;
            </button>
          )}
        </div>
      )}

      {isOpen && query.trim().length >= 2 && (
        <div
          className="global-search__results"
          id="global-search-results"
          role="listbox"
          aria-label="Search results"
        >
          {isSearching && (
            <p className="global-search__status" role="status">
              Searching...
            </p>
          )}

          {!isSearching && total === 0 && (
            <p className="global-search__status">
              No results for &ldquo;{query}&rdquo;
            </p>
          )}

          {!isSearching &&
            groups.map((group) => (
              <div key={group.kind} className="global-search__group">
                <div className="global-search__group-label">{group.label}</div>
                {group.items.map((item) => {
                  const index = flatResults.indexOf(item);
                  return (
                    <button
                      key={item.id}
                      type="button"
                      className={
                        index === highlightedIndex
                          ? "global-search__result global-search__result--highlighted"
                          : "global-search__result"
                      }
                      role="option"
                      aria-selected={index === highlightedIndex}
                      onClick={() => selectResult(item)}
                      onMouseEnter={() => setHighlightedIndex(index)}
                    >
                      <SearchKindIcon kind={item.kind} />
                      <span className="global-search__result-content">
                        <strong>{item.title}</strong>
                        <small>{item.subtitle}</small>
                      </span>
                    </button>
                  );
                })}
              </div>
            ))}

          {!isSearching && total > 0 && (
            <p className="global-search__footer">
              {total} result{total === 1 ? "" : "s"}
            </p>
          )}
        </div>
      )}
    </div>
  );
}

function SearchKindIcon({ kind }: { kind: SearchResultGroup["kind"] }) {
  const iconMap: Record<SearchResultGroup["kind"], "source" | "documents" | "projects"> = {
    source: "source",
    document: "documents",
    evidence: "documents",
    claim: "documents",
    feature: "projects",
  };
  return (
    <span className="global-search__result-kind">
      <Icon name={iconMap[kind]} size={13} />
    </span>
  );
}
