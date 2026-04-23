"use client";

import { useRouter } from "next/navigation";
import { CrawlTarget } from "@/lib/api";
import { deactivateTargetAction } from "@/app/targets/actions";

export default function CrawlTargetList({
  targets,
}: {
  targets: CrawlTarget[];
}) {
  const router = useRouter();

  async function handleDeactivate(id: string) {
    try {
      await deactivateTargetAction(id);
      router.refresh();
    } catch (e) {
      alert("Failed to deactivate target");
    }
  }

  if (targets.length === 0) {
    return (
      <p style={{ color: "#666", fontStyle: "italic" }}>
        No crawl targets configured yet.
      </p>
    );
  }

  return (
    <div style={styles.list}>
      {targets.map((t) => (
        <div key={t.id} style={styles.card}>
          <div style={styles.cardHeader}>
            <a
              href={t.base_url}
              target="_blank"
              rel="noopener noreferrer"
              style={styles.url}
            >
              {t.base_url}
            </a>
            <button
              onClick={() => handleDeactivate(t.id)}
              style={styles.deactivateBtn}
            >
              Deactivate
            </button>
          </div>
          <div style={styles.meta}>
            <span style={styles.badge}>{t.crawl_mode}</span>
            <span style={styles.detail}>Depth: {t.max_depth}</span>
            {t.keywords.length > 0 && (
              <span style={styles.detail}>
                Keywords ({t.keyword_mode}): {t.keywords.join(", ")}
              </span>
            )}
            {t.schedule && (
              <span style={styles.detail}>Schedule: {t.schedule}</span>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  list: {
    display: "flex",
    flexDirection: "column",
    gap: 12,
  },
  card: {
    border: "1px solid #e5e7eb",
    borderRadius: 8,
    padding: 16,
    backgroundColor: "#f3f4f6",
  },
  cardHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 8,
  },
  url: {
    fontWeight: 600,
    color: "#0369a1",
    textDecoration: "none",
    fontSize: 15,
  },
  deactivateBtn: {
    backgroundColor: "#dc2626",
    color: "#fff",
    border: "none",
    borderRadius: 4,
    padding: "6px 12px",
    cursor: "pointer",
    fontSize: 13,
  },
  meta: {
    display: "flex",
    flexWrap: "wrap",
    gap: 12,
    alignItems: "center",
    fontSize: 13,
    color: "#555",
  },
  badge: {
    backgroundColor: "#e8f4f8",
    color: "#0369a1",
    padding: "2px 8px",
    borderRadius: 4,
    fontSize: 12,
    fontWeight: 600,
  },
  detail: {
    color: "#666",
  },
};
