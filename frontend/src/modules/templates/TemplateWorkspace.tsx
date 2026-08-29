import { useCallback, useEffect, useRef, useState } from "react";

import { getTemplate, listTemplates, createTemplate, updateTemplate, deleteTemplate, duplicateTemplate } from "./api";
import type {
  CreateTemplateInput,
  TemplateCategory,
  TemplateDetail,
  TemplateSummary,
  UpdateTemplateInput,
} from "./types";
import { CATEGORY_LABELS, CATEGORY_ORDER } from "./types";
import { MarkdownPreview } from "../../shared/ui/MarkdownPreview";

type ViewMode = "grid" | "list";

const CATEGORY_ICONS: Record<TemplateCategory | "ALL", string> = {
  ALL: "\u229e",
  REQUIREMENTS: "\ud83d\udccb",
  ARCHITECTURE: "\ud83c\udfd7\ufe0f",
  TESTING: "\ud83e\uddea",
  OPERATIONS: "\u2699\ufe0f",
  USER_FACING: "\ud83d\udc64",
  GOVERNANCE: "\ud83d\udee1\ufe0f",
};

const CATEGORY_COLORS: Record<TemplateCategory, string> = {
  REQUIREMENTS: "#3b82f6",
  ARCHITECTURE: "#8b5cf6",
  TESTING: "#f59e0b",
  OPERATIONS: "#10b981",
  USER_FACING: "#ec4899",
  GOVERNANCE: "#6366f1",
};

interface TemplateWorkspaceProps {
  embedded?: boolean;
}

