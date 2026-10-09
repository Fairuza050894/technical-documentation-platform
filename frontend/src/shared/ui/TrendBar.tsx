import { useMemo } from "react";

interface TrendBarProps {
  data: number[];
  height: number;
  width: number;
  minValue?: number;
  maxValue?: number;
  className?: string;
}

export function TrendBar({
  data,
  height,
  width,
  minValue = 0,
  maxValue = 100,
  className = "",
}: TrendBarProps) {
  if (data.length === 0) {
    return (
      <div
        className={`trend-bar ${className}`}
        style={{ height, width, background: "var(--color-border-subtle)" }}
        aria-label="No data"
      />
    );
  }

  const barWidth = width / data.length;
  const valueRange = maxValue - minValue || 1;

  const bars = useMemo(() => {
    const elements: React.ReactNode[] = [];
    for (let i = 0; i < data.length; i++) {
      const normalized = valueRange > 0 ? (data[i]! - minValue) / valueRange : 0;
      const clamped = Math.max(0, Math.min(1, normalized));
      const barHeight = clamped * (height - 4);
      elements.push(
        <div
          key={i}
          className="trend-bar__bar"
          style={{
            left: i * barWidth,
            width: Math.max(1, barWidth - 2),
            height: barHeight,
            background:
              barHeight > (height - 4) * 0.7
                ? "var(--color-score-high)"
                : barHeight > (height - 4) * 0.4
                ? "var(--color-score-medium)"
                : "var(--color-score-low)",
          }}
          aria-label={`Value ${data[i]}`}
        />
      );
    }
    return elements;
  }, [data, height, width, minValue, maxValue]);

  return (
    <div
      className={`trend-bar ${className}`}
      style={{ height, width, position: "relative", background: "var(--color-border-subtle)" }}
      aria-label="Trend chart"
    >
      {bars}
    </div>
  );
}