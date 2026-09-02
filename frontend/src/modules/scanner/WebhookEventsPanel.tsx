import { useCallback, useEffect, useState } from "react";
import { listWebhookEvents } from "./api";
import type { WebhookEvent } from "./types";

interface WebhookEventsPanelProps {
  onSelectScan?: (scanId: string) => void;
}

export function WebhookEventsPanel({ onSelectScan }: WebhookEventsPanelProps) {
  const [events, setEvents] = useState<WebhookEvent[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async (signal?: AbortSignal) => {
    try {
      const data = await listWebhookEvents(signal);
      setEvents(data.items);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    void load(controller.signal);
    return () => controller.abort();
  }, [load]);

  if (loading) return <div className="webhook-panel"><p>Loading...</p></div>;

  return (
    <div className="webhook-panel">
      <div className="webhook-panel__header">
        <h3>Webhook Events</h3>
        <span className="webhook-panel__count">{events.length}</span>
      </div>
      {events.length === 0 ? (
        <div className="webhook-panel__empty">
          <p>No webhook events yet. Configure a GitHub webhook to start receiving push and PR events.</p>
          <p className="webhook-panel__url">Webhook URL: <code>/api/scanner/webhooks/github</code></p>
        </div>
      ) : (
        <div className="webhook-panel__list">
          {events.map((event) => (
            <div key={event.id} className={"webhook-event webhook-event--" + event.status.toLowerCase()}>
              <div className="webhook-event__header">
                <span className="webhook-event__type">{event.event_type === "push" ? "→ Push" : "↔ PR"}</span>
                <span className="webhook-event__branch">{event.branch}</span>
                <span className={"webhook-event__status webhook-event__status--" + event.status.toLowerCase()}>{event.status}</span>
              </div>
              <div className="webhook-event__body">
                <span className="webhook-event__sha">{event.commit_sha.slice(0, 7)}</span>
                <span className="webhook-event__message">{event.commit_message}</span>
              </div>
              <div className="webhook-event__footer">
                <span className="webhook-event__sender">{event.sender}</span>
                <span className="webhook-event__time">{getTimeAgo(event.created_at)}</span>
                {event.scan_id && (
                  <button type="button" className="webhook-event__scan-link" onClick={() => onSelectScan?.(event.scan_id)}>View Scan</button>
                )}
                {event.score_delta !== 0 && (
                  <span className="webhook-event__delta" style={{ color: event.score_delta > 0 ? "#16a34a" : "#dc2626" }}>
                    {event.score_delta > 0 ? "+" : ""}{event.score_delta}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function getTimeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return mins + "m ago";
  const hours = Math.floor(mins / 60);
  if (hours < 24) return hours + "h ago";
  const days = Math.floor(hours / 24);
  return days + "d ago";
}
