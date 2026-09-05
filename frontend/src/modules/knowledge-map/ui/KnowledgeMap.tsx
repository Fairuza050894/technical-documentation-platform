import { useState, useMemo, useEffect } from "react";
import type { Role } from "../domain/types";
import { RoleSwitcher } from "./RoleSwitcher";
import { OverviewCards } from "./OverviewCards";
import { ActionItems } from "./ActionItems";
import { FeatureList } from "./FeatureList";
import { RecentChanges } from "./RecentChanges";
import { getMockKnowledgeMapData } from "../infrastructure/mockData";

const STORAGE_KEY = "km-role";

function getStoredRole(): Role {
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored === "po-ba" || stored === "developer" || stored === "qa" || stored === "devops") {
    return stored;
  }
  return "po-ba";
}

export function KnowledgeMap() {
  const [role, setRole] = useState<Role>(getStoredRole);
  const data = useMemo(() => getMockKnowledgeMapData(), []);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, role);
  }, [role]);

  const filteredActions = useMemo(
    () => data.actionItems.filter((item) => item.targetRole === role),
    [data.actionItems, role]
  );

  return (
    <div className="km">
      <div className="km__header">
        <div>
          <h1 className="km__title">Knowledge Map</h1>
          <p className="km__subtitle">Apa yang kita tahu, apa yang kurang, dan apa yang harus dilakukan</p>
        </div>
        <RoleSwitcher value={role} onChange={setRole} />
      </div>

      <section className="km__section">
        <h2 className="km__section-title">Ringkasan</h2>
        <OverviewCards stats={data.overview} />
      </section>

      <section className="km__section">
        <h2 className="km__section-title">Perubahan terbaru</h2>
        <RecentChanges changes={data.recentChanges} />
      </section>

      <section className="km__section">
        <h2 className="km__section-title">Yang harus dikerjakan</h2>
        <ActionItems items={filteredActions} />
      </section>

      <section className="km__section">
        <h2 className="km__section-title">Fitur terdeteksi</h2>
        <FeatureList features={data.features} />
      </section>
    </div>
  );
}
