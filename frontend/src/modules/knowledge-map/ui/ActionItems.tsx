import type { ActionItem } from "../domain/types";
import { URGENCY_LABELS } from "../domain/constants";

interface Props {
  items: ActionItem[];
}

export function ActionItems({ items }: Props) {
  if (items.length === 0) {
    return <div className="km-empty">Tidak ada action item untuk role ini</div>;
  }

  return (
    <table className="km-table">
      <thead>
        <tr>
          <th>Yang harus dikerjakan</th>
          <th>Cara menyelesaikan</th>
          <th>Urgency</th>
        </tr>
      </thead>
      <tbody>
        {items.map((item) => (
          <tr key={item.id}>
            <td>{item.description}</td>
            <td className="km-table__remediation">{item.remediation}</td>
            <td>
              <span className={`km-badge km-badge--${item.urgency}`}>
                {URGENCY_LABELS[item.urgency]}
              </span>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
