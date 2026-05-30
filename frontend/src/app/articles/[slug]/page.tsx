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
      <h1
        style={{
          fontSize: "var(--crawler-font-size-article)",
          fontWeight: "var(--crawler-font-weight-emphasis)",
          marginBottom: "var(--crawler-space-1)",
        }}
      >
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
    gap: "var(--crawler-space-2)",
    color: "var(--crawler-text-tertiary)",
    fontSize: "var(--crawler-font-size-sm)",
    marginBottom: "var(--crawler-space-2)",
  },
  tags: {
    display: "flex",
    gap: "var(--crawler-space-1)",
    marginBottom: "var(--crawler-space-3)",
  },
  tag: {
    fontSize: "var(--crawler-font-size-micro)",
    backgroundColor: "var(--crawler-surface-raised)",
    padding: "0 var(--crawler-space-1)",
    borderRadius: "var(--crawler-radius-pill)",
    color: "var(--crawler-accent-primary)",
  },
  body: {
    lineHeight: 1.8,
    marginTop: "var(--crawler-space-3)",
  },
  footer: {
    marginTop: "var(--crawler-space-6)",
    paddingTop: "var(--crawler-space-2)",
    borderTop: "1px solid var(--crawler-border-subtle)",
    display: "flex",
    justifyContent: "space-between",
    fontSize: "var(--crawler-font-size-sm)",
    color: "var(--crawler-text-tertiary)",
  },
};
