"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import type { CrawlTargetItem } from "@/db/queries";
import { crawlAction, deactivateTargetAction } from "@/app/targets/actions";

export default function CrawlTargetList({
  targets,
}: {
  targets: CrawlTargetItem[];
}) {
  const router = useRouter();
  const [crawling, setCrawling] = useState<string | null>(null);
  const [queuedJobByTarget, setQueuedJobByTarget] = useState<Record<string, string>>({});

  async function handleDeactivate(id: string) {
    try {
      await deactivateTargetAction(id);
      router.refresh();
    } catch {
      alert("Failed to deactivate target");
    }
  }

  async function handleCrawlOne(id: string) {
    setCrawling(id);
    try {
      const result = await crawlAction(id);
      const jobId = result.jobIds[0];
      if (jobId) {
        setQueuedJobByTarget((current) => ({ ...current, [id]: jobId }));
      }
    } catch {
      alert("Failed to start crawl");
    } finally {
      setCrawling(null);
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
              href={t.baseUrl}
              target="_blank"
              rel="noopener noreferrer"
              style={styles.url}
            >
              {t.baseUrl}
            </a>
            <div style={styles.actions}>
              <button
                onClick={() => handleCrawlOne(t.id)}
                disabled={crawling === t.id}
                style={styles.crawlBtn}
              >
                {crawling === t.id ? "Queuing..." : "Crawl this"}
              </button>
              <button
                onClick={() => handleDeactivate(t.id)}
                style={styles.deactivateBtn}
              >
                Deactivate
              </button>
            </div>
          </div>
          <div style={styles.meta}>
            <span style={styles.badge}>{t.crawlMode}</span>
            <span style={styles.detail}>Depth: {t.maxDepth}</span>
            {queuedJobByTarget[t.id] && (
              <span style={styles.detail}>
                Job: {queuedJobByTarget[t.id].slice(0, 8)}
              </span>
            )}
            {t.keywords.length > 0 && (
              <span style={styles.detail}>
                Keywords ({t.keywordMode}): {t.keywords.join(", ")}
              </span>
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
  actions: {
    display: "flex",
    gap: 8,
  },
  crawlBtn: {
    backgroundColor: "#0369a1",
    color: "#fff",
    border: "none",
    borderRadius: 4,
    padding: "6px 12px",
    cursor: "pointer",
    fontSize: 13,
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
