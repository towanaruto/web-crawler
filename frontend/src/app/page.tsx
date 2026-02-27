import { fetchArticles } from "@/lib/api";
import ArticleList from "@/components/ArticleList";
import Pagination from "@/components/Pagination";
import SearchBar from "@/components/SearchBar";

export default async function HomePage({
  searchParams,
}: {
  searchParams: Promise<{ page?: string; q?: string }>;
}) {
  const { page, q } = await searchParams;
  const currentPage = Math.max(1, Number(page) || 1);
  const limit = 20;
  const offset = (currentPage - 1) * limit;

  let articles;
  let total = 0;
  try {
    const data = await fetchArticles(offset, limit, undefined, q);
    articles = data.items;
    total = data.total;
  } catch {
    articles = [];
  }

  const totalPages = Math.ceil(total / limit);

  return (
    <div>
      <h1 style={{ fontSize: 28, fontWeight: 700, marginBottom: 16 }}>
        Articles
      </h1>
      <SearchBar defaultValue={q} />
      <p style={{ color: "#888", fontSize: 14, marginBottom: 24 }}>
        {total} articles found
        {q ? ` for "${q}"` : ""}
      </p>
      <ArticleList articles={articles} />
      <Pagination currentPage={currentPage} totalPages={totalPages} query={q} />
    </div>
  );
}
