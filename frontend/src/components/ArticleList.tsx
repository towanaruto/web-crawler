"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { deleteArticlesAction } from "@/app/actions";
import type { ArticleListItem } from "@/db/queries";
import ArticleCard from "./ArticleCard";
import styles from "./ArticleList.module.css";

export default function ArticleList({ articles }: { articles: ArticleListItem[] }) {
  const router = useRouter();
  const [selectionMode, setSelectionMode] = useState(false);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [deleting, setDeleting] = useState(false);
  const articleIds = useMemo(() => articles.map((article) => article.id), [articles]);

  useEffect(() => {
    setSelectedIds((current) =>
      current.filter((id) => articleIds.includes(id)),
    );
  }, [articleIds]);

  if (articles.length === 0) {
    return <p className={styles.empty}>No articles found.</p>;
  }

  const selectedCount = selectedIds.length;
  const allSelected = selectedCount === articleIds.length;

  function toggleSelectionMode() {
    setSelectionMode((current) => {
      if (current) setSelectedIds([]);
      return !current;
    });
  }

  function toggleArticleSelection(id: string) {
    setSelectedIds((current) =>
      current.includes(id)
        ? current.filter((selectedId) => selectedId !== id)
        : [...current, id],
    );
  }

  function selectAllVisible() {
    setSelectedIds(articleIds);
  }

  function clearSelection() {
    setSelectedIds([]);
  }

  async function handleBulkDelete() {
    if (selectedCount === 0) return;
    if (!confirm(`${selectedCount}件の記事を削除しますか？`)) return;

    setDeleting(true);
    try {
      await deleteArticlesAction(selectedIds);
      setSelectedIds([]);
      setSelectionMode(false);
      router.refresh();
    } catch {
      alert("一括削除に失敗しました");
    } finally {
      setDeleting(false);
    }
  }

  return (
    <>
      <div className={styles.toolbar}>
        <button
          type="button"
          className={styles.secondaryButton}
          onClick={toggleSelectionMode}
        >
          {selectionMode ? "Cancel selection" : "Select articles"}
        </button>
        {selectionMode && (
          <div className={styles.selectionActions}>
            <span className={styles.selectionCount}>
              {selectedCount} selected
            </span>
            <button
              type="button"
              className={styles.secondaryButton}
              onClick={allSelected ? clearSelection : selectAllVisible}
            >
              {allSelected ? "Clear all" : "Select all visible"}
            </button>
            <button
              type="button"
              className={styles.dangerButton}
              onClick={handleBulkDelete}
              disabled={selectedCount === 0 || deleting}
            >
              {deleting ? "Deleting..." : "Delete selected"}
            </button>
          </div>
        )}
      </div>
      <div className={styles.grid}>
        {articles.map((article) => (
          <ArticleCard
            key={article.id}
            article={article}
            selectionMode={selectionMode}
            selected={selectedIds.includes(article.id)}
            onSelectionChange={toggleArticleSelection}
          />
        ))}
      </div>
    </>
  );
}
