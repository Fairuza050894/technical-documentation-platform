import { useEffect, useMemo, useState } from "react";

import type { Role } from "../domain/types";
import { getDemoKnowledgeMapData } from "../infrastructure/mockData";
import { ActionItems } from "./ActionItems";
import { FeatureList } from "./FeatureList";
import { OverviewCards } from "./OverviewCards";
import { RecentChanges } from "./RecentChanges";
import { RoleSwitcher } from "./RoleSwitcher";

const STORAGE_KEY = "km-role";
const DEMO_MODE = import.meta.env.VITE_KNOWLEDGE_MAP_DEMO === "true";

function getStoredRole(): Role {
  const stored = localStorage.getItem(STORAGE_KEY);
  if (
    stored === "po-ba" ||
    stored === "developer" ||
    stored === "qa" ||
    stored === "devops"
  ) {
    return stored;
  }
  return "po-ba";
}

export function KnowledgeMap() {
  const [role, setRole] = useState<Role>(getStoredRole);
  const data = useMemo(
    () => (DEMO_MODE ? getDemoKnowledgeMapData() : null),
    [],
  );

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, role);
  }, [role]);

  const filteredActions = useMemo(
    () =>
      data === null
        ? []
        : data.actionItems.filter((item) => item.targetRole === role),
    [data, role],
  );

  return (
    <div className="km">
      <div className="km__header">
        <div>
          <h1 className="km__title">Knowledge Map</h1>
          <p className="km__subtitle">
            Apa yang kita tahu, apa yang kurang, dan apa yang harus dilakukan
          </p>
        </div>
        {data !== null && <RoleSwitcher value={role} onChange={setRole} />}
      </div>

      {data === null ? (
        <section className="km-integrity-state" aria-live="polite">
          <span className="km-integrity-state__eyebrow">Source-backed only</span>
          <h2>Knowledge Map belum memiliki agregasi evidence aktif.</h2>
          <p>
            TDP tidak menampilkan angka, perubahan, atau action item contoh
            sebagai fakta repository. Jalankan Repository Scanner dan hubungkan
            source-backed aggregation sebelum data operasional ditampilkan di
            sini.
          </p>
          <div className="km-integrity-state__actions">
            <a className="km-integrity-state__link" href="/scanner">
              Buka Repository Scanner
            </a>
            <span>
              Untuk preview UI lokal saja, set{" "}
              <code>VITE_KNOWLEDGE_MAP_DEMO=true</code>.
            </span>
          </div>
        </section>
      ) : (
        <>
          <div className="km-demo-banner" role="status">
            Mode demo aktif. Seluruh angka dan item di halaman ini adalah
            fixture UI, bukan evidence repository.
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
        </>
      )}
    </div>
  );
}
