import type { DetectedFeature } from "../domain/types";

interface Props {
  features: DetectedFeature[];
}

function StatusDot({ status }: { status: string }) {
  if (status === "ready") return <span className="km-status km-status--ready">&#10003;</span>;
  if (status === "partial") return <span className="km-status km-status--partial">!</span>;
  return <span className="km-status km-status--missing">&#10007;</span>;
}

export function FeatureList({ features }: Props) {
  return (
    <table className="km-table">
      <thead>
        <tr>
          <th>Fitur</th>
          <th>Sumber</th>
          <th>Dokumen</th>
          <th>Test</th>
        </tr>
      </thead>
      <tbody>
        {features.map((f) => (
          <tr key={f.key}>
            <td>{f.name}</td>
            <td className="km-table__source">{f.source === "auto" ? "Otomatis" : "Manual"}</td>
            <td>
              <StatusDot status={f.docStatus} />
              <span className="km-table__count">{f.docCount}/{f.docTotal}</span>
            </td>
            <td>
              <StatusDot status={f.testStatus} />
              <span className="km-table__count">{f.testCount}/{f.testTotal}</span>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
