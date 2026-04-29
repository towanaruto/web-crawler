import type { ArticleListItem } from "@/db/queries";
import ArticleCard from "./ArticleCard";

export default function ArticleList({ articles }: { articles: ArticleListItem[] }) {
  if (articles.length === 0) {
    return <p style={{ color: "#888", padding: "40px 0" }}>No articles found.</p>;
  }
  return (
    <div>
      {articles.map((article) => (
        <ArticleCard key={article.id} article={article} />
      ))}
    </div>
  );
}
