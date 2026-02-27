import Link from "next/link";

export default function Header() {
  return (
    <header style={styles.header}>
      <div style={styles.inner}>
        <Link href="/" style={styles.logo}>
          Web Crawler CMS
        </Link>
        <nav>
          <Link href="/" style={styles.navLink}>
            Articles
          </Link>
        </nav>
      </div>
    </header>
  );
}

const styles: Record<string, React.CSSProperties> = {
  header: {
    borderBottom: "1px solid #e5e7eb",
    backgroundColor: "#fff",
  },
  inner: {
    maxWidth: 960,
    margin: "0 auto",
    padding: "16px 24px",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
  },
  logo: {
    fontSize: 20,
    fontWeight: 700,
    textDecoration: "none",
    color: "#111",
  },
  navLink: {
    textDecoration: "none",
    color: "#555",
  },
};
