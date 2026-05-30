"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import type { CrawlTargetItem } from "@/db/queries";
import { crawlAction, deactivateTargetAction } from "@/app/targets/actions";
import TargetScheduleForm from "@/components/TargetScheduleForm";

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
      <p style={{ color: "var(--crawler-text-tertiary)", fontStyle: "italic" }}>
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
          <TargetScheduleForm target={t} />
        </div>
      ))}
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  list: {
    display: "flex",
    flexDirection: "column",
    gap: "var(--crawler-space-2)",
  },
  card: {
    border: "1px solid var(--crawler-border-subtle)",
    borderRadius: "var(--crawler-radius-lg)",
    padding: "var(--crawler-space-2)",
    backgroundColor: "var(--crawler-surface-raised)",
  },
  cardHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: "var(--crawler-space-1)",
  },
  url: {
    fontWeight: "var(--crawler-font-weight-emphasis)",
    color: "var(--crawler-accent-primary)",
    textDecoration: "none",
    fontSize: "var(--crawler-font-size-md)",
  },
  actions: {
    display: "flex",
    gap: "var(--crawler-space-1)",
  },
  crawlBtn: {
    backgroundColor: "var(--crawler-accent-primary)",
    color: "var(--crawler-text-on-accent)",
    border: "none",
    borderRadius: "var(--crawler-radius-pill)",
    padding: "var(--crawler-space-1) var(--crawler-space-2)",
    cursor: "pointer",
    fontSize: "var(--crawler-font-size-caption)",
  },
  deactivateBtn: {
    backgroundColor: "var(--crawler-danger-primary)",
    color: "var(--crawler-text-on-accent)",
    border: "none",
    borderRadius: "var(--crawler-radius-pill)",
    padding: "var(--crawler-space-1) var(--crawler-space-2)",
    cursor: "pointer",
    fontSize: "var(--crawler-font-size-caption)",
  },
  meta: {
    display: "flex",
    flexWrap: "wrap",
    gap: "var(--crawler-space-2)",
    alignItems: "center",
    fontSize: "var(--crawler-font-size-caption)",
    color: "var(--crawler-text-secondary)",
  },
  badge: {
    backgroundColor: "var(--crawler-surface-bg)",
    color: "var(--crawler-accent-primary)",
    padding: "0 var(--crawler-space-1)",
    borderRadius: "var(--crawler-radius-pill)",
    fontSize: "var(--crawler-font-size-micro)",
    fontWeight: "var(--crawler-font-weight-emphasis)",
  },
  detail: {
    color: "var(--crawler-text-tertiary)",
  },
};
