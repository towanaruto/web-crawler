"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

export default function SearchBar({ defaultValue }: { defaultValue?: string }) {
  const [query, setQuery] = useState(defaultValue || "");
  const router = useRouter();

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const params = new URLSearchParams();
    if (query.trim()) params.set("q", query.trim());
    router.push(`/?${params.toString()}`);
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
          onClick={() => {
            setQuery("");
            router.push("/");
          }}
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
    gap: 8,
    marginBottom: 16,
  },
  input: {
    flex: 1,
    padding: "10px 14px",
    fontSize: 16,
    border: "1px solid #d1d5db",
    borderRadius: 6,
    outline: "none",
  },
  button: {
    padding: "10px 20px",
    fontSize: 16,
    backgroundColor: "#111",
    color: "#fff",
    border: "none",
    borderRadius: 6,
    cursor: "pointer",
  },
  clear: {
    padding: "10px 16px",
    fontSize: 16,
    backgroundColor: "#f3f4f6",
    color: "#666",
    border: "1px solid #d1d5db",
    borderRadius: 6,
    cursor: "pointer",
  },
};
