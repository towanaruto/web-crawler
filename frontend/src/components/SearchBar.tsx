"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

export default function SearchBar({
  defaultValue,
  sort,
  direction,
}: {
  defaultValue?: string;
  sort?: string;
  direction?: string;
}) {
  const [query, setQuery] = useState(defaultValue || "");
  const router = useRouter();

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const params = new URLSearchParams();
    if (query.trim()) params.set("q", query.trim());
    if (sort) params.set("sort", sort);
    if (direction) params.set("direction", direction);
    router.push(`/?${params.toString()}`);
  }

  function handleClear() {
    const params = new URLSearchParams();
    if (sort) params.set("sort", sort);
    if (direction) params.set("direction", direction);
    const qs = params.toString();
    setQuery("");
    router.push(qs ? `/?${qs}` : "/");
  }

  return (
    <form onSubmit={handleSubmit} style={styles.form}>
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search articles... (e.g. AI, ChatGPT)"
        style={styles.input}
      />
      <button type="submit" style={styles.button}>
        Search
      </button>
      {defaultValue && (
        <button
          type="button"
          onClick={handleClear}
          style={styles.clear}
        >
          Clear
        </button>
      )}
    </form>
  );
}

const styles: Record<string, React.CSSProperties> = {
  form: {
    display: "flex",
    gap: "var(--crawler-space-1)",
    marginBottom: "var(--crawler-space-2)",
  },
  input: {
    flex: 1,
    padding: "var(--crawler-space-1) var(--crawler-space-2)",
    fontSize: "var(--crawler-font-size-md)",
    border: "1px solid var(--crawler-border-subtle)",
    borderRadius: "var(--crawler-radius-pill)",
    outline: "none",
  },
  button: {
    padding: "var(--crawler-space-1) var(--crawler-space-3)",
    fontSize: "var(--crawler-font-size-md)",
    fontWeight: "var(--crawler-font-weight-emphasis)",
    backgroundColor: "var(--crawler-accent-primary)",
    color: "var(--crawler-text-on-accent)",
    border: "none",
    borderRadius: "var(--crawler-radius-pill)",
    cursor: "pointer",
  },
  clear: {
    padding: "var(--crawler-space-1) var(--crawler-space-2)",
    fontSize: "var(--crawler-font-size-md)",
    backgroundColor: "var(--crawler-surface-raised)",
    color: "var(--crawler-text-secondary)",
    border: "1px solid var(--crawler-border-subtle)",
    borderRadius: "var(--crawler-radius-pill)",
    cursor: "pointer",
  },
};
