import { notFound } from "next/navigation";

import { getArticleBySlug } from "@/db/queries";
import { requireCurrentUser } from "@/lib/current-user";

export default async function ArticlePage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const user = await requireCurrentUser();
  const article = await getArticleBySlug(slug, user.id);
  if (!article) notFound();

  return (
    <article>
      <h1 style={{ fontSize: 32, fontWeight: 700, marginBottom: 8 }}>
        {article.title}
      </h1>
      <div style={styles.meta}>
        {article.author && <span>By {article.author.name}</span>}
        {article.publishedAt && (
          <time>{new Date(article.publishedAt).toLocaleDateString()}</time>
        )}
        {article.category && <span>{article.category.name}</span>}
      </div>
      {article.tags.length > 0 && (
        <div style={styles.tags}>
          {article.tags.map((tag) => (
            <span key={tag.id} style={styles.tag}>
              {tag.name}
            </span>
          ))}
        </div>
      )}
      {article.bodyHtml ? (
        <div
          style={styles.body}
          dangerouslySetInnerHTML={{ __html: article.bodyHtml }}
        />
      ) : (
        <div style={styles.body}>
          <p>{article.bodyText}</p>
        </div>
      )}
      <footer style={styles.footer}>
        <a href={article.sourceUrl} target="_blank" rel="noopener noreferrer">
          Original source
        </a>
        {article.crawledAt && (
          <span>
            Crawled: {new Date(article.crawledAt).toLocaleDateString()}
          </span>
        )}
      </footer>
    </article>
  );
}

const styles: Record<string, React.CSSProperties> = {
  meta: {
    display: "flex",
    gap: 16,
    color: "#666",
    fontSize: 14,
    marginBottom: 16,
  },
  tags: {
    display: "flex",
    gap: 6,
    marginBottom: 24,
  },
  tag: {
    fontSize: 12,
    backgroundColor: "#e8f4f8",
    padding: "2px 8px",
    borderRadius: 12,
    color: "#0369a1",
  },
  body: {
    lineHeight: 1.8,
    marginTop: 24,
  },
  footer: {
    marginTop: 48,
    paddingTop: 16,
    borderTop: "1px solid #e5e7eb",
    display: "flex",
    justifyContent: "space-between",
    fontSize: 14,
    color: "#888",
  },
};
