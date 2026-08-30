import { useEffect, useRef } from "react";
import mermaid from "mermaid";

let mermaidInitialized = false;

function ensureMermaidInit(): void {
  if (mermaidInitialized) return;
  mermaid.initialize({
    startOnLoad: false,
    theme: "default",
    securityLevel: "loose",
    fontFamily: "inherit",
    flowchart: { curve: "basis", padding: 16 },
    er: {},
    sequence: { mirrorActors: false, messageAlign: "center" },
  });
  mermaidInitialized = true;
}

interface MermaidDiagramProps {
  chart: string;
  id?: string;
}

export function MermaidDiagram({ chart, id }: MermaidDiagramProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const renderId = id || "mermaid-" + Math.random().toString(36).slice(2, 10);

  useEffect(() => {
    if (!containerRef.current || !chart.trim()) return;
    ensureMermaidInit();

    let cancelled = false;

    async function render(): Promise<void> {
      try {
        const { svg } = await mermaid.render(renderId, chart.trim());
        if (!cancelled && containerRef.current) {
          containerRef.current.innerHTML = svg;
        }
      } catch (err) {
        if (!cancelled && containerRef.current) {
          containerRef.current.innerHTML = '<pre class="mermaid-fallback">' + chart + '</pre>';
        }
      }
    }

    void render();
    return () => { cancelled = true; };
  }, [chart, renderId]);

  return <div ref={containerRef} className="mermaid-container" />;
}
