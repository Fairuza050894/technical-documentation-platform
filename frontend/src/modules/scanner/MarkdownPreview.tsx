import { useMemo } from "react";
import { MermaidDiagram } from "./MermaidDiagram";

interface MarkdownPreviewProps {
  content: string;
}

interface ParsedBlock {
  type: "markdown" | "mermaid";
  content: string;
  id: string;
}

function parseContent(raw: string): ParsedBlock[] {
  const blocks: ParsedBlock[] = [];
  const parts = raw.split(/```mermaid\n?/);

  for (let i = 0; i < parts.length; i++) {
    if (i % 2 === 0) {
      if ((parts[i] ?? "").trim()) {
        blocks.push({ type: "markdown", content: parts[i] ?? "", id: "md-" + i });
      }
    } else {
      const part = parts[i] ?? "";
      const endIdx = part.indexOf("```");
      const chart = endIdx >= 0 ? part.slice(0, endIdx) : part;
      if (chart.trim()) {
        blocks.push({ type: "mermaid", content: chart.trim(), id: "mm-" + i });
      }
      const rest = endIdx >= 0 ? part.slice(endIdx + 3) : "";
      if (rest.trim()) {
        blocks.push({ type: "markdown", content: rest, id: "md-rest-" + i });
      }
    }
  }

  return blocks;
}

function renderMarkdownLine(line: string | undefined, key: number): React.ReactNode {
  if (!line) return null;
  const trimmed = line.trimStart();

  if (trimmed.startsWith("# ")) return <h1 key={key}>{trimmed.slice(2)}</h1>;
  if (trimmed.startsWith("## ")) return <h2 key={key}>{trimmed.slice(3)}</h2>;
  if (trimmed.startsWith("### ")) return <h3 key={key}>{trimmed.slice(4)}</h3>;
  if (trimmed.startsWith("#### ")) return <h4 key={key}>{trimmed.slice(5)}</h4>;
  if (trimmed.startsWith("> ")) return <blockquote key={key}>{renderInline(String(trimmed.slice(2)))}</blockquote>;
  if (trimmed.startsWith("---")) return <hr key={key} />;
  if (trimmed.startsWith("- ")) return <li key={key} className="md-li">{renderInline(trimmed.slice(2))}</li>;
  if (/^\d+\. /.test(trimmed)) return <li key={key} className="md-oli">{renderInline(trimmed.replace(/^\d+\. /, ""))}</li>;
  if (trimmed.startsWith("| ")) {
    return <div key={key} className="md-table-row">{renderInline(trimmed)}</div>;
  }
  if (trimmed.startsWith("```")) return null;
  if (trimmed.startsWith("<!--")) return null;
  if (trimmed.endsWith("-->")) return null;
  if (!trimmed) return <br key={key} />;

  return <p key={key}>{renderInline(trimmed)}</p>;
}

function renderInline(text: string): React.ReactNode {
  const parts: React.ReactNode[] = [];
  let remaining = text;
  let idx = 0;

  const patterns = [
    { regex: /\*\*(.+?)\*\*/, tag: "strong" as const },
    { regex: /\*(.+?)\*/, tag: "em" as const },
    { regex: /`([^`]+)`/, tag: "code" as const },
    { regex: /\[([^\]]+)\]\(([^)]+)\)/, tag: "a" as const },
  ];

  while (remaining.length > 0) {
    let earliest = -1;
    let earliestIdx = remaining.length;
    let earliestMatch: RegExpMatchArray | null = null;

    for (let p = 0; p < patterns.length; p++) {
      const pat = patterns[p];
      if (!pat) continue;
      const match = remaining.match(pat.regex);
      if (match && match.index !== undefined && match.index < earliestIdx) {
        earliestIdx = match.index;
        earliest = p;
        earliestMatch = match;
      }
    }

    if (earliest === -1 || !earliestMatch || earliestMatch.index === undefined) {
      parts.push(remaining);
      break;
    }

    if (earliestMatch.index > 0) {
      parts.push(remaining.slice(0, earliestMatch.index));
    }

    const pattern = patterns[earliest];
    if (!pattern) { parts.push(remaining); break; }
    const captured1 = earliestMatch[1] ?? "";
    const captured2 = earliestMatch[2] ?? "";
    const matchLen = earliestMatch[0].length;

    if (pattern.tag === "a") {
      parts.push(<a key={idx++} href={captured2} target="_blank" rel="noreferrer">{captured1}</a>);
    } else if (pattern.tag === "strong") {
      parts.push(<strong key={idx++}>{captured1}</strong>);
    } else if (pattern.tag === "em") {
      parts.push(<em key={idx++}>{captured1}</em>);
    } else if (pattern.tag === "code") {
      parts.push(<code key={idx++} className="md-inline-code">{captured1}</code>);
    }

    remaining = remaining.slice(earliestMatch.index + matchLen);
  }

  return <>{parts}</>;
}

function renderMarkdownBlock(text: string): React.ReactNode {
  const lines = text.split("\n");
  const elements: React.ReactNode[] = [];
  let inCodeBlock = false;
  let codeLines: string[] = [];
  let codeKey = 0;

  for (let i = 0; i < lines.length; i++) {
    const line: string = lines[i] ?? "";
    if (line.trimStart().startsWith("```")) {
      if (inCodeBlock) {
        elements.push(<pre key={"code-" + codeKey++} className="md-code-block"><code>{codeLines.join("\n")}</code></pre>);
        codeLines = [];
        inCodeBlock = false;
      } else {
        inCodeBlock = true;
      }
      continue;
    }
    if (inCodeBlock) {
      codeLines.push(line);
      continue;
    }
    elements.push(renderMarkdownLine(line, i));
  }

  if (inCodeBlock && codeLines.length > 0) {
    elements.push(<pre key={"code-" + codeKey} className="md-code-block"><code>{codeLines.join("\n")}</code></pre>);
  }

  return <>{elements}</>;
}

export function MarkdownPreview({ content }: MarkdownPreviewProps) {
  const blocks = useMemo(() => parseContent(content), [content]);

  return (
    <div className="markdown-preview">
      {blocks.map((block) => {
        if (block.type === "mermaid") {
          return <MermaidDiagram key={block.id} chart={block.content} id={block.id} />;
        }
        return <div key={block.id} className="md-block">{renderMarkdownBlock(block.content)}</div>;
      })}
    </div>
  );
}
