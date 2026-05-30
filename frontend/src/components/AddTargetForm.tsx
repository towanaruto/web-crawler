"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { addTargetAction } from "@/app/targets/actions";

export default function AddTargetForm() {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);

  const [url, setUrl] = useState("");
  const [crawlMode, setCrawlMode] = useState("static");
  const [maxDepth, setMaxDepth] = useState(2);
  const [keywords, setKeywords] = useState("");
  const [keywordMode, setKeywordMode] = useState("any");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      await addTargetAction({
        base_url: url,
        crawl_mode: crawlMode,
        max_depth: maxDepth,
        keywords: keywords
          ? keywords.split(",").map((k) => k.trim()).filter(Boolean)
          : [],
        keyword_mode: keywordMode,
      });
      setUrl("");
      setCrawlMode("static");
      setMaxDepth(2);
      setKeywords("");
      setKeywordMode("any");
      setOpen(false);
      router.refresh();
    } catch {
      alert("Failed to add target");
    } finally {
      setLoading(false);
    }
  }

  if (!open) {
    return (
      <button onClick={() => setOpen(true)} style={styles.openBtn}>
        + Add Crawl Target
      </button>
    );
  }

  return (
    <form onSubmit={handleSubmit} style={styles.form}>
      <div style={styles.field}>
        <label style={styles.label}>URL *</label>
        <input
          type="url"
          required
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://example.com"
          style={styles.input}
        />
      </div>
      <div style={styles.row}>
        <div style={styles.field}>
          <label style={styles.label}>Crawl Mode</label>
          <select
            value={crawlMode}
            onChange={(e) => setCrawlMode(e.target.value)}
            style={styles.input}
          >
            <option value="static">static</option>
            <option value="dynamic">dynamic</option>
          </select>
        </div>
        <div style={styles.field}>
          <label style={styles.label}>Max Depth</label>
          <input
            type="number"
            min={0}
            max={10}
            value={maxDepth}
            onChange={(e) => setMaxDepth(Number(e.target.value))}
            style={styles.input}
          />
        </div>
      </div>
      <div style={styles.row}>
        <div style={styles.field}>
          <label style={styles.label}>Keywords (comma-separated)</label>
          <input
            type="text"
            value={keywords}
            onChange={(e) => setKeywords(e.target.value)}
            placeholder="keyword1, keyword2"
            style={styles.input}
          />
        </div>
        <div style={styles.field}>
          <label style={styles.label}>Keyword Mode</label>
          <select
            value={keywordMode}
            onChange={(e) => setKeywordMode(e.target.value)}
            style={styles.input}
          >
            <option value="any">any</option>
            <option value="all">all</option>
          </select>
        </div>
      </div>
      <div style={styles.actions}>
        <button type="submit" disabled={loading} style={styles.submitBtn}>
          {loading ? "Adding..." : "Add Target"}
        </button>
        <button
          type="button"
          onClick={() => setOpen(false)}
          style={styles.cancelBtn}
        >
          Cancel
        </button>
      </div>
    </form>
  );
}

const styles: Record<string, React.CSSProperties> = {
  openBtn: {
    backgroundColor: "var(--crawler-accent-primary)",
    color: "var(--crawler-text-on-accent)",
    border: "none",
    borderRadius: "var(--crawler-radius-pill)",
    padding: "var(--crawler-space-1) var(--crawler-space-3)",
    cursor: "pointer",
    fontSize: "var(--crawler-font-size-sm)",
    fontWeight: "var(--crawler-font-weight-emphasis)",
    marginBottom: "var(--crawler-space-2)",
  },
  form: {
    border: "1px solid var(--crawler-border-subtle)",
    borderRadius: "var(--crawler-radius-lg)",
    padding: "var(--crawler-space-3)",
    marginBottom: "var(--crawler-space-3)",
    backgroundColor: "var(--crawler-surface-raised)",
    display: "flex",
    flexDirection: "column",
    gap: "var(--crawler-space-2)",
  },
  field: {
    display: "flex",
    flexDirection: "column",
    gap: "var(--crawler-space-1)",
    flex: 1,
  },
  row: {
    display: "flex",
    gap: "var(--crawler-space-2)",
  },
  label: {
    fontSize: "var(--crawler-font-size-caption)",
    fontWeight: "var(--crawler-font-weight-emphasis)",
    color: "var(--crawler-text-primary)",
  },
  input: {
    padding: "var(--crawler-space-1) var(--crawler-space-2)",
    border: "1px solid var(--crawler-border-subtle)",
    borderRadius: "var(--crawler-radius-md)",
    fontSize: "var(--crawler-font-size-sm)",
  },
  actions: {
    display: "flex",
    gap: "var(--crawler-space-1)",
    marginTop: "var(--crawler-space-1)",
  },
  submitBtn: {
    backgroundColor: "var(--crawler-accent-primary)",
    color: "var(--crawler-text-on-accent)",
    border: "none",
    borderRadius: "var(--crawler-radius-pill)",
    padding: "var(--crawler-space-1) var(--crawler-space-2)",
    cursor: "pointer",
    fontSize: "var(--crawler-font-size-sm)",
    fontWeight: "var(--crawler-font-weight-emphasis)",
  },
  cancelBtn: {
    backgroundColor: "var(--crawler-surface-bg)",
    color: "var(--crawler-text-secondary)",
    border: "1px solid var(--crawler-border-subtle)",
    borderRadius: "var(--crawler-radius-pill)",
    padding: "var(--crawler-space-1) var(--crawler-space-2)",
    cursor: "pointer",
    fontSize: "var(--crawler-font-size-sm)",
  },
};
