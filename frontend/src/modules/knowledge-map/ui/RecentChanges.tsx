import type { ChangeItem } from "../domain/changeTypes";

interface Props {
  changes: ChangeItem[];
}

function ChangeBadge({ changeType }: { changeType: string }) {
  if (changeType === "added") return <span className="km-change-badge km-change-badge--added">Tambah</span>;
  if (changeType === "removed") return <span className="km-change-badge km-change-badge--removed">Hapus</span>;
  return <span className="km-change-badge km-change-badge--modified">Ubah</span>;
}

export function RecentChanges({ changes }: Props) {
  if (changes.length === 0) {
    return <div className="km-empty">Belum ada perubahan terdeteksi</div>;
  }

  return (
    <table className="km-table">
      <thead>
        <tr>
          <th>Perubahan</th>
          <th>Sumber</th>
          <th>Jenis</th>
          <th>Kapan</th>
        </tr>
      </thead>
      <tbody>
        {changes.map((c) => (
          <tr key={c.id}>
            <td>
              <span>{c.description}</span>
              <span className="km-table__detail">{c.detail}</span>
            </td>
            <td className="km-table__source">{c.sourceName}</td>
            <td>
              <ChangeBadge changeType={c.changeType} />
            </td>
            <td className="km-table__time">{c.timestamp}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
