import { useCallback, useEffect, useMemo, useState } from "react";

import { Icon } from "../../shared/ui/Icon";
import { MarkdownPreview } from "../../shared/ui/MarkdownPreview";
import {
  createTemplate,
  deleteTemplate,
  duplicateTemplate,
  getTemplate,
  listTemplates,
  updateTemplate,
} from "./api";
import type {
  CreateTemplateInput,
  TemplateCategory,
  TemplateCollection,
  TemplateDetail,
  TemplateSummary,
  UpdateTemplateInput,
} from "./types";
import { CATEGORY_LABELS, CATEGORY_ORDER } from "./types";

interface TemplateWorkspaceProps {
  embedded?: boolean;
}

export function TemplateWorkspace({ embedded = false }: TemplateWorkspaceProps) {
  const [templates, setTemplates] = useState<TemplateCollection>({ items: [], total: 0 });
  const [selectedTemplate, setSelectedTemplate] = useState<TemplateDetail | null>(null);
  const [activeCategory, setActiveCategory] = useState<TemplateCategory | "ALL">("ALL");
  const [filter, setFilter] = useState("");
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [isBusy, setIsBusy] = useState(false);
  const [message, setMessage] = useState("Loading templates...");
  const [editContent, setEditContent] = useState("");
  const [isEditing, setIsEditing] = useState(false);

  const [formKey, setFormKey] = useState("");
  const [formName, setFormName] = useState("");
  const [formDescription, setFormDescription] = useState("");
  const [formCategory, setFormCategory] = useState<TemplateCategory>("REQUIREMENTS");
  const [formStandard, setFormStandard] = useState("Custom");
  const [formContent, setFormContent] = useState("");

  const load = useCallback(async (signal?: AbortSignal) => {
    try {
      const collection = await listTemplates(undefined, signal);
      setTemplates(collection);
      setMessage(`${collection.total} templates available`);
    } catch (error: unknown) {
      if (error instanceof DOMException && error.name === "AbortError") return;
      setMessage(error instanceof Error ? error.message : "Templates could not be loaded.");
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    void load(controller.signal);
    return () => controller.abort();
  }, [load]);

  const filteredTemplates = useMemo(() => {
    let items = templates.items;
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
  }, [templates.items, activeCategory, filter]);

  const categoryCounts = useMemo(() => {
    const counts: Record<string, number> = { ALL: templates.items.length };
    for (const item of templates.items) {
      counts[item.category] = (counts[item.category] || 0) + 1;
    }
    return counts;
  }, [templates.items]);

  async function handleSelectTemplate(templateId: string): Promise<void> {
    setMessage("Loading template...");
    try {
      const detail = await getTemplate(templateId);
      setSelectedTemplate(detail);
      setEditContent(detail.content);
      setIsEditing(false);
      setMessage(`${detail.name} loaded`);
    } catch (error: unknown) {
      setMessage(error instanceof Error ? error.message : "Template could not be loaded.");
    }
  }

  async function handleSave(): Promise<void> {
    if (!selectedTemplate || isBusy) return;
    setIsBusy(true);
    setMessage("Saving template...");
    try {
      const input: UpdateTemplateInput = { content: editContent };
      const updated = await updateTemplate(selectedTemplate.id, input);
      setSelectedTemplate(updated);
      setEditContent(updated.content);
      setIsEditing(false);
      await load();
      setMessage(`Template saved as v${updated.version}`);
    } catch (error: unknown) {
      setMessage(error instanceof Error ? error.message : "Save failed.");
    } finally {
      setIsBusy(false);
    }
  }

  async function handleDuplicate(templateId: string, name: string): Promise<void> {
    if (isBusy) return;
    setIsBusy(true);
    setMessage("Duplicating template...");
    try {
      const newKey = prompt(`Enter key for copy of "${name}":`);
      if (!newKey) {
        setIsBusy(false);
        return;
      }
      const copy = await duplicateTemplate(templateId, newKey);
      await load();
      setMessage(`Duplicated as ${copy.key}`);
    } catch (error: unknown) {
      setMessage(error instanceof Error ? error.message : "Duplication failed.");
    } finally {
      setIsBusy(false);
    }
  }

  async function handleDelete(templateId: string): Promise<void> {
    if (isBusy) return;
    setIsBusy(true);
    setMessage("Deleting template...");
    try {
      await deleteTemplate(templateId);
      if (selectedTemplate?.id === templateId) {
        setSelectedTemplate(null);
      }
      await load();
      setMessage("Template deleted");
    } catch (error: unknown) {
      setMessage(error instanceof Error ? error.message : "Delete failed.");
    } finally {
      setIsBusy(false);
    }
  }

  async function handleCreate(): Promise<void> {
    if (isBusy) return;
    setIsBusy(true);
    setMessage("Creating template...");
    try {
      const input: CreateTemplateInput = {
        key: formKey,
        name: formName,
        description: formDescription,
        category: formCategory,
        standard: formStandard,
        content: formContent,
      };
      const created = await createTemplate(input);
      await load();
      setShowCreateForm(false);
      resetForm();
      setMessage(`Template ${created.key} created`);
    } catch (error: unknown) {
      setMessage(error instanceof Error ? error.message : "Creation failed.");
    } finally {
      setIsBusy(false);
    }
  }

  function resetForm(): void {
    setFormKey("");
    setFormName("");
    setFormDescription("");
    setFormCategory("REQUIREMENTS");
    setFormStandard("Custom");
    setFormContent("");
  }

  return (
    <div className="template-workspace">
      {!embedded && (
        <header className="topbar">
          <div>
            <p className="eyebrow">Document templates</p>
            <h1>Templates</h1>
          </div>
          <span className="environment-badge">{templates.total} templates</span>
        </header>
      )}

      <div className="template-layout">
        <aside className="template-sidebar" aria-label="Template categories">
          <button
            type="button"
            className={activeCategory === "ALL" ? "template-category-btn template-category-btn--active" : "template-category-btn"}
            onClick={() => setActiveCategory("ALL")}
          >
            <span>All Templates</span>
            <span className="template-category-count">{categoryCounts.ALL || 0}</span>
          </button>
          {CATEGORY_ORDER.map((cat) => (
            <button
              key={cat}
              type="button"
              className={activeCategory === cat ? "template-category-btn template-category-btn--active" : "template-category-btn"}
              onClick={() => setActiveCategory(cat)}
            >
              <span>{CATEGORY_LABELS[cat]}</span>
              <span className="template-category-count">{categoryCounts[cat] || 0}</span>
            </button>
          ))}
        </aside>

        <div className="template-main">
          <div className="template-toolbar">
            <div className="list-filter">
              <input
                type="search"
                placeholder="Filter templates..."
                value={filter}
                onChange={(event) => setFilter(event.target.value)}
                aria-label="Filter templates"
              />
              {filter && (
                <span className="record-count">{filteredTemplates.length} of {templates.items.length}</span>
              )}
            </div>
            <button
              type="button"
              className="button button--primary"
              onClick={() => setShowCreateForm(!showCreateForm)}
            >
              {showCreateForm ? "Cancel" : "Create template"}
            </button>
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
                  <textarea id="tpl-content" className="template-content-editor" rows={15} value={formContent} onChange={(e) => setFormContent(e.target.value)} placeholder="# Template Title

## Section 1

Content here..." />
                </div>
              </div>
              <div className="form-actions">
                <button type="button" className="button button--primary" disabled={isBusy} onClick={() => void handleCreate()}>
                  {isBusy ? "Creating..." : "Create template"}
                </button>
              </div>
            </div>
          )}

          <div className="template-grid">
            {filteredTemplates.map((template) => (
              <div
                key={template.id}
                className={`template-card${selectedTemplate?.id === template.id ? " template-card--selected" : ""}`}
                onClick={() => void handleSelectTemplate(template.id)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => { if (e.key === "Enter") void handleSelectTemplate(template.id); }}
              >
                <div className="template-card__header">
                  <span className="template-card__key">{template.key}</span>
                  {template.is_builtin && <span className="template-card__badge">Built-in</span>}
                </div>
                <strong className="template-card__name">{template.name}</strong>
                <p className="template-card__description">{template.description || "No description"}</p>
                <div className="template-card__meta">
                  <span>{CATEGORY_LABELS[template.category]}</span>
                  <span>{template.standard}</span>
                  <span>{template.section_count} sections</span>
                </div>
                <div className="template-card__actions">
                  {!template.is_builtin && (
                    <button
                      type="button"
                      className="button button--quiet"
                      disabled={isBusy}
                      onClick={(e) => { e.stopPropagation(); void handleDelete(template.id); }}
                    >
                      Delete
                    </button>
                  )}
                  <button
                    type="button"
                    className="button button--secondary"
                    disabled={isBusy}
                    onClick={(e) => { e.stopPropagation(); void handleDuplicate(template.id, template.name); }}
                  >
                    Duplicate
                  </button>
                </div>
              </div>
            ))}
          </div>

          {filteredTemplates.length === 0 && (
            <div className="empty-state">
              <h3>No templates found</h3>
              <p>{filter ? "Try a different search term." : "Create a custom template to get started."}</p>
            </div>
          )}
        </div>

      </div>

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
          aria-label={`Preview: ${selectedTemplate.name}`}
        >
          <div className="template-modal">
            <header className="template-modal__header">
              <div className="template-modal__title">
                <span className="template-card__key">{selectedTemplate.key}</span>
                {selectedTemplate.is_builtin && <span className="template-card__badge">Built-in</span>}
                <h3>{selectedTemplate.name}</h3>
              </div>
              <div className="template-modal__header-actions">
                {isEditing ? (
                  <>
                    <button type="button" className="button button--primary" disabled={isBusy || selectedTemplate.is_builtin} onClick={() => void handleSave()}>
                      {isBusy ? "Saving..." : "Save"}
                    </button>
                    <button type="button" className="button button--secondary" onClick={() => { setIsEditing(false); setEditContent(selectedTemplate.content); }}>
                      Cancel
                    </button>
                  </>
                ) : (
                  <button
                    type="button"
                    className="button button--secondary"
                    disabled={selectedTemplate.is_builtin}
                    onClick={() => setIsEditing(true)}
                  >
                    {selectedTemplate.is_builtin ? "Read-only" : "Edit"}
                  </button>
                )}
                <button
                  type="button"
                  className="template-modal__close"
                  onClick={() => { setSelectedTemplate(null); setIsEditing(false); }}
                  aria-label="Close preview"
                >
                  &times;
                </button>
              </div>
            </header>

            <div className="template-modal__meta">
              <span>{CATEGORY_LABELS[selectedTemplate.category]}</span>
              <span>{selectedTemplate.standard}</span>
              <span>v{selectedTemplate.version}</span>
              <span>{selectedTemplate.description}</span>
            </div>

            <div className="template-modal__body">
              {isEditing ? (
                <textarea
                  className="template-content-editor template-content-editor--modal"
                  value={editContent}
                  onChange={(event) => setEditContent(event.target.value)}
                  aria-label="Edit template content"
                />
              ) : (
                <MarkdownPreview content={selectedTemplate.content} />
              )}
            </div>
          </div>
        </div>
      )}

      <p className="loading-state" role="status">{message}</p>
    </div>
  );
}
