import Link from "next/link";

export default function Pagination({
  currentPage,
  totalPages,
  query,
}: {
  currentPage: number;
  totalPages: number;
  query?: string;
}) {
  if (totalPages <= 1) return null;

  function buildHref(page: number) {
    const params = new URLSearchParams();
    if (page > 1) params.set("page", String(page));
    if (query) params.set("q", query);
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
    gap: 24,
    padding: "32px 0",
  },
  link: {
    padding: "8px 16px",
    backgroundColor: "#111",
    color: "#fff",
    textDecoration: "none",
    borderRadius: 6,
    fontSize: 14,
  },
  disabled: {
    padding: "8px 16px",
    backgroundColor: "#e5e7eb",
    color: "#aaa",
    borderRadius: 6,
    fontSize: 14,
  },
  info: {
    fontSize: 14,
    color: "#666",
  },
};
