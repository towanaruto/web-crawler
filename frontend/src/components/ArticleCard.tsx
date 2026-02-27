import Link from "next/link";
import { Article } from "@/lib/api";

export default function ArticleCard({ article }: { article: Article }) {
  return (
    <article style={styles.card}>
      <Link href={`/articles/${article.slug}`} style={styles.title}>
        {article.title}
      </Link>
      <div style={styles.meta}>
        {article.author && <span>{article.author.name}</span>}
        {article.category && (
          <span style={styles.category}>{article.category.name}</span>
        )}
        {article.published_at && (
          <time>{new Date(article.published_at).toLocaleDateString()}</time>
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
  title: {
    fontSize: 20,
    fontWeight: 600,
    textDecoration: "none",
    color: "#111",
  },
  meta: {
    display: "flex",
    gap: 12,
    marginTop: 8,
    fontSize: 14,
    color: "#666",
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
