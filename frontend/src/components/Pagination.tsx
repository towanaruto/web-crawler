import Link from "next/link";

export default function Pagination({
  currentPage,
  totalPages,
  query,
  sort,
  direction,
}: {
  currentPage: number;
  totalPages: number;
  query?: string;
  sort?: string;
  direction?: string;
}) {
  if (totalPages <= 1) return null;

  function buildHref(page: number) {
    const params = new URLSearchParams();
    if (page > 1) params.set("page", String(page));
    if (query) params.set("q", query);
    if (sort) params.set("sort", sort);
    if (direction) params.set("direction", direction);
    const qs = params.toString();
    return qs ? `/?${qs}` : "/";
  }

  return (
    <nav style={styles.nav}>
      {currentPage > 1 ? (
        <Link href={buildHref(currentPage - 1)} style={styles.link}>
          &laquo; Prev
        </Link>
      ) : (
        <span style={styles.disabled}>&laquo; Prev</span>
      )}

      <span style={styles.info}>
        Page {currentPage} / {totalPages}
      </span>

      {currentPage < totalPages ? (
        <Link href={buildHref(currentPage + 1)} style={styles.link}>
          Next &raquo;
        </Link>
      ) : (
        <span style={styles.disabled}>Next &raquo;</span>
      )}
    </nav>
  );
}

const styles: Record<string, React.CSSProperties> = {
  nav: {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    gap: "var(--crawler-space-3)",
    padding: "var(--crawler-space-4) 0",
  },
  link: {
    padding: "var(--crawler-space-1) var(--crawler-space-2)",
    backgroundColor: "var(--crawler-accent-primary)",
    color: "var(--crawler-text-on-accent)",
    textDecoration: "none",
    borderRadius: "var(--crawler-radius-pill)",
    fontSize: "var(--crawler-font-size-sm)",
    fontWeight: "var(--crawler-font-weight-emphasis)",
  },
  disabled: {
    padding: "var(--crawler-space-1) var(--crawler-space-2)",
    backgroundColor: "var(--crawler-surface-muted)",
    color: "var(--crawler-text-tertiary)",
    borderRadius: "var(--crawler-radius-pill)",
    fontSize: "var(--crawler-font-size-sm)",
  },
  info: {
    fontSize: "var(--crawler-font-size-sm)",
    color: "var(--crawler-text-tertiary)",
  },
};
