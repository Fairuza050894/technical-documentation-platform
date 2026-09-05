export interface ChangeItem {
  id: string;
  description: string;
  sourceName: string;
  changeType: "added" | "removed" | "modified";
  timestamp: string;
  detail: string;
}
