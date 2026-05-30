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
    backgroundColor: "#0369a1",
    color: "#fff",
    border: "none",
    borderRadius: 6,
    padding: "10px 20px",
    cursor: "pointer",
    fontSize: 14,
    fontWeight: 600,
    marginBottom: 16,
  },
  form: {
    border: "1px solid #e5e7eb",
    borderRadius: 8,
    padding: 20,
    marginBottom: 24,
    backgroundColor: "#f3f4f6",
    display: "flex",
    flexDirection: "column",
    gap: 12,
  },
  field: {
    display: "flex",
    flexDirection: "column",
    gap: 4,
    flex: 1,
  },
  row: {
    display: "flex",
    gap: 12,
  },
  label: {
    fontSize: 13,
    fontWeight: 600,
    color: "#111",
  },
  input: {
    padding: "8px 10px",
    border: "1px solid #e5e7eb",
    borderRadius: 4,
    fontSize: 14,
  },
  actions: {
    display: "flex",
    gap: 8,
    marginTop: 4,
  },
  submitBtn: {
    backgroundColor: "#0369a1",
    color: "#fff",
    border: "none",
    borderRadius: 4,
    padding: "8px 16px",
    cursor: "pointer",
    fontSize: 14,
    fontWeight: 600,
  },
  cancelBtn: {
    backgroundColor: "#fff",
    color: "#555",
    border: "1px solid #e5e7eb",
    borderRadius: 4,
    padding: "8px 16px",
    cursor: "pointer",
    fontSize: 14,
  },
};
