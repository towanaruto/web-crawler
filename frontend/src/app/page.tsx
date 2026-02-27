import { fetchArticles } from "@/lib/api";
import ArticleList from "@/components/ArticleList";

export default async function HomePage() {
  let articles;
  try {
    const data = await fetchArticles();
    articles = data.items;
  } catch {
    articles = [];
  }

  return (
    <div>
      <h1 style={{ fontSize: 28, fontWeight: 700, marginBottom: 24 }}>
        Articles
      </h1>
      <ArticleList articles={articles} />
    </div>
  );
}
