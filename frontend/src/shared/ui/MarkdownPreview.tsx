import { useMemo } from "react";

interface MarkdownPreviewProps {
  content: string;
}

export function MarkdownPreview({ content }: MarkdownPreviewProps) {
  const html = useMemo(() => renderMarkdown(content), [content]);
  return (
    <div
      className="markdown-preview"
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}

function renderMarkdown(source: string): string {
  const lines = source.split("\n");
  const output: string[] = [];
  let inTable = false;
  let tableRows: string[] = [];
  let inCodeBlock = false;
  let codeLines: string[] = [];
  let codeLanguage = "";
  let inList = false;
  let listItems: string[] = [];
  let listType: "ul" | "ol" = "ul";

  function flushTable(): void {
    if (tableRows.length === 0) return;
    const headerRow = tableRows[0] ?? "";
    const headerCells = parseTableRow(headerRow);
    const bodyRows = tableRows.slice(2);
    let html = '<table class="md-table"><thead><tr>';
    for (const cell of headerCells) {
      html += `<th>${inlineFormat(cell)}</th>`;
    }
    html += "</tr></thead><tbody>";
    for (const row of bodyRows) {
      const cells = parseTableRow(row);
      html += "<tr>";
      for (const cell of cells) {
        html += `<td>${inlineFormat(cell)}</td>`;
      }
      html += "</tr>";
    }
    html += "</tbody></table>";
    output.push(html);
    tableRows = [];
    inTable = false;
  }

  function flushCode(): void {
    if (codeLines.length === 0) return;
    const escaped = codeLines
      .join("\n")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
    const langLabel = codeLanguage ? ` data-lang="${codeLanguage}"` : "";
    output.push(`<pre class="md-code-block"${langLabel}><code>${escaped}</code></pre>`);
    codeLines = [];
    codeLanguage = "";
    inCodeBlock = false;
  }

  function flushList(): void {
    if (listItems.length === 0) return;
    const tag = listType;
    const items = listItems.map((item) => `<li>${inlineFormat(item)}</li>`).join("");
    output.push(`<${tag} class="md-list">${items}</${tag}>`);
    listItems = [];
    inList = false;
  }

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i] ?? "";

    if (line.trim().startsWith("```")) {
      if (inCodeBlock) {
        flushCode();
      } else {
        if (inTable) flushTable();
        if (inList) flushList();
        inCodeBlock = true;
        codeLanguage = (line.trim().slice(3) ?? "").trim();
      }
      continue;
    }

    if (inCodeBlock) {
      codeLines.push(line);
      continue;
    }

    if (line.trim().startsWith("|") && line.trim().endsWith("|")) {
      if (!inTable) {
        if (inList) flushList();
        inTable = true;
      }
      tableRows.push(line.trim());
      continue;
    } else if (inTable) {
      flushTable();
    }

    const headingMatch = line.match(/^(#{1,6})\s+(.+)$/);
    if (headingMatch && headingMatch[1] && headingMatch[2]) {
      if (inList) flushList();
      const level = headingMatch[1].length;
      const text = inlineFormat(headingMatch[2]);
      output.push(`<h${level} class="md-h${level}">${text}</h${level}>`);
      continue;
    }

    if (line.trim() === "---") {
      if (inList) flushList();
      output.push('<hr class="md-hr" />');
      continue;
    }

    const ulMatch = line.match(/^[-*]\s+(.+)$/);
    if (ulMatch && ulMatch[1]) {
      if (inList && listType !== "ul") flushList();
      if (!inList) { inList = true; listType = "ul"; }
      listItems.push(ulMatch[1]);
      continue;
    }

    const olMatch = line.match(/^\d+\.\s+(.+)$/);
    if (olMatch && olMatch[1]) {
      if (inList && listType !== "ol") flushList();
      if (!inList) { inList = true; listType = "ol"; }
      listItems.push(olMatch[1]);
      continue;
    }

    if (inList && line.trim() === "") {
      flushList();
      continue;
    }

    if (line.trim().startsWith("> ")) {
      if (inList) flushList();
      const bqText = line.trim().slice(2);
      output.push(`<blockquote class="md-blockquote">${inlineFormat(bqText)}</blockquote>`);
      continue;
    }

    if (line.trim() === "") {
      if (inList) flushList();
      continue;
    }

    if (inList) flushList();
    output.push(`<p class="md-paragraph">${inlineFormat(line)}</p>`);
  }

  if (inTable) flushTable();
  if (inCodeBlock) flushCode();
  if (inList) flushList();

  return output.join("\n");
}

function inlineFormat(text: string): string {
  return text
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.+?)\*/g, "<em>$1</em>")
    .replace(/`(.+?)`/g, '<code class="md-inline-code">$1</code>')
    .replace(/$$(.+?)$$$$(.+?)$$/g, '<a class="md-link" href="$2">$1</a>')
    .replace(/<!--.+?-->/g, "");
}

function parseTableRow(line: string): string[] {
  return line
    .split("|")
    .slice(1, -1)
    .map((cell) => (cell ?? "").trim());
}
