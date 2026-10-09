import { useEffect, useMemo, useState } from "react";
import type { Role } from "../domain/types";
import { getDemoKnowledgeMapData } from "../infrastructure/mockData";
import { ActionItems } from "./ActionItems";
import { FeatureList } from "./FeatureList";
import { OverviewCards } from "./OverviewCards";
import { RecentChanges } from "./RecentChanges";
import { RoleSwitcher } from "./RoleSwitcher";

const STORAGE_KEY = "km-role";
const demoMode = import.meta.env.VITE_KNOWLEDGE_MAP_DEMO === "true";

function getStoredRole(): Role {
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored === "po-ba" || stored === "developer" || stored === "qa" || stored === "devops") {
    return stored;
  }
  return "po-ba";
}

export function KnowledgeMap() {
  const [role, setRole] = useState<Role>(getStoredRole);
  const data = useMemo(() => (demoMode ? getDemoKnowledgeMapData() : null), []);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, role);
  }, [role]);

  if (data === null) {
    return (
      <div className="km">
        <div className="km__header">
          <div>
            <h1 className="km__title">Knowledge Map</h1>
            <p className="km__subtitle">
              Source-backed visibility for documentation, test, and change evidence.
            </p>
          </div>
        </div>

        <section className="km__section" aria-live="polite">
          <h2 className="km__section-title">Evidence status</h2>
          <div className="km-empty">
            Knowledge Map does not yet have a source-backed aggregator at this baseline.
            Demo data is intentionally not shown as repository fact. Connect this capability
            to the evidence API before using metrics, changes, or action items for
            operational decisions.
          </div>
        </section>
      </div>
    );
  }

  const filteredActions = data.actionItems.filter((item) => item.targetRole === role);

  return (
    <div className="km">
      <div className="km__header">
        <div>
          <h1 className="km__title">Knowledge Map</h1>
          <p className="km__subtitle">Mode demo — data di bawah adalah fixture untuk preview UI.</p>
        </div>
        <RoleSwitcher value={role} onChange={setRole} />
      </div>

      <section className="km__section">
        <h2 className="km__section-title">Ringkasan demo</h2>
        <OverviewCards stats={data.overview} />
      </section>

      <section className="km__section">
        <h2 className="km__section-title">Perubahan demo</h2>
        <RecentChanges changes={data.recentChanges} />
      </section>

      <section className="km__section">
        <h2 className="km__section-title">Action item demo</h2>
        <ActionItems items={filteredActions} />
      </section>

      <section className="km__section">
        <h2 className="km__section-title">Fitur demo</h2>
        <FeatureList features={data.features} />
      </section>
    </div>
  );
}
