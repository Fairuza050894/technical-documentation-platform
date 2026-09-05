import type { OverviewStat } from "../domain/types";

interface Props {
  stats: OverviewStat[];
}

export function OverviewCards({ stats }: Props) {
  return (
    <div className="km-overview">
      {stats.map((stat) => (
        <div key={stat.label} className={`km-overview__card km-overview__card--${stat.status}`}>
          <span className="km-overview__value">{stat.value}</span>
          <span className="km-overview__label">{stat.label}</span>
          <span className="km-overview__detail">{stat.detail}</span>
        </div>
      ))}
    </div>
  );
}