export function TemplateWorkspace({ embedded = false }: TemplateWorkspaceProps) {
  const [templates, setTemplates] = useState<TemplateSummary[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<TemplateDetail | null>(null);
  const [activeCategory, setActiveCategory] = useState<TemplateCategory | "ALL">("ALL");
  const [filter, setFilter] = useState("");
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [isBusy, setIsBusy] = useState(false);
  const [editContent, setEditContent] = useState("");
  const [isEditing, setIsEditing] = useState(false);
  const [viewMode, setViewMode] = useState<ViewMode>("grid");
  const [currentPage, setCurrentPage] = useState(1);
  const PAGE_SIZE = 10;
  const [toast, setToast] = useState<{ message: string; isError: boolean } | null>(null);
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);
  const editorRef = useRef<HTMLTextAreaElement>(null);

  const [formKey, setFormKey] = useState("");
  const [formName, setFormName] = useState("");
  const [formDescription, setFormDescription] = useState("");
  const [formCategory, setFormCategory] = useState<TemplateCategory>("REQUIREMENTS");
  const [formStandard, setFormStandard] = useState("Custom");
  const [formContent, setFormContent] = useState("");

  const load = useCallback(async (signal?: AbortSignal) => {
    try {
      const collection = await listTemplates(undefined, undefined, signal);
      setTemplates(collection.items);
    } catch (error: unknown) {
      if (error instanceof DOMException && error.name === "AbortError") return;
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    void load(controller.signal);
    return () => controller.abort();
  }, [load]);

  const filteredTemplates = (() => {
    let items = templates;
    if (activeCategory !== "ALL") {
      items = items.filter((t) => t.category === activeCategory);
    }
    if (filter.trim()) {
      const query = filter.trim().toLowerCase();
      items = items.filter(
        (t) =>
          t.name.toLowerCase().includes(query) ||
          t.key.toLowerCase().includes(query) ||
          t.description.toLowerCase().includes(query) ||
          t.standard.toLowerCase().includes(query),
      );
    }
    return items;
  })();

  const totalPages = Math.max(1, Math.ceil(filteredTemplates.length / PAGE_SIZE));
  const paginatedTemplates = filteredTemplates.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE);

  const categoryCounts = (() => {
    const counts: Record<string, number> = { ALL: templates.length };
    for (const item of templates) {
      counts[item.category] = (counts[item.category] || 0) + 1;
    }
    return counts;
  })();

  function showToast(msg: string, isError = false): void {
    setToast({ message: msg, isError });
    setTimeout(() => setToast(null), 3000);
  }

  function insertMarkdown(before: string, after: string): void {
    const textarea = editorRef.current;
    if (!textarea) return;
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const selected = editContent.substring(start, end);
    const replacement = before + selected + after;
    const newContent = editContent.substring(0, start) + replacement + editContent.substring(end);
    setEditContent(newContent);
    setTimeout(() => {
      textarea.focus();
      const cursorPos = start + before.length + selected.length;
      textarea.setSelectionRange(cursorPos, cursorPos);
    }, 0);
  }

  function resetForm(): void {
    setFormKey("");
    setFormName("");
    setFormDescription("");
    setFormCategory("REQUIREMENTS");
    setFormStandard("Custom");
    setFormContent("");
  }

  async function handleSelectTemplate(templateId: string): Promise<void> {
    try {
      const detail = await getTemplate(templateId);
      setSelectedTemplate(detail);
      setEditContent(detail.content);
      setIsEditing(false);
    } catch (error: unknown) {
      showToast(error instanceof Error ? error.message : "Template could not be loaded.", true);
    }
  }

  async function handleSave(): Promise<void> {
    if (!selectedTemplate || isBusy) return;
    if (selectedTemplate.is_builtin) {
      showToast("Cannot edit built-in templates. Please customize first.", true);
      return;
    }
    setIsBusy(true);
    try {
      const input: UpdateTemplateInput = { content: editContent };
      const updated = await updateTemplate(selectedTemplate.id, input);
      setSelectedTemplate(updated);
      setEditContent(updated.content);
      setIsEditing(false);
      await load();
      showToast("Template saved as v" + updated.version);
    } catch (error: unknown) {
      showToast(error instanceof Error ? error.message : "Save failed.", true);
    } finally {
      setIsBusy(false);
    }
  }

  async function handleDuplicate(templateId: string, name: string): Promise<void> {
    if (isBusy) return;
    setIsBusy(true);
    try {
      const sourceTemplate = await getTemplate(templateId);
      const defaultKey = sourceTemplate.key + "_CUSTOM";
      const newKey = prompt(`Enter key for your custom "${name}":`, defaultKey);
      if (!newKey) { setIsBusy(false); return; }
      const copy = await duplicateTemplate(templateId, newKey);
      await load();
      setSelectedTemplate(copy);
      setEditContent(copy.content);
      setIsEditing(true);
      showToast("Custom template " + copy.key + " created. You can now edit it.");
    } catch (error: unknown) {
      showToast(error instanceof Error ? error.message : "Duplication failed.", true);
    } finally {
      setIsBusy(false);
    }
  }

  function handleDeleteClick(templateId: string): void {
    setConfirmDeleteId(templateId);
  }

  async function executeDelete(templateId: string): Promise<void> {
    setConfirmDeleteId(null);
    setIsBusy(true);
    try {
      await deleteTemplate(templateId);
      setSelectedTemplate((prev) => (prev?.id === templateId ? null : prev));
      setIsEditing(false);
      await load();
      showToast("Template deleted");
    } catch (error: unknown) {
      showToast(error instanceof Error ? error.message : "Delete failed.", true);
    } finally {
      setIsBusy(false);
    }
  }

  async function handleCreate(): Promise<void> {
    if (isBusy) return;
    setIsBusy(true);
    try {
      const input: CreateTemplateInput = {
        key: formKey, name: formName, description: formDescription,
        category: formCategory, standard: formStandard, content: formContent,
      };
      const created = await createTemplate(input);
      await load();
      setShowCreateForm(false);
      resetForm();
      showToast("Template " + created.key + " created");
    } catch (error: unknown) {
      showToast(error instanceof Error ? error.message : "Creation failed.", true);
    } finally {
      setIsBusy(false);
    }
  }

  return (
    <div className="template-workspace">
      {!embedded && (
        <header className="topbar">
          <div>
            <p className="eyebrow">Document templates</p>
            <h1>Templates</h1>
          </div>
          <span className="environment-badge">{templates.length} templates</span>
        </header>
      )}

      <div className="template-layout">
        <aside className="template-sidebar" aria-label="Template categories">
          <div className="template-sidebar__header">
            <span>Categories</span>
          </div>
          <button
            type="button"
            className={activeCategory === "ALL" ? "template-cat-btn template-cat-btn--active" : "template-cat-btn"}
            onClick={() => { setActiveCategory("ALL"); setCurrentPage(1); }}
          >
            <span className="template-cat-btn__icon">{CATEGORY_ICONS.ALL}</span>
            <span className="template-cat-btn__label">All Templates</span>
            <span className="template-cat-btn__count">{categoryCounts.ALL || 0}</span>
          </button>
          {CATEGORY_ORDER.map((cat) => (
            <button
              key={cat}
              type="button"
              className={activeCategory === cat ? "template-cat-btn template-cat-btn--active" : "template-cat-btn"}
              onClick={() => { setActiveCategory(cat); setCurrentPage(1); }}
              style={activeCategory === cat ? { "--cat-color": CATEGORY_COLORS[cat] } as React.CSSProperties : undefined}
            >
              <span className="template-cat-btn__icon">{CATEGORY_ICONS[cat]}</span>
              <span className="template-cat-btn__label">{CATEGORY_LABELS[cat]}</span>
              <span className="template-cat-btn__count">{categoryCounts[cat] || 0}</span>
            </button>
          ))}
        </aside>

        <div className="template-main">
          <div className="template-toolbar">
            <div className="list-filter">
              <input
                type="search"
                placeholder="Search templates..."
                value={filter}
                onChange={(event) => { setFilter(event.target.value); setCurrentPage(1); }}
                aria-label="Search templates"
                className="template-search-input"
              />
              {filter && (
                <span className="record-count">{filteredTemplates.length} of {templates.length}</span>
              )}
            </div>
            <div className="template-toolbar__actions">
              <div className="template-view-toggle">
                <button
                  type="button"
                  className={viewMode === "grid" ? "template-view-btn template-view-btn--active" : "template-view-btn"}
                  onClick={() => setViewMode("grid")}
                  aria-label="Grid view"
                  title="Grid view"
                >
                  {"\u229e"}
                </button>
                <button
                  type="button"
                  className={viewMode === "list" ? "template-view-btn template-view-btn--active" : "template-view-btn"}
                  onClick={() => setViewMode("list")}
                  aria-label="List view"
                  title="List view"
                >
                  {"\u2630"}
                </button>
              </div>
              <button
                type="button"
                className="button button--primary"
                onClick={() => setShowCreateForm(!showCreateForm)}
              >
                {showCreateForm ? "Cancel" : "+ Create template"}
              </button>
            </div>
          </div>

          {showCreateForm && (
            <div className="form-panel template-create-form">
              <h3>Create custom template</h3>
              <div className="form-grid">
                <div className="field">
                  <label htmlFor="tpl-key">Template key</label>
                  <input id="tpl-key" required minLength={2} maxLength={50} value={formKey} onChange={(e) => setFormKey(e.target.value.toUpperCase())} placeholder="MY_TEMPLATE" />
                </div>
                <div className="field">
                  <label htmlFor="tpl-name">Name</label>
                  <input id="tpl-name" required maxLength={200} value={formName} onChange={(e) => setFormName(e.target.value)} placeholder="My Custom Template" />
                </div>
                <div className="field">
                  <label htmlFor="tpl-category">Category</label>
                  <select id="tpl-category" value={formCategory} onChange={(e) => setFormCategory(e.target.value as TemplateCategory)}>
                    {CATEGORY_ORDER.map((cat) => (
                      <option key={cat} value={cat}>{CATEGORY_LABELS[cat]}</option>
                    ))}
                  </select>
                </div>
                <div className="field">
                  <label htmlFor="tpl-standard">Standard</label>
                  <input id="tpl-standard" value={formStandard} onChange={(e) => setFormStandard(e.target.value)} placeholder="Custom" />
                </div>
                <div className="field field--wide">
                  <label htmlFor="tpl-description">Description</label>
                  <textarea id="tpl-description" maxLength={1000} value={formDescription} onChange={(e) => setFormDescription(e.target.value)} placeholder="Describe the purpose of this template." />
                </div>
                <div className="field field--wide">
                  <label htmlFor="tpl-content">Template content (Markdown)</label>
                  <textarea id="tpl-content" className="template-content-editor" rows={15} value={formContent} onChange={(e) => setFormContent(e.target.value)} placeholder="# Template Title" />
                </div>
              </div>
              <div className="form-actions">
                <button type="button" className="button button--primary" disabled={isBusy} onClick={() => void handleCreate()}>
                  {isBusy ? "Creating..." : "Create template"}
                </button>
              </div>
            </div>
          )}

          {filteredTemplates.length === 0 ? (
            <div className="template-empty-state">
              <span className="template-empty-state__icon">{"\ud83d\udcc4"}</span>
              <h3>No templates found</h3>
              <p>{filter ? "Try a different search term." : "Create a custom template to get started."}</p>
            </div>
          ) : viewMode === "grid" ? (
            <div className="template-grid">
              {paginatedTemplates.map((template) => (
                <div
                  key={template.id}
                  className={"template-card" + (selectedTemplate?.id === template.id ? " template-card--selected" : "")}
                  onClick={() => void handleSelectTemplate(template.id)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => { if (e.key === "Enter") void handleSelectTemplate(template.id); }}
                  style={{ "--card-accent": CATEGORY_COLORS[template.category] } as React.CSSProperties}
                >
                  <div className="template-card__accent" />
                  <div className="template-card__body">
                    <div className="template-card__header">
                      <span className="template-card__cat-icon">{CATEGORY_ICONS[template.category] || "\ud83d\udcc4"}</span>
                      <span className="template-card__key">{template.key}</span>
                      {template.is_builtin
                        ? <span className="template-card__badge">Built-in</span>
                        : <span className="template-card__badge template-card__badge--custom">Custom</span>
                      }
                    </div>
                    <strong className="template-card__name">{template.name}</strong>
                    <p className="template-card__description">{template.description || "No description"}</p>
                    <div className="template-card__footer">
                      <div className="template-card__meta">
                        <span className="template-card__meta-item">
                          <span className="template-card__meta-dot" style={{ background: CATEGORY_COLORS[template.category] }} />
                          {CATEGORY_LABELS[template.category]}
                        </span>
                        <span className="template-card__meta-item">{template.standard}</span>
                        <span className="template-card__meta-item">{template.section_count} sections</span>
                      </div>
                      <div className="template-card__actions">
                        {!template.is_builtin && (
                          <button type="button" className="button button--quiet button--sm" disabled={isBusy} onClick={(e) => { e.stopPropagation(); handleDeleteClick(template.id); }}>
                            Delete
                          </button>
                        )}
                        <button type="button" className="button button--secondary button--sm" disabled={isBusy} onClick={(e) => { e.stopPropagation(); void handleDuplicate(template.id, template.name); }}>
                          {template.is_builtin ? "Customize" : "Duplicate"}
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="template-list">
              {paginatedTemplates.map((template) => (
                <div
                  key={template.id}
                  className={"template-list-item" + (selectedTemplate?.id === template.id ? " template-list-item--selected" : "")}
                  onClick={() => void handleSelectTemplate(template.id)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => { if (e.key === "Enter") void handleSelectTemplate(template.id); }}
                  style={{ "--card-accent": CATEGORY_COLORS[template.category] } as React.CSSProperties}
                >
                  <div className="template-list-item__accent" />
                  <span className="template-list-item__icon">{CATEGORY_ICONS[template.category] || "\ud83d\udcc4"}</span>
                  <div className="template-list-item__info">
                    <div className="template-list-item__top">
                      <span className="template-card__key">{template.key}</span>
                      <strong className="template-list-item__name">{template.name}</strong>
                      {template.is_builtin
                        ? <span className="template-card__badge">Built-in</span>
                        : <span className="template-card__badge template-card__badge--custom">Custom</span>
                      }
                    </div>
                    <div className="template-list-item__bottom">
                      <span className="template-list-item__desc">{template.description || "No description"}</span>
                      <span className="template-list-item__meta">
                        {CATEGORY_LABELS[template.category]} {"\u00b7"} {template.standard} {"\u00b7"} {template.section_count} sections
                      </span>
                    </div>
                  </div>
                  <div className="template-list-item__actions">
                    {!template.is_builtin && (
                      <button type="button" className="button button--quiet button--sm" disabled={isBusy} onClick={(e) => { e.stopPropagation(); handleDeleteClick(template.id); }}>
                        Delete
                      </button>
                    )}
                    <button type="button" className="button button--secondary button--sm" disabled={isBusy} onClick={(e) => { e.stopPropagation(); void handleDuplicate(template.id, template.name); }}>
                      {template.is_builtin ? "Customize" : "Duplicate"}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {filteredTemplates.length > PAGE_SIZE && (
          <div className="template-pagination">
            <button
              type="button"
              className="template-pagination__btn"
              disabled={currentPage === 1}
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
            >
              Prev
            </button>
            <div className="template-pagination__pages">
              {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
                <button
                  key={page}
                  type="button"
                  className={page === currentPage ? "template-pagination__page template-pagination__page--active" : "template-pagination__page"}
                  onClick={() => setCurrentPage(page)}
                >
                  {page}
                </button>
              ))}
            </div>
            <button
              type="button"
              className="template-pagination__btn"
              disabled={currentPage === totalPages}
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
            >
              Next
            </button>
          </div>
        )}

        {selectedTemplate && (
          <div
            className="template-modal-overlay"
            onClick={(event) => {
              if (event.target === event.currentTarget) {
                setSelectedTemplate(null);
                setIsEditing(false);
              }
            }}
            role="dialog"
            aria-modal="true"
            aria-label={"Preview: " + selectedTemplate.name}
          >
            <div className="template-modal">
              <header className="template-modal__header">
                <div className="template-modal__title">
                  <span className="template-card__cat-icon">{CATEGORY_ICONS[selectedTemplate.category] || "\ud83d\udcc4"}</span>
                  <span className="template-card__key">{selectedTemplate.key}</span>
                  {selectedTemplate.is_builtin
                    ? <span className="template-card__badge">Built-in</span>
                    : <span className="template-card__badge template-card__badge--custom">Custom</span>
                  }
                  <h3>{selectedTemplate.name}</h3>
                </div>
                <div className="template-modal__header-actions">
                  {isEditing ? (
                    <>
                      <button type="button" className="button button--primary button--sm" disabled={isBusy || selectedTemplate.is_builtin} onClick={() => void handleSave()}>
                        {isBusy ? "Saving..." : "Save"}
                      </button>
                      <button type="button" className="button button--secondary button--sm" onClick={() => { setIsEditing(false); setEditContent(selectedTemplate.content); }}>
                        Cancel
                      </button>
                    </>
                  ) : (
                    <>
                      <button type="button" className="button button--secondary button--sm" disabled={selectedTemplate.is_builtin} onClick={() => setIsEditing(true)}>
                        {selectedTemplate.is_builtin ? "Read-only" : "Edit"}
                      </button>
                      {!selectedTemplate.is_builtin && (
                        <button type="button" className="button button--quiet button--sm" disabled={isBusy} onClick={() => handleDeleteClick(selectedTemplate.id)}>
                          Delete
                        </button>
                      )}
                    </>
                  )}
                  <button type="button" className="template-modal__close" onClick={() => { setSelectedTemplate(null); setIsEditing(false); }} aria-label="Close preview">
                    {"\u00d7"}
                  </button>
                </div>
              </header>

              <div className="template-modal__meta">
                <span style={{ color: CATEGORY_COLORS[selectedTemplate.category] }}>{CATEGORY_LABELS[selectedTemplate.category]}</span>
                <span>{selectedTemplate.standard}</span>
                <span>v{selectedTemplate.version}</span>
                <span className="template-modal__meta-desc">{selectedTemplate.description}</span>
              </div>

              <div className="template-modal__body">
                {isEditing ? (
                  <div className="template-editor-wrapper">
                    <div className="template-editor-toolbar">
                      <button type="button" className="template-editor-btn" title="Bold" onClick={() => insertMarkdown("**", "**")}>B</button>
                      <button type="button" className="template-editor-btn template-editor-btn--italic" title="Italic" onClick={() => insertMarkdown("*", "*")}>I</button>
                      <span className="template-editor-separator" />
                      <button type="button" className="template-editor-btn" title="Heading 2" onClick={() => insertMarkdown("## ", "")}>H2</button>
                      <button type="button" className="template-editor-btn" title="Heading 3" onClick={() => insertMarkdown("### ", "")}>H3</button>
                      <span className="template-editor-separator" />
                      <button type="button" className="template-editor-btn" title="Table" onClick={() => insertMarkdown("| Col 1 | Col 2 |\n|-------|-------|\n| ", " | |")}>Table</button>
                      <button type="button" className="template-editor-btn" title="List" onClick={() => insertMarkdown("- ", "")}>List</button>
                      <button type="button" className="template-editor-btn" title="Code" onClick={() => insertMarkdown("```\n", "\n```")}>Code</button>
                    </div>
                    <textarea
                      ref={editorRef}
                      className="template-content-editor template-content-editor--full"
                      value={editContent}
                      onChange={(event) => setEditContent(event.target.value)}
                      aria-label="Edit template content"
                    />
                  </div>
                ) : (
                  <MarkdownPreview content={selectedTemplate.content} />
                )}
              </div>
            </div>
          </div>
        )}

        {confirmDeleteId && (
          <div className="confirm-dialog-overlay" onClick={() => setConfirmDeleteId(null)}>
            <div className="confirm-dialog" onClick={(e) => e.stopPropagation()}>
              <p className="confirm-dialog__message">Are you sure you want to delete this template?</p>
              <div className="confirm-dialog__actions">
                <button type="button" className="button button--quiet" onClick={() => setConfirmDeleteId(null)}>Cancel</button>
                <button type="button" className="button button--danger" onClick={() => void executeDelete(confirmDeleteId)}>Delete</button>
              </div>
            </div>
          </div>
        )}

        {toast && (
          <div className={"toast-message " + (toast.isError ? "toast-message--error" : "toast-message--success")} role="alert">
            {toast.message}
          </div>
        )}
      </div>
    </div>
  );
}
