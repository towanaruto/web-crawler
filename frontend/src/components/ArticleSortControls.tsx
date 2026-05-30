import Link from "next/link";
import type { ArticleSort } from "@/db/queries";
import styles from "./ArticleSortControls.module.css";

const options: { label: string; sort: ArticleSort["sort"]; direction: ArticleSort["direction"] }[] = [
  { label: "Crawled newest", sort: "crawledAt", direction: "desc" },
  { label: "Crawled oldest", sort: "crawledAt", direction: "asc" },
  { label: "Title A-Z", sort: "title", direction: "asc" },
  { label: "Title Z-A", sort: "title", direction: "desc" },
  { label: "Published newest", sort: "publishedAt", direction: "desc" },
  { label: "Published oldest", sort: "publishedAt", direction: "asc" },
];

export default function ArticleSortControls({
  currentSort,
  query,
}: {
  currentSort: ArticleSort;
  query?: string;
}) {
  return (
    <div className={styles.toolbar} aria-label="Article sorting">
      <span className={styles.label}>Sort by</span>
      <div className={styles.options}>
        {options.map((option) => {
          const active =
            option.sort === currentSort.sort &&
            option.direction === currentSort.direction;
          return (
            <Link
              key={`${option.sort}-${option.direction}`}
              href={buildHref(option, query)}
              className={`${styles.option} ${active ? styles.optionActive : ""}`}
              aria-current={active ? "true" : undefined}
            >
              {option.label}
            </Link>
          );
        })}
      </div>
    </div>
  );
}

function buildHref(sort: ArticleSort, query?: string) {
  const params = new URLSearchParams();
  if (query) params.set("q", query);
  params.set("sort", sort.sort);
  params.set("direction", sort.direction);
  return `/?${params.toString()}`;
}
