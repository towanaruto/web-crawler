import ArticleList from "@/components/ArticleList";
import ArticleSortControls from "@/components/ArticleSortControls";
import Pagination from "@/components/Pagination";
import SearchBar from "@/components/SearchBar";
import {
  listArticles,
  normalizeArticleSort,
  type ArticleListItem,
} from "@/db/queries";
import { requireCurrentUser } from "@/lib/current-user";
import styles from "./HomePage.module.css";

export default async function HomePage({
  searchParams,
}: {
  searchParams: Promise<{
    page?: string;
    q?: string;
    sort?: string;
    direction?: string;
  }>;
}) {
  const { page, q, sort, direction } = await searchParams;
  const currentPage = Math.max(1, Number(page) || 1);
  const articleSort = normalizeArticleSort(sort, direction);
  const user = await requireCurrentUser();
  const limit = 20;
  const offset = (currentPage - 1) * limit;

  let items: ArticleListItem[] = [];
  let total = 0;
  try {
    const data = await listArticles({
      userId: user.id,
      search: q,
      offset,
      limit,
      sort: articleSort.sort,
      direction: articleSort.direction,
    });
    items = data.items;
    total = data.total;
  } catch {
    // swallow — empty state is rendered below.
  }

  const totalPages = Math.ceil(total / limit);

  return (
    <div>
      <h1 className={styles.heading}>Articles</h1>
      <SearchBar
        defaultValue={q}
        sort={articleSort.sort}
        direction={articleSort.direction}
      />
      <p className={styles.summary}>
        {total} articles found
        {q ? ` for "${q}"` : ""}
      </p>
      <ArticleSortControls currentSort={articleSort} query={q} />
      <ArticleList articles={items} />
      <Pagination
        currentPage={currentPage}
        totalPages={totalPages}
        query={q}
        sort={articleSort.sort}
        direction={articleSort.direction}
      />
    </div>
  );
}
