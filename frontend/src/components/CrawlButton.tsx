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
      const res = await crawlAction();
      setResult(
        `Crawled ${res.targets_crawled} targets, ${res.pages_crawled} pages fetched, found ${res.articles_found} articles, ${res.failed} failed`
      );
    } catch {
      setResult("Crawl failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={styles.wrapper}>
      <button onClick={handleCrawl} disabled={loading} style={styles.btn}>
        {loading ? "Crawling..." : "Crawl Now"}
      </button>
      {result && <span style={styles.result}>{result}</span>}
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  wrapper: {
    display: "flex",
    alignItems: "center",
    gap: 12,
    marginBottom: 16,
  },
  btn: {
    backgroundColor: "#0369a1",
    color: "#fff",
    border: "none",
    borderRadius: 6,
    padding: "10px 20px",
    cursor: "pointer",
    fontSize: 14,
    fontWeight: 600,
  },
  result: {
    fontSize: 13,
    color: "#555",
  },
};
