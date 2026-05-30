"use client";

import { useState } from "react";
import { crawlAction } from "@/app/targets/actions";

export default function CrawlButton() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string | null>(null);

  async function handleCrawl() {
    setLoading(true);
    setResult(null);
    try {
      const result = await crawlAction();
      setResult(formatResult(result.targetsQueued, result.jobIds));
    } catch {
      setResult("Failed to start crawl.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={styles.wrapper}>
      <button onClick={handleCrawl} disabled={loading} style={styles.btn}>
        {loading ? "Queuing..." : "Crawl Now"}
      </button>
      {result && <span style={styles.result}>{result}</span>}
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  wrapper: {
    display: "flex",
    alignItems: "center",
    gap: "var(--crawler-space-2)",
    marginBottom: "var(--crawler-space-2)",
  },
  btn: {
    backgroundColor: "var(--crawler-accent-primary)",
    color: "var(--crawler-text-on-accent)",
    border: "none",
    borderRadius: "var(--crawler-radius-pill)",
    padding: "var(--crawler-space-1) var(--crawler-space-3)",
    cursor: "pointer",
    fontSize: "var(--crawler-font-size-sm)",
    fontWeight: "var(--crawler-font-weight-emphasis)",
  },
  result: {
    fontSize: "var(--crawler-font-size-caption)",
    color: "var(--crawler-text-secondary)",
  },
};

function formatResult(targetsQueued: number, jobIds: string[]) {
  if (jobIds.length > 0) {
    return `Queued ${jobIds.length} crawl job${jobIds.length === 1 ? "" : "s"}.`;
  }
  return `Started crawl for ${targetsQueued} target${targetsQueued === 1 ? "" : "s"}.`;
}
