"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import type { ArticleListItem } from "@/db/queries";
import { deleteArticleAction } from "@/app/actions";
import styles from "./ArticleCard.module.css";

export default function ArticleCard({ article }: { article: ArticleListItem }) {
  const router = useRouter();
  const [deleting, setDeleting] = useState(false);
  const visibleTags = article.tags.slice(0, 3);
  const hiddenTagCount = article.tags.length - visibleTags.length;

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
    <article className={styles.card}>
      <div className={styles.media}>
        {article.featuredImageUrl ? (
          <img
            src={article.featuredImageUrl}
            alt=""
            className={styles.image}
            loading="lazy"
          />
        ) : (
          <div className={styles.imageFallback}>No image</div>
        )}
      </div>
      <div className={styles.body}>
        <div className={styles.header}>
          <Link href={`/articles/${article.slug}`} className={styles.title}>
            {article.title}
          </Link>
          <button
            onClick={handleDelete}
            disabled={deleting}
            className={styles.deleteBtn}
          >
            {deleting ? "..." : "Delete"}
          </button>
        </div>
        <div className={styles.meta}>
          {article.crawledAt && (
            <time className={styles.metaItem}>
              Crawled: {new Date(article.crawledAt).toLocaleString()}
            </time>
          )}
          {article.author && (
            <span className={styles.metaItem}>{article.author.name}</span>
          )}
          {article.category && (
            <span className={styles.category}>{article.category.name}</span>
          )}
          {article.publishedAt && (
            <time className={styles.metaItem}>
              Published: {new Date(article.publishedAt).toLocaleDateString()}
            </time>
          )}
        </div>
        {article.excerpt && <p className={styles.excerpt}>{article.excerpt}</p>}
        {visibleTags.length > 0 && (
          <div className={styles.tags}>
            {visibleTags.map((tag) => (
              <span key={tag.id} className={styles.tag}>
                {tag.name}
              </span>
            ))}
            {hiddenTagCount > 0 && (
              <span className={styles.tag}>+{hiddenTagCount}</span>
            )}
          </div>
        )}
      </div>
    </article>
  );
}
