import type { ArticleListItem } from "@/db/queries";
import ArticleCard from "./ArticleCard";
import styles from "./ArticleList.module.css";

export default function ArticleList({ articles }: { articles: ArticleListItem[] }) {
  if (articles.length === 0) {
    return <p className={styles.empty}>No articles found.</p>;
  }
  return (
    <div className={styles.grid}>
      {articles.map((article) => (
        <ArticleCard key={article.id} article={article} />
      ))}
    </div>
  );
}
