"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import type { ArticleListItem } from "@/db/queries";
import { deleteArticleAction } from "@/app/actions";

export default function ArticleCard({ article }: { article: ArticleListItem }) {
  const router = useRouter();
  const [deleting, setDeleting] = useState(false);

  async function handleDelete() {
    if (!confirm(`"${article.title}" を削除しますか？`)) return;
    setDeleting(true);
    try {
      await deleteArticleAction(article.id);
      router.refresh();
    } catch {
      alert("削除に失敗しました");
    } finally {
      setDeleting(false);
    }
  }

  return (
    <article style={styles.card}>
      <div style={styles.header}>
        <Link href={`/articles/${article.slug}`} style={styles.title}>
          {article.title}
        </Link>
        <button
          onClick={handleDelete}
          disabled={deleting}
          style={styles.deleteBtn}
        >
          {deleting ? "..." : "Delete"}
        </button>
      </div>
      <div style={styles.meta}>
        {article.crawledAt && (
          <time style={styles.crawledAt}>
            Crawled: {new Date(article.crawledAt).toLocaleString()}
          </time>
        )}
        {article.author && <span>{article.author.name}</span>}
        {article.category && (
          <span style={styles.category}>{article.category.name}</span>
        )}
        {article.publishedAt && (
          <time>
            Published: {new Date(article.publishedAt).toLocaleDateString()}
          </time>
        )}
      </div>
      {article.excerpt && <p style={styles.excerpt}>{article.excerpt}</p>}
      {article.tags.length > 0 && (
        <div style={styles.tags}>
          {article.tags.map((tag) => (
            <span key={tag.id} style={styles.tag}>
              {tag.name}
            </span>
          ))}
        </div>
      )}
    </article>
  );
}

const styles: Record<string, React.CSSProperties> = {
  card: {
    padding: "24px 0",
    borderBottom: "1px solid #e5e7eb",
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "flex-start",
    gap: 12,
  },
  title: {
    fontSize: 20,
    fontWeight: 600,
    textDecoration: "none",
    color: "#111",
  },
  deleteBtn: {
    backgroundColor: "transparent",
    color: "#999",
    border: "1px solid #e5e7eb",
    borderRadius: 4,
    padding: "4px 10px",
    cursor: "pointer",
    fontSize: 12,
    flexShrink: 0,
  },
  meta: {
    display: "flex",
    gap: 12,
    marginTop: 8,
    fontSize: 14,
    color: "#666",
    flexWrap: "wrap" as const,
  },
  crawledAt: {
    color: "#0369a1",
    fontWeight: 500,
  },
  category: {
    backgroundColor: "#f0f0f0",
    padding: "2px 8px",
    borderRadius: 4,
  },
  excerpt: {
    marginTop: 8,
    color: "#444",
    lineHeight: 1.6,
  },
  tags: {
    display: "flex",
    gap: 6,
    marginTop: 8,
  },
  tag: {
    fontSize: 12,
    backgroundColor: "#e8f4f8",
    padding: "2px 8px",
    borderRadius: 12,
    color: "#0369a1",
  },
};
